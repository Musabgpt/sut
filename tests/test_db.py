import os
import tempfile
import unittest

from sut.db import (
    add_product,
    create_sale,
    delete_product,
    init_db,
    list_products,
    list_sales,
    today_total,
    update_product,
)


class ProductTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        init_db(self.db_path)

    def test_add_and_list_product(self) -> None:
        product_id = add_product("تفاح", 5000.0, 10, self.db_path)
        products = list_products(self.db_path)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["id"], product_id)
        self.assertEqual(products[0]["name"], "تفاح")
        self.assertEqual(products[0]["quantity"], 10)

    def test_update_product(self) -> None:
        product_id = add_product("برتقال", 4000.0, 5, self.db_path)
        update_product(product_id, "برتقال ممتاز", 4500.0, 7, self.db_path)
        product = list_products(self.db_path)[0]
        self.assertEqual(product["name"], "برتقال ممتاز")
        self.assertEqual(product["price"], 4500.0)
        self.assertEqual(product["quantity"], 7)

    def test_delete_product(self) -> None:
        product_id = add_product("موز", 3000.0, 3, self.db_path)
        delete_product(product_id, self.db_path)
        self.assertEqual(list_products(self.db_path), [])


class SaleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        init_db(self.db_path)
        self.product_id = add_product("رز", 10000.0, 5, self.db_path)

    def test_sale_calculates_change_and_updates_stock(self) -> None:
        sale = create_sale(self.product_id, 2, 25000.0, self.db_path)
        self.assertEqual(sale["total"], 20000.0)
        self.assertEqual(sale["change"], 5000.0)
        product = list_products(self.db_path)[0]
        self.assertEqual(product["quantity"], 3)

    def test_insufficient_stock_raises(self) -> None:
        with self.assertRaises(ValueError):
            create_sale(self.product_id, 10, 100000.0, self.db_path)

    def test_insufficient_payment_raises(self) -> None:
        with self.assertRaises(ValueError):
            create_sale(self.product_id, 1, 5000.0, self.db_path)

    def test_today_total(self) -> None:
        create_sale(self.product_id, 1, 10000.0, self.db_path)
        create_sale(self.product_id, 1, 10000.0, self.db_path)
        self.assertEqual(today_total(self.db_path), 20000.0)
        self.assertEqual(len(list_sales(10, self.db_path)), 2)


if __name__ == "__main__":
    unittest.main()
