from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from database import add_product, delete_product, list_products, update_product


class InventoryFrame(ttk.Frame):
    def __init__(self, master, on_inventory_changed=None):
        super().__init__(master, padding=16)
        self.on_inventory_changed = on_inventory_changed
        self.selected_product_id = None
        self._build_layout()
        self.refresh_products()

    def _build_layout(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(self, text="Product Details", padding=12)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(form, text="Category").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Label(form, text="Price").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Label(form, text="Stock Qty").grid(row=3, column=0, sticky="w", pady=4)

        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.search_var = tk.StringVar()

        ttk.Entry(form, textvariable=self.name_var, width=28).grid(row=0, column=1, pady=4)
        ttk.Entry(form, textvariable=self.category_var, width=28).grid(row=1, column=1, pady=4)
        ttk.Entry(form, textvariable=self.price_var, width=28).grid(row=2, column=1, pady=4)
        ttk.Entry(form, textvariable=self.stock_var, width=28).grid(row=3, column=1, pady=4)

        button_bar = ttk.Frame(form)
        button_bar.grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="ew")
        ttk.Button(button_bar, text="Add Product", command=self.add_product_action).grid(row=0, column=0, padx=4)
        ttk.Button(button_bar, text="Update Product", command=self.update_product_action).grid(row=0, column=1, padx=4)
        ttk.Button(button_bar, text="Delete Product", command=self.delete_product_action).grid(row=0, column=2, padx=4)
        ttk.Button(button_bar, text="Clear", command=self.clear_form).grid(row=0, column=3, padx=4)

        product_section = ttk.LabelFrame(self, text="Inventory", padding=12)
        product_section.grid(row=0, column=1, rowspan=2, sticky="nsew")
        product_section.columnconfigure(0, weight=1)
        product_section.rowconfigure(1, weight=1)

        search_bar = ttk.Frame(product_section)
        search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        search_bar.columnconfigure(1, weight=1)
        ttk.Label(search_bar, text="Search").grid(row=0, column=0, padx=(0, 8))
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_products())
        ttk.Button(search_bar, text="Export CSV", command=self.export_to_csv).grid(row=0, column=2, padx=(8, 0))

        columns = ("ID", "Name", "Category", "Price", "Stock")
        self.tree = ttk.Treeview(product_section, columns=columns, show="headings", height=16)
        for column, width in zip(columns, (70, 180, 160, 100, 100)):
            self.tree.heading(column, text=column)
            self.tree.column(column, width=width, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        scrollbar = ttk.Scrollbar(product_section, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _validate_form(self):
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        if not name:
            raise ValueError("Product name is required.")
        try:
            price = float(self.price_var.get())
            stock = int(self.stock_var.get())
        except ValueError as exc:
            raise ValueError("Price must be numeric and stock must be an integer.") from exc
        if price < 0 or stock < 0:
            raise ValueError("Price and stock must be zero or greater.")
        return name, category, price, stock

    def add_product_action(self):
        try:
            name, category, price, stock = self._validate_form()
            add_product(name, category, price, stock)
        except ValueError as exc:
            messagebox.showerror("Invalid Product", str(exc))
            return

        self.refresh_products()
        self.clear_form()
        self._notify_inventory_changed()

    def update_product_action(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select Product", "Choose a product to update.")
            return

        try:
            name, category, price, stock = self._validate_form()
            update_product(self.selected_product_id, name, category, price, stock)
        except ValueError as exc:
            messagebox.showerror("Invalid Product", str(exc))
            return

        self.refresh_products()
        self.clear_form()
        self._notify_inventory_changed()

    def delete_product_action(self):
        if not self.selected_product_id:
            messagebox.showwarning("Select Product", "Choose a product to delete.")
            return

        if not messagebox.askyesno("Delete Product", "Delete the selected product?"):
            return

        delete_product(self.selected_product_id)
        self.refresh_products()
        self.clear_form()
        self._notify_inventory_changed()

    def clear_form(self):
        self.selected_product_id = None
        self.name_var.set("")
        self.category_var.set("")
        self.price_var.set("")
        self.stock_var.set("")
        self.tree.selection_remove(*self.tree.selection())

    def refresh_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for product in list_products(self.search_var.get()):
            self.tree.insert(
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

    def on_tree_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        self.selected_product_id = int(values[0])
        self.name_var.set(values[1])
        self.category_var.set(values[2])
        self.price_var.set(values[3])
        self.stock_var.set(values[4])

    def export_to_csv(self):
        products = list_products(self.search_var.get())
        if not products:
            messagebox.showinfo("No Data", "There are no products to export.")
            return

        export_path = filedialog.asksaveasfilename(
            title="Save Inventory CSV",
            initialfile="inventory_export.csv",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not export_path:
            return

        dataframe = pd.DataFrame(products)
        dataframe.rename(
            columns={"ID": "Product ID", "Stock_Qty": "Stock Qty"},
            inplace=True,
        )
        dataframe.to_csv(Path(export_path), index=False)
        messagebox.showinfo("Export Complete", f"Inventory exported to:\n{export_path}")

    def _notify_inventory_changed(self):
        if callable(self.on_inventory_changed):
            self.on_inventory_changed()
