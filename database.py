"""
Database Helper Module for IT Ticket Tracking System
Handles SQLite database connection, initialization, migrations, and CRUD operations.
"""

import os
import sqlite3
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "tickets.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")

DEFAULT_EMPLOYEES = [
    "Monte",
    "Seth",
    "Nate",
    "Duda",
    "Darin"
]

def ensure_directories_exist():
    """Ensure data and backup directories exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection with row factory and foreign keys enabled."""
    ensure_directories_exist()
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables and seed default employees if database is empty."""
    ensure_directories_exist()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Employees Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        
        # Tickets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                helped_person TEXT NOT NULL,
                issue TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                resolution TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            );
        """)
        
        # Seed default employees if none exist
        cursor.execute("SELECT COUNT(*) FROM employees;")
        count = cursor.fetchone()[0]
        if count == 0:
            for name in DEFAULT_EMPLOYEES:
                cursor.execute(
                    "INSERT INTO employees (name, active) VALUES (?, 1);",
                    (name,)
                )
        conn.commit()

# --- EMPLOYEE OPERATIONS ---

def get_employees(active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve employees from database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT id, name, active, created_at FROM employees WHERE active = 1 ORDER BY name ASC;")
        else:
            cursor.execute("SELECT id, name, active, created_at FROM employees ORDER BY name ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def add_employee(name: str) -> bool:
    """Add a new employee."""
    name_clean = name.strip()
    if not name_clean:
        raise ValueError("Employee name cannot be empty.")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, active) VALUES (?, 1);", (name_clean,))
        conn.commit()
        return True

def update_employee(employee_id: int, name: str, active: int) -> bool:
    """Update employee name and active status."""
    name_clean = name.strip()
    if not name_clean:
        raise ValueError("Employee name cannot be empty.")
        
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE employees SET name = ?, active = ? WHERE id = ?;",
            (name_clean, int(active), employee_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
    """Get employee by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, active, created_at FROM employees WHERE id = ?;", (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- TICKET OPERATIONS ---

def ticket_id_exists(ticket_id: str) -> bool:
    """Check if a ticket ID already exists in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tickets WHERE ticket_id = ?;", (ticket_id,))
        return cursor.fetchone() is not None

def add_ticket(ticket_id: str, helped_person: str, issue: str, employee_id: int, resolution: str, created_at: str) -> bool:
    """Insert a new ticket record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (ticket_id, created_at, helped_person, issue, employee_id, resolution)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (ticket_id, created_at, helped_person.strip(), issue.strip(), employee_id, resolution.strip()))
        conn.commit()
        return True

def update_ticket(ticket_id: str, helped_person: str, issue: str, employee_id: int, resolution: str, updated_at: str) -> bool:
    """Update an existing ticket record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets
            SET helped_person = ?, issue = ?, employee_id = ?, resolution = ?, updated_at = ?
            WHERE ticket_id = ?;
        """, (helped_person.strip(), issue.strip(), employee_id, resolution.strip(), updated_at, ticket_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_ticket(ticket_id: str) -> bool:
    """Delete a ticket by ticket_id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE ticket_id = ?;", (ticket_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_all_tickets_df() -> pd.DataFrame:
    """
    Retrieve all tickets joined with employee name as a Pandas DataFrame.
    Newest tickets appear first by default.
    """
    query = """
        SELECT 
            t.ticket_id AS 'Ticket ID',
            SUBSTR(t.created_at, 1, 10) AS 'Date',
            SUBSTR(t.created_at, 12, 8) AS 'Time',
            t.helped_person AS 'Who Was Helped',
            t.issue AS 'Issue',
            e.name AS 'Employee',
            t.employee_id AS 'Employee ID',
            t.resolution AS 'How It Was Resolved',
            t.created_at AS 'Created At',
            t.updated_at AS 'Updated At'
        FROM tickets t
        LEFT JOIN employees e ON t.employee_id = e.id
        ORDER BY t.created_at DESC;
    """
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)
        return df

def get_ticket_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a specific ticket."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.ticket_id, t.created_at, t.updated_at, t.helped_person, 
                   t.issue, t.employee_id, e.name AS employee_name, t.resolution
            FROM tickets t
            LEFT JOIN employees e ON t.employee_id = e.id
            WHERE t.ticket_id = ?;
        """, (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- BACKUP UTILITIES ---

def create_db_backup() -> str:
    """Create a timestamped backup of the database file."""
    ensure_directories_exist()
    if not os.path.exists(DB_PATH):
        init_db()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"tickets_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    shutil.copy2(DB_PATH, backup_path)
    return backup_path
