"""SQLite data access for SUT — البائع السوري."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from typing import Any

DEFAULT_DB_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "sut")
DB_PATH = os.environ.get("SUT_DB_PATH") or os.path.join(DEFAULT_DB_DIR, "sut.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total REAL NOT NULL CHECK (total >= 0),
    paid REAL NOT NULL CHECK (paid >= 0),
    change REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
);
"""


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _migrate_sales_foreign_key(connection: sqlite3.Connection) -> None:
    """Allow deleting a product while keeping its sales history."""
    rows = connection.execute("PRAGMA foreign_key_list(sales)").fetchall()
    needs_migration = any(
        row["table"] == "products" and (row["on_delete"] or "").upper() != "SET NULL"
        for row in rows
    )
    if not needs_migration:
        return
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.executescript(
            """
            BEGIN;
            ALTER TABLE sales RENAME TO sales_old;
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                total REAL NOT NULL CHECK (total >= 0),
                paid REAL NOT NULL CHECK (paid >= 0),
                change REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
            );
            INSERT INTO sales (id, product_id, product_name, quantity, unit_price,
                               total, paid, change, created_at)
            SELECT id, product_id, product_name, quantity, unit_price,
                   total, paid, change, created_at FROM sales_old;
            DROP TABLE sales_old;
            COMMIT;
            """
        )
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def init_db(db_path: str | None = None) -> None:
    with connect(db_path) as connection:
        connection.executescript(_SCHEMA)
        _migrate_sales_foreign_key(connection)
        connection.commit()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_products(db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, name, price, quantity, created_at, updated_at "
            "FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [dict(row) for row in rows]


def get_product(product_id: int, db_path: str | None = None) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT id, name, price, quantity FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
    return dict(row) if row else None


def add_product(name: str, price: float, quantity: int, db_path: str | None = None) -> int:
    name = name.strip()
    if not name:
        raise ValueError("اسم المنتج مطلوب")
    if price < 0:
        raise ValueError("السعر لا يمكن أن يكون سالباً")
    if quantity < 0:
        raise ValueError("الكمية لا يمكن أن تكون سالبة")
    now = _now()
    try:
        with connect(db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO products (name, price, quantity, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, price, quantity, now, now),
            )
            connection.commit()
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise ValueError("اسم المنتج مستخدم بالفعل") from exc


def update_product(
    product_id: int, name: str, price: float, quantity: int, db_path: str | None = None
) -> None:
    name = name.strip()
    if not name:
        raise ValueError("اسم المنتج مطلوب")
    if price < 0:
        raise ValueError("السعر لا يمكن أن يكون سالباً")
    if quantity < 0:
        raise ValueError("الكمية لا يمكن أن تكون سالبة")
    try:
        with connect(db_path) as connection:
            cursor = connection.execute(
                "UPDATE products SET name = ?, price = ?, quantity = ?, updated_at = ? "
                "WHERE id = ?",
                (name, price, quantity, _now(), product_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                raise ValueError("المنتج غير موجود")
    except sqlite3.IntegrityError as exc:
        raise ValueError("اسم المنتج مستخدم بالفعل") from exc


def delete_product(product_id: int, db_path: str | None = None) -> None:
    with connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise ValueError("المنتج غير موجود")


def create_sale(
    product_id: int, quantity: int, paid: float, db_path: str | None = None
) -> dict[str, Any]:
    if quantity <= 0:
        raise ValueError("الكمية يجب أن تكون أكبر من صفر")
    if paid < 0:
        raise ValueError("المبلغ المدفوع لا يمكن أن يكون سالباً")

    with connect(db_path) as connection:
        product = connection.execute(
            "SELECT id, name, price, quantity FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise ValueError("المنتج غير موجود")
        if int(product["quantity"]) < quantity:
            raise ValueError("المخزون غير كافٍ")
        unit_price = float(product["price"])
        total = round(unit_price * quantity, 2)
        if paid < total:
            raise ValueError("المبلغ المدفوع غير كافٍ")
        change = round(paid - total, 2)
        cursor = connection.execute(
            "INSERT INTO sales "
            "(product_id, product_name, quantity, unit_price, total, paid, change, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                int(product["id"]),
                str(product["name"]),
                quantity,
                unit_price,
                total,
                paid,
                change,
                _now(),
            ),
        )
        connection.execute(
            "UPDATE products SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
            (quantity, _now(), product_id),
        )
        connection.commit()
        sale_id = int(cursor.lastrowid)

    return {
        "id": sale_id,
        "product_id": product_id,
        "product_name": str(product["name"]),
        "quantity": quantity,
        "unit_price": unit_price,
        "total": total,
        "paid": paid,
        "change": change,
    }


def list_sales(limit: int = 500, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, product_id, product_name, quantity, unit_price, total, paid, "
            "change, created_at FROM sales ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def today_total(db_path: str | None = None) -> float:
    today = date.today().isoformat()
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(SUM(total), 0) AS total FROM sales "
            "WHERE substr(created_at, 1, 10) = ?",
            (today,),
        ).fetchone()
    return float(row["total"]) if row else 0.0
