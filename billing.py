from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

import pandas as pd

from database import list_products, save_invoice
from pdf_generator import generate_invoice_pdf


class BillingFrame(ttk.Frame):
    GST_RATE = 0.18

    def __init__(self, master, on_invoice_created=None):
        super().__init__(master, padding=16)
        self.on_invoice_created = on_invoice_created
        self.products = []
        self.cart_items = []
        self._build_layout()
        self.refresh_products()

    def _build_layout(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.LabelFrame(self, text="Invoice Details", padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.customer_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.selected_product_var = tk.StringVar()
        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        ttk.Label(header, text="Customer Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(header, textvariable=self.customer_var, width=28).grid(row=0, column=1, padx=(8, 18))
        ttk.Label(header, text="Search Product").grid(row=0, column=2, sticky="w")
        search_entry = ttk.Entry(header, textvariable=self.search_var, width=24)
        search_entry.grid(row=0, column=3, padx=(8, 18))
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_products())
        ttk.Label(header, text="Quantity").grid(row=0, column=4, sticky="w")
        ttk.Entry(header, textvariable=self.quantity_var, width=8).grid(row=0, column=5, padx=(8, 0))

        left_panel = ttk.LabelFrame(self, text="Available Products", padding=12)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)

        self.product_box = ttk.Combobox(
            left_panel,
            textvariable=self.selected_product_var,
            state="readonly",
        )
        self.product_box.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(left_panel, text="Add To Cart", command=self.add_to_cart).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        product_columns = ("ID", "Name", "Category", "Price", "Stock")
        self.product_tree = ttk.Treeview(left_panel, columns=product_columns, show="headings", height=14)
        for column, width in zip(product_columns, (60, 160, 140, 90, 80)):
            self.product_tree.heading(column, text=column)
            self.product_tree.column(column, width=width, anchor="center")
        self.product_tree.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select)

        right_panel = ttk.LabelFrame(self, text="Cart", padding=12)
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)

        cart_columns = ("Product ID", "Name", "Qty", "Price", "Total")
        self.cart_tree = ttk.Treeview(right_panel, columns=cart_columns, show="headings", height=14)
        for column, width in zip(cart_columns, (80, 150, 70, 80, 90)):
            self.cart_tree.heading(column, text=column)
            self.cart_tree.column(column, width=width, anchor="center")
        self.cart_tree.grid(row=0, column=0, columnspan=2, sticky="nsew")

        ttk.Button(right_panel, text="Remove Item", command=self.remove_selected_item).grid(row=1, column=0, sticky="w", pady=(8, 12))
        ttk.Button(right_panel, text="Clear Cart", command=self.clear_cart).grid(row=1, column=1, sticky="e", pady=(8, 12))

        totals = ttk.Frame(right_panel)
        totals.grid(row=2, column=0, columnspan=2, sticky="ew")
        for row_index, label in enumerate(("Subtotal", "GST (18%)", "Total")):
            ttk.Label(totals, text=label).grid(row=row_index, column=0, sticky="w", pady=4)
        ttk.Label(totals, textvariable=self.subtotal_var).grid(row=0, column=1, sticky="e")
        ttk.Label(totals, textvariable=self.gst_var).grid(row=1, column=1, sticky="e")
        ttk.Label(totals, textvariable=self.total_var, font=("Segoe UI", 10, "bold")).grid(row=2, column=1, sticky="e")

        ttk.Button(right_panel, text="Generate Invoice", command=self.checkout).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))

    def refresh_products(self):
        self.products = list_products(self.search_var.get())

        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        for product in self.products:
            self.product_tree.insert(
                "",
                "end",
                values=(
                    product["ID"],
                    product["Name"],
                    product["Category"],
                    f"{float(product['Price']):.2f}",
                    product["Stock_Qty"],
                ),
            )

        labels = [
            f"{product['ID']} - {product['Name']} ({product['Stock_Qty']} in stock)"
            for product in self.products
        ]
        self.product_box["values"] = labels
        if labels and self.selected_product_var.get() not in labels:
            self.selected_product_var.set(labels[0])
        elif not labels:
            self.selected_product_var.set("")

    def on_product_select(self, _event):
        selection = self.product_tree.selection()
        if not selection:
            return
        values = self.product_tree.item(selection[0], "values")
        self.selected_product_var.set(f"{values[0]} - {values[1]} ({values[4]} in stock)")

    def add_to_cart(self):
        selected_label = self.selected_product_var.get().strip()
        if not selected_label:
            messagebox.showwarning("No Product", "Select a product first.")
            return

        try:
            quantity = int(self.quantity_var.get())
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a whole number.")
            return

        if quantity <= 0:
            messagebox.showerror("Invalid Quantity", "Quantity must be greater than zero.")
            return

        product_id = int(selected_label.split(" - ", 1)[0])
        product = next((item for item in self.products if item["ID"] == product_id), None)
        if not product:
            messagebox.showerror("Missing Product", "The selected product is no longer available.")
            self.refresh_products()
            return

        existing_qty = sum(item["qty"] for item in self.cart_items if item["product_id"] == product_id)
        if existing_qty + quantity > int(product["Stock_Qty"]):
            messagebox.showerror("Insufficient Stock", "Requested quantity exceeds stock.")
            return

        existing_item = next((item for item in self.cart_items if item["product_id"] == product_id), None)
        if existing_item:
            existing_item["qty"] += quantity
        else:
            self.cart_items.append(
                {
                    "product_id": product["ID"],
                    "name": product["Name"],
                    "qty": quantity,
                    "price": float(product["Price"]),
                }
            )

        self.quantity_var.set("1")
        self._render_cart()

    def remove_selected_item(self):
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("No Item", "Select a cart item to remove.")
            return

        product_id = int(self.cart_tree.item(selection[0], "values")[0])
        self.cart_items = [item for item in self.cart_items if item["product_id"] != product_id]
        self._render_cart()

    def clear_cart(self):
        self.cart_items = []
        self._render_cart()

    def _render_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        for item in self.cart_items:
            line_total = item["qty"] * item["price"]
            self.cart_tree.insert(
                "",
                "end",
                values=(
                    item["product_id"],
                    item["name"],
                    item["qty"],
                    f"{item['price']:.2f}",
                    f"{line_total:.2f}",
                ),
            )

        self._update_totals()

    def _update_totals(self):
        if not self.cart_items:
            self.subtotal_var.set("0.00")
            self.gst_var.set("0.00")
            self.total_var.set("0.00")
            return

        dataframe = pd.DataFrame(self.cart_items)
        subtotal = float((dataframe["qty"] * dataframe["price"]).sum())
        gst = subtotal * self.GST_RATE
        total = subtotal + gst

        self.subtotal_var.set(f"{subtotal:.2f}")
        self.gst_var.set(f"{gst:.2f}")
        self.total_var.set(f"{total:.2f}")

    def checkout(self):
        customer = self.customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Customer Required", "Enter the customer name.")
            return
        if not self.cart_items:
            messagebox.showwarning("Cart Empty", "Add at least one product to the cart.")
            return

        self.refresh_products()

        try:
            invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subtotal = float(self.subtotal_var.get())
            gst = float(self.gst_var.get())
            total = float(self.total_var.get())

            invoice_no = save_invoice(customer, total, gst, items=self.cart_items, invoice_date=invoice_date)
            pdf_path = generate_invoice_pdf(
                invoice_no=invoice_no,
                customer_name=customer,
                invoice_date=invoice_date,
                items=self.cart_items,
                subtotal=subtotal,
                gst=gst,
                total=total,
            )
        except ValueError as exc:
            messagebox.showerror("Checkout Failed", str(exc))
            self.refresh_products()
            return

        messagebox.showinfo(
            "Invoice Created",
            f"Invoice #{invoice_no} generated successfully.\nPDF saved to:\n{pdf_path}",
        )
        self.customer_var.set("")
        self.clear_cart()
        self.refresh_products()
        if callable(self.on_invoice_created):
            self.on_invoice_created(invoice_no)
