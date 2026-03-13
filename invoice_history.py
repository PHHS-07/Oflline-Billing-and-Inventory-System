from pathlib import Path
import os
import tkinter as tk
from tkinter import messagebox, ttk

from database import get_invoice_items, list_invoices


BASE_DIR = Path(__file__).resolve().parent
INVOICE_DIR = BASE_DIR / "invoices"


class InvoiceHistoryFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=16)
        self.invoices = []
        self.selected_invoice_no = None
        self.search_var = tk.StringVar()
        self.summary_var = tk.StringVar(value="Select an invoice to view details.")
        self._build_layout()
        self.refresh_invoices()

    def _build_layout(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Search Invoice").grid(row=0, column=0, sticky="w", padx=(0, 8))
        search_entry = ttk.Entry(header, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_invoices())
        ttk.Button(header, text="Refresh", command=self.refresh_invoices).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(header, text="Open PDF", command=self.open_selected_pdf).grid(row=0, column=3, padx=(8, 0))

        invoice_panel = ttk.LabelFrame(self, text="Invoices", padding=12)
        invoice_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        invoice_panel.columnconfigure(0, weight=1)
        invoice_panel.rowconfigure(0, weight=1)

        invoice_columns = ("Invoice No", "Date", "Customer", "GST", "Total")
        self.invoice_tree = ttk.Treeview(invoice_panel, columns=invoice_columns, show="headings", height=18)
        for column, width in zip(invoice_columns, (90, 170, 180, 90, 100)):
            self.invoice_tree.heading(column, text=column)
            self.invoice_tree.column(column, width=width, anchor="center")
        self.invoice_tree.grid(row=0, column=0, sticky="nsew")
        self.invoice_tree.bind("<<TreeviewSelect>>", self.on_invoice_select)

        invoice_scroll = ttk.Scrollbar(invoice_panel, orient="vertical", command=self.invoice_tree.yview)
        invoice_scroll.grid(row=0, column=1, sticky="ns")
        self.invoice_tree.configure(yscrollcommand=invoice_scroll.set)

        details_panel = ttk.LabelFrame(self, text="Invoice Details", padding=12)
        details_panel.grid(row=1, column=1, sticky="nsew")
        details_panel.columnconfigure(0, weight=1)
        details_panel.rowconfigure(1, weight=1)

        ttk.Label(details_panel, textvariable=self.summary_var, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 10))

        item_columns = ("Product ID", "Product", "Qty", "Price", "Line Total")
        self.item_tree = ttk.Treeview(details_panel, columns=item_columns, show="headings", height=16)
        for column, width in zip(item_columns, (90, 150, 70, 80, 90)):
            self.item_tree.heading(column, text=column)
            self.item_tree.column(column, width=width, anchor="center")
        self.item_tree.grid(row=1, column=0, sticky="nsew")

        item_scroll = ttk.Scrollbar(details_panel, orient="vertical", command=self.item_tree.yview)
        item_scroll.grid(row=1, column=1, sticky="ns")
        self.item_tree.configure(yscrollcommand=item_scroll.set)

    def refresh_invoices(self):
        self.invoices = list_invoices(self.search_var.get())

        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)

        for invoice in self.invoices:
            self.invoice_tree.insert(
                "",
                "end",
                values=(
                    invoice["Invoice_No"],
                    invoice["Date"],
                    invoice["Customer_Name"],
                    f"{float(invoice['GST']):.2f}",
                    f"{float(invoice['Total_Amount']):.2f}",
                ),
            )

        if self.selected_invoice_no:
            for child in self.invoice_tree.get_children():
                values = self.invoice_tree.item(child, "values")
                if int(values[0]) == self.selected_invoice_no:
                    self.invoice_tree.selection_set(child)
                    self.invoice_tree.focus(child)
                    self.on_invoice_select(None)
                    return

        self.selected_invoice_no = None
        self._clear_details()

    def on_invoice_select(self, _event):
        selection = self.invoice_tree.selection()
        if not selection:
            self.selected_invoice_no = None
            self._clear_details()
            return

        values = self.invoice_tree.item(selection[0], "values")
        self.selected_invoice_no = int(values[0])
        items = get_invoice_items(self.selected_invoice_no)

        for child in self.item_tree.get_children():
            self.item_tree.delete(child)

        subtotal = 0.0
        for item in items:
            line_total = float(item["Qty"]) * float(item["Price"])
            subtotal += line_total
            self.item_tree.insert(
                "",
                "end",
                values=(
                    item["Product_ID"],
                    item["Name"],
                    item["Qty"],
                    f"{float(item['Price']):.2f}",
                    f"{line_total:.2f}",
                ),
            )

        self.summary_var.set(
            "\n".join(
                [
                    f"Invoice No: {values[0]}",
                    f"Date: {values[1]}",
                    f"Customer: {values[2]}",
                    f"Subtotal: {subtotal:.2f}",
                    f"GST: {values[3]}",
                    f"Total: {values[4]}",
                ]
            )
        )

    def open_selected_pdf(self):
        if not self.selected_invoice_no:
            messagebox.showwarning("No Invoice", "Select an invoice first.")
            return

        pdf_path = INVOICE_DIR / f"invoice_{self.selected_invoice_no}.pdf"
        if not pdf_path.exists():
            messagebox.showerror("PDF Missing", f"Could not find:\n{pdf_path}")
            return

        os.startfile(str(pdf_path))

    def _clear_details(self):
        for child in self.item_tree.get_children():
            self.item_tree.delete(child)
        self.summary_var.set("Select an invoice to view details.")
