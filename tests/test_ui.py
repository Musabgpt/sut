"""UI-level tests for SUT. Run with xvfb-run on headless machines."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

try:
    from sut import app as app_module
    from sut import db

    SutApp = app_module.SutApp
    TK_ERROR = None
except Exception as exc:  # tkinter or its shared libraries are missing
    TK_ERROR = exc
    app_module = None  # type: ignore[assignment]
    db = None  # type: ignore[assignment]
    SutApp = None  # type: ignore[assignment]


HAS_TK = TK_ERROR is None and bool(os.environ.get("DISPLAY"))


def _noop(*_args, **_kwargs):
    return None


@unittest.skipUnless(HAS_TK, "Tkinter and a display are required for UI tests")
class UiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "ui.db")
        self.old_db_path = db.DB_PATH
        db.DB_PATH = self.db_path
        db.init_db(self.db_path)
        self.patchers = [
            mock.patch.object(app_module.messagebox, "showinfo", _noop),
            mock.patch.object(app_module.messagebox, "showwarning", _noop),
            mock.patch.object(app_module.messagebox, "showerror", _noop),
            mock.patch.object(app_module.messagebox, "askyesno", lambda *a, **k: True),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.app = SutApp()
        self.app.withdraw()
        self.app.update_idletasks()

    def tearDown(self) -> None:
        try:
            self.app.destroy()
        except Exception:
            pass
        for patcher in self.patchers:
            patcher.stop()
        db.DB_PATH = self.old_db_path
        self.tmp.cleanup()

    def _fill_product(self, name: str, price: str, quantity: str) -> None:
        self.app.product_id_var.set("")
        self.app.product_name_var.set(name)
        self.app.product_price_var.set(price)
        self.app.product_qty_var.set(quantity)

    def test_add_update_delete_product(self) -> None:
        self._fill_product("تفاح", "5000", "10")
        self.app._add_product()
        self.app.update_idletasks()
        products = db.list_products(self.db_path)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["name"], "تفاح")
        self.assertEqual(len(self.app.products_tree.get_children()), 1)

        product_id = products[0]["id"]
        self.app.product_id_var.set(str(product_id))
        self.app.product_name_var.set("تفاح أحمر")
        self.app.product_price_var.set("6500")
        self.app.product_qty_var.set("12")
        self.app._update_product()
        updated = db.list_products(self.db_path)[0]
        self.assertEqual(
            (updated["name"], updated["price"], updated["quantity"]),
            ("تفاح أحمر", 6500.0, 12),
        )

        self.app.product_id_var.set(str(product_id))
        self.app._delete_product()
        self.assertEqual(db.list_products(self.db_path), [])
        self.assertEqual(len(self.app.products_tree.get_children()), 0)

    def test_sale_updates_stock_total_and_change(self) -> None:
        self._fill_product("رز", "10000", "5")
        self.app._add_product()
        self.app.update_idletasks()

        self.app.sale_product_var.set(next(iter(self.app.product_map)))
        self.app.sale_qty_var.set("2")
        self.app.sale_paid_var.set("25000")
        self.app.update_idletasks()
        self.assertIn("20,000.00", self.app.sale_total_var.get())
        self.assertEqual(self.app.sale_change_var.get(), "5,000.00 ل.س")

        self.app._complete_sale()
        self.app.update_idletasks()
        product = db.list_products(self.db_path)[0]
        self.assertEqual(product["quantity"], 3)
        self.assertEqual(db.today_total(self.db_path), 20000.0)
        self.assertIn("20,000.00", self.app.today_total_var.get())
        self.assertEqual(len(self.app.history_tree.get_children()), 1)

    def test_invalid_sale_is_rejected(self) -> None:
        self._fill_product("سكر", "4000", "2")
        self.app._add_product()
        self.app.update_idletasks()
        self.app.sale_product_var.set(next(iter(self.app.product_map)))
        self.app.sale_qty_var.set("5")
        self.app.sale_paid_var.set("20000")
        self.app.update_idletasks()
        self.assertIn("المخزون", self.app.sale_total_var.get())
        self.app._complete_sale()
        self.assertEqual(len(db.list_sales(10, self.db_path)), 0)
        self.assertEqual(db.list_products(self.db_path)[0]["quantity"], 2)

    def test_data_survives_restart(self) -> None:
        self._fill_product("زيت", "12000", "4")
        self.app._add_product()
        self.app.update_idletasks()
        self.app.destroy()

        self.app = SutApp()
        self.app.withdraw()
        self.app.update_idletasks()
        rows = self.app.products_tree.get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.app.products_tree.item(rows[0], "values")[1], "زيت")


if __name__ == "__main__":
    unittest.main()
