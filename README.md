---

# 🧾 Offline Billing & Inventory Management System

A desktop application built for small businesses to manage billing and inventory entirely offline — no internet required. Features GST-compliant invoice generation, product management, and customer records, all in a clean Tkinter interface.

---

## 📌 Features

- 🛒 Product management — add, edit, and delete inventory items
- 👤 Customer records management
- 🧮 Automated GST calculation on bills
- 🔍 Real-time search across products and customers
- 🧾 PDF invoice export with print-ready GST-compliant bills
- 📦 Fully offline — no internet connection required

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python |
| GUI | Tkinter |
| Database | SQLite |
| PDF Export | ReportLab |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/PHHS-07/Oflline-Billing-and-Inventory-System.git
cd Oflline-Billing-and-Inventory-System
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python main.py
```

> 💡 No database setup needed — SQLite creates the database file automatically on first run.

---

## 📦 Requirements

```txt
reportlab
```

Install with:

```bash
pip install -r requirements.txt
```

> SQLite is built into Python — no separate installation required.

---

## 🚀 Usage

1. Launch the app with `python main.py`
2. Add products and customers via their respective modules
3. Create a new bill — GST is calculated automatically
4. Export the bill as a PDF for printing or records

---

## ⚖️ License

This project is licensed under the **MIT License**. See the LICENSE file for details.

---

## 👤 Author

Created by **Hari Hara Sudhan P**

- GitHub: [github.com/PHHS-07](https://github.com/PHHS-07)
- Email: [phariharasudhan2004@gmail.com](mailto:phariharasudhan2004@gmail.com)

---

## ⚠️ Disclaimer

This application is intended for **small business and educational use**. Always verify generated bills and tax calculations before use in a production environment.

---
