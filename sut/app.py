"""Tkinter user interface for SUT — البائع السوري."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

try:
    from .db import (
        DB_PATH,
        add_product,
        create_sale,
        delete_product,
        init_db,
        list_products,
        list_sales,
        today_total,
        update_product,
    )
except ImportError:  # Running as a plain script during development.
    from db import (  # type: ignore
        DB_PATH,
        add_product,
        create_sale,
        delete_product,
        init_db,
        list_products,
        list_sales,
        today_total,
        update_product,
    )


def money(value: float) -> str:
    return f"{value:,.2f} ل.س"


class SutApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__(className="SUT")
        self.title("SUT — البائع السوري")
        self.geometry("1120x720")
        self.minsize(960, 640)
        self.configure(bg="#eef2f5")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=(12, 8), font=("DejaVu Sans", 12, "bold"))
        style.configure("TLabel", font=("DejaVu Sans", 11))
        style.configure("TLabelframe.Label", font=("DejaVu Sans", 12, "bold"))
        style.configure("Treeview", rowheight=28, font=("DejaVu Sans", 11))
        style.configure("Treeview.Heading", font=("DejaVu Sans", 11, "bold"))

        init_db()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.products_tab = ttk.Frame(self.notebook, padding=8)
        self.sales_tab = ttk.Frame(self.notebook, padding=8)
        self.history_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.products_tab, text="المنتجات")
        self.notebook.add(self.sales_tab, text="البيع")
        self.notebook.add(self.history_tab, text="المبيعات")

        # Product form state.
        self.product_id_var = tk.StringVar()
        self.product_name_var = tk.StringVar()
        self.product_price_var = tk.StringVar()
        self.product_qty_var = tk.StringVar()

        # Sale state.
        self.sale_product_var = tk.StringVar()
        self.sale_qty_var = tk.StringVar(value="1")
        self.sale_paid_var = tk.StringVar()
        self.sale_total_var = tk.StringVar(value="0.00 ل.س")
        self.sale_change_var = tk.StringVar(value="0.00 ل.س")
        self.product_map: dict[str, int] = {}

        self._build_products_tab()
        self._build_sales_tab()
        self._build_history_tab()

        self._refresh_products()
        self._refresh_sales_history()

        status = ttk.Label(
            self,
            text=f"قاعدة البيانات: {DB_PATH}",
            anchor="e",
            padding=(10, 4),
        )
        status.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------ products
    def _build_products_tab(self) -> None:
        form = ttk.LabelFrame(self.products_tab, text="بيانات المنتج", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="اسم المنتج").grid(row=0, column=1, sticky="e", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.product_name_var, width=34, justify="right").grid(
            row=0, column=0, sticky="w", padx=6, pady=4
        )

        ttk.Label(form, text="السعر (ل.س)").grid(row=1, column=1, sticky="e", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.product_price_var, width=34, justify="right").grid(
            row=1, column=0, sticky="w", padx=6, pady=4
        )

        ttk.Label(form, text="الكمية").grid(row=2, column=1, sticky="e", padx=6, pady=4)
        ttk.Entry(form, textvariable=self.product_qty_var, width=34, justify="right").grid(
            row=2, column=0, sticky="w", padx=6, pady=4
        )

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(8, 0))
        for text, command in (
            ("إضافة", self._add_product),
            ("تعديل", self._update_product),
            ("حذف", self._delete_product),
            ("مسح", self._clear_product_form),
        ):
            ttk.Button(buttons, text=text, command=command).pack(side="right", padx=4)

        tree_frame = ttk.Frame(self.products_tab)
        tree_frame.pack(fill="both", expand=True)
        columns = ("id", "name", "price", "quantity")
        self.products_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=16
        )
        headings = {
            "id": ("#", 70),
            "name": ("اسم المنتج", 360),
            "price": ("السعر", 160),
            "quantity": ("الكمية", 120),
        }
        for column, (heading, width) in headings.items():
            self.products_tree.heading(column, text=heading)
            self.products_tree.column(column, width=width, anchor="center")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        self.products_tree.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.products_tree.bind("<<TreeviewSelect>>", self._product_selected)

    def _product_selected(self, _event: Any = None) -> None:
        selected = self.products_tree.selection()
        if not selected:
            return
        values = self.products_tree.item(selected[0], "values")
        self.product_id_var.set(str(values[0]))
        self.product_name_var.set(str(values[1]))
        self.product_price_var.set(str(values[2]))
        self.product_qty_var.set(str(values[3]))

    def _clear_product_form(self) -> None:
        self.product_id_var.set("")
        self.product_name_var.set("")
        self.product_price_var.set("")
        self.product_qty_var.set("")

    def _read_product_form(self) -> tuple[str, float, int]:
        name = self.product_name_var.get()
        try:
            price = float(self.product_price_var.get().replace(",", "."))
        except ValueError as exc:
            raise ValueError("السعر يجب أن يكون رقماً") from exc
        try:
            quantity = int(self.product_qty_var.get())
        except ValueError as exc:
            raise ValueError("الكمية يجب أن تكون عدداً صحيحاً") from exc
        return name, price, quantity

    def _add_product(self) -> None:
        try:
            name, price, quantity = self._read_product_form()
            add_product(name, price, quantity)
        except Exception as exc:  # ValueError and sqlite3 errors
            messagebox.showerror("خطأ", str(exc))
            return
        self._clear_product_form()
        self._refresh_products()
        messagebox.showinfo("تم", "تمت إضافة المنتج")

    def _update_product(self) -> None:
        product_id_text = self.product_id_var.get().strip()
        if not product_id_text:
            messagebox.showwarning("تنبيه", "اختر منتجاً من القائمة أولاً")
            return
        try:
            name, price, quantity = self._read_product_form()
            update_product(int(product_id_text), name, price, quantity)
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))
            return
        self._clear_product_form()
        self._refresh_products()
        messagebox.showinfo("تم", "تم تعديل المنتج")

    def _delete_product(self) -> None:
        product_id_text = self.product_id_var.get().strip()
        if not product_id_text:
            messagebox.showwarning("تنبيه", "اختر منتجاً من القائمة أولاً")
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف هذا المنتج؟"):
            return
        try:
            delete_product(int(product_id_text))
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))
            return
        self._clear_product_form()
        self._refresh_products()

    def _refresh_products(self) -> None:
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        for product in list_products():
            self.products_tree.insert(
                "",
                "end",
                values=(
                    product["id"],
                    product["name"],
                    f"{float(product['price']):.2f}",
                    product["quantity"],
                ),
            )
        self._refresh_product_combobox()

    def _refresh_product_combobox(self) -> None:
        products = list_products()
        self.product_map = {f"{p['name']}  ({p['quantity']})": int(p["id"]) for p in products}
        values = list(self.product_map)
        self.sale_product_combo["values"] = values
        if values and self.sale_product_var.get() not in values:
            self.sale_product_var.set(values[0])
        elif not values:
            self.sale_product_var.set("")

    # --------------------------------------------------------------------- sales
    def _build_sales_tab(self) -> None:
        form = ttk.LabelFrame(self.sales_tab, text="عملية بيع", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="المنتج").grid(row=0, column=1, sticky="e", padx=6, pady=4)
        self.sale_product_combo = ttk.Combobox(
            form, textvariable=self.sale_product_var, state="readonly", width=40, justify="right"
        )
        self.sale_product_combo.grid(row=0, column=0, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="الكمية").grid(row=1, column=1, sticky="e", padx=6, pady=4)
        ttk.Spinbox(
            form, from_=1, to=100000, textvariable=self.sale_qty_var, width=38, justify="right"
        ).grid(row=1, column=0, sticky="w", padx=6, pady=4)

        ttk.Label(form, text="الإجمالي").grid(row=2, column=1, sticky="e", padx=6, pady=4)
        ttk.Label(form, textvariable=self.sale_total_var, width=40, anchor="e").grid(
            row=2, column=0, sticky="w", padx=6, pady=4
        )

        ttk.Label(form, text="المبلغ المدفوع").grid(row=3, column=1, sticky="e", padx=6, pady=4)
        paid_entry = ttk.Entry(form, textvariable=self.sale_paid_var, width=42, justify="right")
        paid_entry.grid(row=3, column=0, sticky="w", padx=6, pady=4)
        paid_entry.bind("<Return>", lambda _event: self._complete_sale())

        ttk.Label(form, text="الباقي").grid(row=4, column=1, sticky="e", padx=6, pady=4)
        ttk.Label(form, textvariable=self.sale_change_var, width=40, anchor="e").grid(
            row=4, column=0, sticky="w", padx=6, pady=4
        )

        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text="إتمام البيع", command=self._complete_sale).pack(side="right", padx=4)
        ttk.Button(buttons, text="حساب", command=self._update_sale_totals).pack(side="right", padx=4)

        hint = ttk.Label(
            self.sales_tab,
            text="اختر المنتج والكمية، أدخل المبلغ المدفوع، ثم اضغط «إتمام البيع».",
            anchor="e",
        )
        hint.pack(fill="x", pady=4)

        self.sale_product_var.trace_add("write", lambda *_: self._update_sale_totals())
        self.sale_qty_var.trace_add("write", lambda *_: self._update_sale_totals())
        self.sale_paid_var.trace_add("write", lambda *_: self._update_sale_totals())

    def _selected_product(self) -> dict[str, Any] | None:
        label = self.sale_product_var.get()
        product_id = self.product_map.get(label)
        if product_id is None:
            return None
        return next((p for p in list_products() if int(p["id"]) == product_id), None)

    def _update_sale_totals(self) -> None:
        product = self._selected_product()
        if product is None:
            self.sale_total_var.set("0.00 ل.س")
            self.sale_change_var.set("0.00 ل.س")
            return
        try:
            quantity = int(self.sale_qty_var.get())
        except ValueError:
            self.sale_total_var.set("كمية غير صالحة")
            self.sale_change_var.set("")
            return
        if quantity <= 0:
            self.sale_total_var.set("كمية غير صالحة")
            self.sale_change_var.set("")
            return
        if quantity > int(product["quantity"]):
            self.sale_total_var.set("المخزون غير كافٍ")
            self.sale_change_var.set("")
            return
        total = float(product["price"]) * quantity
        self.sale_total_var.set(money(total))
        paid_text = self.sale_paid_var.get().strip()
        if not paid_text:
            self.sale_change_var.set("0.00 ل.س")
            return
        try:
            paid = float(paid_text.replace(",", "."))
        except ValueError:
            self.sale_change_var.set("مبلغ غير صالح")
            return
        change = paid - total
        if change < 0:
            self.sale_change_var.set("غير كافٍ")
        else:
            self.sale_change_var.set(money(change))

    def _complete_sale(self) -> None:
        product = self._selected_product()
        if product is None:
            messagebox.showwarning("تنبيه", "اختر منتجاً")
            return
        try:
            quantity = int(self.sale_qty_var.get())
            paid = float(self.sale_paid_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("خطأ", "تحقق من الكمية والمبلغ المدفوع")
            return
        try:
            sale = create_sale(int(product["id"]), quantity, paid)
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))
            return
        messagebox.showinfo(
            "تم البيع",
            f"المنتج: {sale['product_name']}\n"
            f"الكمية: {sale['quantity']}\n"
            f"الإجمالي: {money(sale['total'])}\n"
            f"المدفوع: {money(sale['paid'])}\n"
            f"الباقي: {money(sale['change'])}",
        )
        self.sale_qty_var.set("1")
        self.sale_paid_var.set("")
        self._refresh_products()
        self._update_sale_totals()
        self._refresh_sales_history()

    # --------------------------------------------------------------- history
    def _build_history_tab(self) -> None:
        top = ttk.Frame(self.history_tab)
        top.pack(fill="x", pady=(0, 8))
        self.today_total_var = tk.StringVar(value="0.00 ل.س")
        ttk.Label(top, text="إجمالي مبيعات اليوم:", anchor="e").pack(side="right", padx=6)
        ttk.Label(top, textvariable=self.today_total_var, anchor="e").pack(side="right", padx=6)
        ttk.Button(top, text="تحديث", command=self._refresh_sales_history).pack(side="left", padx=6)

        tree_frame = ttk.Frame(self.history_tab)
        tree_frame.pack(fill="both", expand=True)
        columns = ("id", "date", "product", "quantity", "unit", "total", "paid", "change")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        headings = {
            "id": ("#", 60),
            "date": ("التاريخ", 170),
            "product": ("المنتج", 220),
            "quantity": ("الكمية", 80),
            "unit": ("سعر الوحدة", 120),
            "total": ("الإجمالي", 120),
            "paid": ("المدفوع", 120),
            "change": ("الباقي", 120),
        }
        for column, (heading, width) in headings.items():
            self.history_tree.heading(column, text=heading)
            self.history_tree.column(column, width=width, anchor="center")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _refresh_sales_history(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for sale in list_sales():
            self.history_tree.insert(
                "",
                "end",
                values=(
                    sale["id"],
                    sale["created_at"],
                    sale["product_name"],
                    sale["quantity"],
                    f"{float(sale['unit_price']):.2f}",
                    f"{float(sale['total']):.2f}",
                    f"{float(sale['paid']):.2f}",
                    f"{float(sale['change']):.2f}",
                ),
            )
        self.today_total_var.set(money(today_total()))


def main() -> None:
    app = SutApp()
    app.mainloop()


if __name__ == "__main__":
    main()
