# 🎫 IT Support Ticket Tracking System

A complete, lightweight, and modern IT Ticket Tracking System built with **Python**, **Streamlit**, **SQLite**, **Pandas**, and **Plotly**. 

Designed specifically for the small McKay School IT support team replacing legacy Excel/VBA ticket-tracking workbooks, prioritizing speed, data integrity, seamless exports, and zero-friction data entry.

---

## 🌟 Key Features

* **⚡ Rapid Ticket Logging**: Optimized input form automatically captures local timestamps and generates safe, collision-resistant unique Ticket IDs (`TK-YYYYMMDD-XXXX`).
* **📋 Comprehensive Ticket Directory**: Searchable and filterable dataset by date range, employee, ticket recipient, and keyword matching across issue & resolution descriptions.
* **📅 Dynamic Monthly Views**: Recreates monthly Excel workbook tabs dynamically using a single normalized SQLite database (no duplicate tables needed).
* **📊 Executive Dashboard**: High-level metrics (Total, Month, Today, Active Techs) paired with interactive Plotly visualizations (volume over time, staff workload distribution).
* **👥 Staff Management**: Add, update, or deactivate IT staff accounts. Deactivation preserves historical ticket links while filtering inactive staff from new ticket forms.
* **💾 Data Exports & Backups**: Export filtered or complete datasets to CSV and custom-styled Excel (`.xlsx`) files with auto-wrapped text formatting. Create timestamped database backups or download raw SQLite files directly.

---

## 📸 Screenshots

*(Placeholder for application interface screenshots)*

---

## 📋 Requirements

* **Python 3.9+** (Tested on Python 3.13)
* Dependencies specified in `requirements.txt`:
  * `streamlit`
  * `pandas`
  * `plotly`
  * `openpyxl`

---

## 🛠️ Quick Start & Installation

### 1. Clone or Download Repository
Navigate to your target working directory:
```bash
cd csrtickets
```

### 2. Create Virtual Environment
Create a clean Python virtual environment named `.venv`:
```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

* **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```
* **Windows (Command Prompt / PowerShell)**:
  ```cmd
  .venv\Scripts\activate
  ```

### 4. Install Dependencies
Install all required libraries:
```bash
pip install -r requirements.txt
```

### 5. Run the Application
Launch the Streamlit web application:
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🗄️ Database & Storage Information

* **Database File**: Stored locally at `data/tickets.db`.
* **Automatic Initialization**: The database schema initializes automatically on the first launch. Placeholder employees are seeded if no staff records exist.
* **Backups**: 
  * Timestamped database backups are stored in `data/backups/`.
  * Manual backups can be created at any time via the **Employees & Settings** tab.
  * Direct `.db` downloads are available directly from the user interface.

---

## 📂 Project Architecture

```
csrtickets/
├── app.py                  # Main Streamlit application & navigation router
├── database.py             # SQLite helper (schema, connection, CRUD operations, backups)
├── models.py               # Ticket ID generator & validation logic
├── utils.py                # CSV & Excel styled export functions, date utilities
├── pages/                  # Application views / navigation pages
│   ├── new_ticket.py       # Fast ticket entry form
│   ├── all_tickets.py      # Searchable ticket grid, inline editor, deletion & exports
│   ├── monthly_tickets.py  # Dynamic monthly analytics & reports
│   ├── dashboard.py        # Executive metrics & Plotly chart analytics
│   └── employees.py        # Employee roster management & database backup tools
├── data/                   # Local SQLite database directory (auto-created)
│   ├── tickets.db          # Active SQLite database file
│   └── backups/            # Local backup snapshot directory
├── requirements.txt        # Python package dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## 💡 Usage Workflow

1. **New Ticket**: Navigate to the default page, type recipient name, select assigned technician, enter issue & resolution details, and click **🚀 Add Ticket**.
2. **Review & Filter**: Open **All Tickets** to filter by date range, staff member, or keywords. Edit or delete existing records if required.
3. **Monthly Reporting**: Open **Tickets by Month** to review specific monthly totals and download Excel/CSV reports for management.
4. **Staff Management**: Add new team members or deactivate departing staff under **Employees & Settings**.
