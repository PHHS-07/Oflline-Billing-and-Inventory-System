import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventory.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS Products (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Category TEXT,
                Price REAL,
                Stock_Qty INTEGER
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS Invoices (
                Invoice_No INTEGER PRIMARY KEY AUTOINCREMENT,
                Date TEXT,
                Customer_Name TEXT,
                Total_Amount REAL,
                GST REAL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS Invoice_Items (
                Item_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Invoice_No INTEGER,
                Product_ID INTEGER,
                Qty INTEGER,
                Price REAL,
                FOREIGN KEY (Invoice_No) REFERENCES Invoices(Invoice_No) ON DELETE CASCADE,
                FOREIGN KEY (Product_ID) REFERENCES Products(ID)
            )
            """
        )


def add_product(name, category, price, stock):
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO Products (Name, Category, Price, Stock_Qty)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), category.strip(), float(price), int(stock)),
        )
        return cursor.lastrowid


def get_product(product_id):
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM Products WHERE ID = ?",
            (product_id,),
        ).fetchone()
    return dict(row) if row else None


def list_products(search_term=""):
    query = "SELECT * FROM Products"
    params = ()
    if search_term:
        query += " WHERE Name LIKE ? OR Category LIKE ?"
        like_term = f"%{search_term.strip()}%"
        params = (like_term, like_term)
    query += " ORDER BY Name COLLATE NOCASE"

    with closing(get_connection()) as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_product(product_id, name, category, price, stock):
    with closing(get_connection()) as connection, connection:
        connection.execute(
            """
            UPDATE Products
            SET Name = ?, Category = ?, Price = ?, Stock_Qty = ?
            WHERE ID = ?
            """,
            (name.strip(), category.strip(), float(price), int(stock), product_id),
        )


def delete_product(product_id):
    with closing(get_connection()) as connection, connection:
        connection.execute("DELETE FROM Products WHERE ID = ?", (product_id,))


def update_stock(product_id, qty):
    with closing(get_connection()) as connection, connection:
        product = connection.execute(
            "SELECT Stock_Qty FROM Products WHERE ID = ?",
            (product_id,),
        ).fetchone()
        if not product:
            raise ValueError("Product not found.")

        new_stock = int(product["Stock_Qty"]) - int(qty)
        if new_stock < 0:
            raise ValueError("Insufficient stock.")

        connection.execute(
            "UPDATE Products SET Stock_Qty = ? WHERE ID = ?",
            (new_stock, product_id),
        )


def save_invoice(customer, total, gst, items=None, invoice_date=None):
    items = items or []
    invoice_date = invoice_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO Invoices (Date, Customer_Name, Total_Amount, GST)
            VALUES (?, ?, ?, ?)
            """,
            (invoice_date, customer.strip(), float(total), float(gst)),
        )
        invoice_no = cursor.lastrowid

        for item in items:
            connection.execute(
                """
                INSERT INTO Invoice_Items (Invoice_No, Product_ID, Qty, Price)
                VALUES (?, ?, ?, ?)
                """,
                (invoice_no, item["product_id"], int(item["qty"]), float(item["price"])),
            )

            product = connection.execute(
                "SELECT Stock_Qty FROM Products WHERE ID = ?",
                (item["product_id"],),
            ).fetchone()
            if not product:
                raise ValueError(f"Product ID {item['product_id']} not found.")

            new_stock = int(product["Stock_Qty"]) - int(item["qty"])
            if new_stock < 0:
                raise ValueError(f"Insufficient stock for product ID {item['product_id']}.")

            connection.execute(
                "UPDATE Products SET Stock_Qty = ? WHERE ID = ?",
                (new_stock, item["product_id"]),
            )

    return invoice_no


def get_invoice(invoice_no):
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM Invoices WHERE Invoice_No = ?",
            (invoice_no,),
        ).fetchone()
    return dict(row) if row else None


def list_invoices(search_term=""):
    query = "SELECT * FROM Invoices"
    params = ()
    if search_term:
        query += " WHERE Customer_Name LIKE ? OR Date LIKE ?"
        like_term = f"%{search_term.strip()}%"
        params = (like_term, like_term)
    query += " ORDER BY Invoice_No DESC"

    with closing(get_connection()) as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_invoice_items(invoice_no):
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT ii.Item_ID, ii.Invoice_No, ii.Product_ID, ii.Qty, ii.Price, p.Name
            FROM Invoice_Items ii
            JOIN Products p ON p.ID = ii.Product_ID
            WHERE ii.Invoice_No = ?
            ORDER BY ii.Item_ID
            """,
            (invoice_no,),
        ).fetchall()
    return [dict(row) for row in rows]
