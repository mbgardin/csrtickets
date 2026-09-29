"""
Database Helper Module for IT Ticket Tracking System
Supports dual storage engine: Cloud Supabase (PostgreSQL) and Local SQLite.
Seamlessly falls back to local SQLite if Supabase is offline or unconfigured.
"""

import os
import sqlite3
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st

# Supabase imports
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "tickets.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")

DEFAULT_EMPLOYEES = [
    "Alex Rivera",
    "David Chen",
    "Emily Taylor",
    "Sarah Jenkins",
    "Michael Vance"
]

# Credentials fallback (Can be overridden in Streamlit Secrets .streamlit/secrets.toml)
DEFAULT_SUPABASE_URL = "https://dcbwazzxhqcbahdleukr.supabase.co"
DEFAULT_SUPABASE_KEY = "sb_publishable_WrZIBPH203xm7ucyUwQEXg_41UVgkUu"

def get_supabase_credentials():
    """Retrieve Supabase credentials from Streamlit Secrets or defaults."""
    url = None
    key = None
    if hasattr(st, "secrets"):
        try:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass
    if not url:
        url = os.environ.get("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    if not key:
        key = os.environ.get("SUPABASE_KEY", DEFAULT_SUPABASE_KEY)
    return url, key

def get_supabase_client() -> Optional[Any]:
    """Get Supabase client instance if available."""
    if not HAS_SUPABASE_LIB:
        return None
    url, key = get_supabase_credentials()
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

def is_supabase_active() -> bool:
    """Check if Supabase connection is live and tables exist."""
    client = get_supabase_client()
    if client is None:
        return False
    try:
        # Test query employees table
        client.table("employees").select("id").limit(1).execute()
        return True
    except Exception:
        return False

# --- SQLITE LOCAL ENGINE ---

def ensure_directories_exist():
    """Ensure data and backup directories exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def get_sqlite_connection() -> sqlite3.Connection:
    """Get a SQLite database connection."""
    ensure_directories_exist()
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database storage engine (SQLite & Supabase seed check)."""
    ensure_directories_exist()
    
    # 1. Initialize SQLite local tables
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
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
        cursor.execute("SELECT COUNT(*) FROM employees;")
        if cursor.fetchone()[0] == 0:
            for name in DEFAULT_EMPLOYEES:
                cursor.execute("INSERT INTO employees (name, active) VALUES (?, 1);", (name,))
        conn.commit()

    # 2. Check Supabase cloud engine
    if is_supabase_active():
        client = get_supabase_client()
        try:
            res = client.table("employees").select("id").execute()
            if not res.data:
                for name in DEFAULT_EMPLOYEES:
                    client.table("employees").insert({"name": name, "active": 1}).execute()
        except Exception:
            pass

# --- EMPLOYEE OPERATIONS ---

def get_employees(active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieve employees from active database (Supabase or SQLite)."""
    if is_supabase_active():
        try:
            client = get_supabase_client()
            query = client.table("employees").select("id, name, active, created_at").order("name")
            if active_only:
                query = query.eq("active", 1)
            res = query.execute()
            return res.data
        except Exception as e:
            st.warning(f"Supabase error, falling back to local SQLite: {str(e)}")

    # SQLite Fallback
    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        if active_only:
            cursor.execute("SELECT id, name, active, created_at FROM employees WHERE active = 1 ORDER BY name ASC;")
        else:
            cursor.execute("SELECT id, name, active, created_at FROM employees ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

def add_employee(name: str) -> bool:
    """Add a new employee."""
    name_clean = name.strip()
    if not name_clean:
        raise ValueError("Employee name cannot be empty.")
    
    if is_supabase_active():
        try:
            client = get_supabase_client()
            client.table("employees").insert({"name": name_clean, "active": 1}).execute()
            # Also keep local SQLite in sync
            with get_sqlite_connection() as conn:
                conn.execute("INSERT OR IGNORE INTO employees (name, active) VALUES (?, 1);", (name_clean,))
                conn.commit()
            return True
        except Exception as e:
            st.warning(f"Supabase error, using SQLite: {str(e)}")

    with get_sqlite_connection() as conn:
        conn.execute("INSERT INTO employees (name, active) VALUES (?, 1);", (name_clean,))
        conn.commit()
        return True

def update_employee(employee_id: int, name: str, active: int) -> bool:
    """Update employee details."""
    name_clean = name.strip()
    if not name_clean:
        raise ValueError("Employee name cannot be empty.")
        
    if is_supabase_active():
        try:
            client = get_supabase_client()
            client.table("employees").update({"name": name_clean, "active": int(active)}).eq("id", employee_id).execute()
        except Exception as e:
            st.warning(f"Supabase update warning: {str(e)}")

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET name = ?, active = ? WHERE id = ?;", (name_clean, int(active), employee_id))
        conn.commit()
        return cursor.rowcount > 0

# --- TICKET OPERATIONS ---

def ticket_id_exists(ticket_id: str) -> bool:
    """Check if ticket ID exists."""
    if is_supabase_active():
        try:
            client = get_supabase_client()
            res = client.table("tickets").select("id").eq("ticket_id", ticket_id).execute()
            if res.data:
                return True
        except Exception:
            pass

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM tickets WHERE ticket_id = ?;", (ticket_id,))
        return cursor.fetchone() is not None

def add_ticket(ticket_id: str, helped_person: str, issue: str, employee_id: int, resolution: str, created_at: str) -> bool:
    """Insert a new ticket into database."""
    ticket_payload = {
        "ticket_id": ticket_id,
        "created_at": created_at,
        "helped_person": helped_person.strip(),
        "issue": issue.strip(),
        "employee_id": employee_id,
        "resolution": resolution.strip()
    }

    if is_supabase_active():
        try:
            client = get_supabase_client()
            client.table("tickets").insert(ticket_payload).execute()
            # Sync to local SQLite as backup
            with get_sqlite_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tickets (ticket_id, created_at, helped_person, issue, employee_id, resolution)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (ticket_id, created_at, helped_person.strip(), issue.strip(), employee_id, resolution.strip()))
                conn.commit()
            return True
        except Exception as e:
            st.error(f"Supabase Ticket Insert Error: {str(e)}")

    # SQLite Fallback
    with get_sqlite_connection() as conn:
        conn.execute("""
            INSERT INTO tickets (ticket_id, created_at, helped_person, issue, employee_id, resolution)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (ticket_id, created_at, helped_person.strip(), issue.strip(), employee_id, resolution.strip()))
        conn.commit()
        return True

def update_ticket(ticket_id: str, helped_person: str, issue: str, employee_id: int, resolution: str, updated_at: str) -> bool:
    """Update existing ticket details."""
    update_payload = {
        "helped_person": helped_person.strip(),
        "issue": issue.strip(),
        "employee_id": employee_id,
        "resolution": resolution.strip(),
        "updated_at": updated_at
    }

    if is_supabase_active():
        try:
            client = get_supabase_client()
            client.table("tickets").update(update_payload).eq("ticket_id", ticket_id).execute()
        except Exception as e:
            st.warning(f"Supabase update error: {str(e)}")

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets
            SET helped_person = ?, issue = ?, employee_id = ?, resolution = ?, updated_at = ?
            WHERE ticket_id = ?;
        """, (helped_person.strip(), issue.strip(), employee_id, resolution.strip(), updated_at, ticket_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_ticket(ticket_id: str) -> bool:
    """Delete ticket from database."""
    if is_supabase_active():
        try:
            client = get_supabase_client()
            client.table("tickets").delete().eq("ticket_id", ticket_id).execute()
        except Exception as e:
            st.warning(f"Supabase delete error: {str(e)}")

    with get_sqlite_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE ticket_id = ?;", (ticket_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_all_tickets_df() -> pd.DataFrame:
    """Retrieve all tickets formatted as a Pandas DataFrame (newest first)."""
    if is_supabase_active():
        try:
            client = get_supabase_client()
            tickets_res = client.table("tickets").select("*").order("created_at", desc=True).execute()
            emps_res = client.table("employees").select("id, name").execute()
            
            tickets_data = tickets_res.data
            emp_map = {e["id"]: e["name"] for e in emps_res.data} if emps_res.data else {}

            if tickets_data:
                rows = []
                for t in tickets_data:
                    created = str(t.get("created_at", ""))
                    date_part = created[:10] if len(created) >= 10 else created
                    time_part = created[11:19] if len(created) >= 19 else ""
                    rows.append({
                        "Ticket ID": t.get("ticket_id"),
                        "Date": date_part,
                        "Time": time_part,
                        "Who Was Helped": t.get("helped_person"),
                        "Issue": t.get("issue"),
                        "Employee": emp_map.get(t.get("employee_id"), "Unknown"),
                        "Employee ID": t.get("employee_id"),
                        "How It Was Resolved": t.get("resolution"),
                        "Created At": t.get("created_at"),
                        "Updated At": t.get("updated_at")
                    })
                return pd.DataFrame(rows)
            else:
                return pd.DataFrame(columns=[
                    "Ticket ID", "Date", "Time", "Who Was Helped", "Issue", "Employee", 
                    "Employee ID", "How It Was Resolved", "Created At", "Updated At"
                ])
        except Exception as e:
            st.warning(f"Supabase fetch error, using SQLite: {str(e)}")

    # SQLite Fallback
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
    with get_sqlite_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_ticket_by_id(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get single ticket details by ID."""
    df = get_all_tickets_df()
    if not df.empty:
        match = df[df['Ticket ID'] == ticket_id]
        if not match.empty:
            row = match.iloc[0]
            return {
                "ticket_id": row["Ticket ID"],
                "created_at": row["Created At"],
                "updated_at": row["Updated At"],
                "helped_person": row["Who Was Helped"],
                "issue": row["Issue"],
                "employee_id": row["Employee ID"],
                "employee_name": row["Employee"],
                "resolution": row["How It Was Resolved"]
            }
    return None

def create_db_backup() -> str:
    """Create local timestamped SQLite backup."""
    ensure_directories_exist()
    if not os.path.exists(DB_PATH):
        init_db()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"tickets_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path
