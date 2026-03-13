from pathlib import Path
import tkinter as tk
from tkinter import ttk

from billing import BillingFrame
from database import initialize_database
from invoice_history import InvoiceHistoryFrame
from inventory import InventoryFrame


BASE_DIR = Path(__file__).resolve().parent


class BillingSystemApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Billing System")
        self.geometry("1200x720")
        self.minsize(1000, 640)
        self._set_icon()
        self._configure_style()
        self._build_ui()

    def _set_icon(self):
        icon_path = BASE_DIR / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass

    def _configure_style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.invoice_history_frame = InvoiceHistoryFrame(notebook)
        self.billing_frame = BillingFrame(notebook, on_invoice_created=self._handle_invoice_created)
        self.inventory_frame = InventoryFrame(notebook, on_inventory_changed=self.billing_frame.refresh_products)

        notebook.add(self.billing_frame, text="Billing")
        notebook.add(self.inventory_frame, text="Inventory")
        notebook.add(self.invoice_history_frame, text="Invoice History")

    def _handle_invoice_created(self, _invoice_no):
        self.invoice_history_frame.refresh_invoices()


def main():
    initialize_database()
    app = BillingSystemApp()
    app.mainloop()


if __name__ == "__main__":
    main()
