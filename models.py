"""
Models and Validation Logic for IT Ticket Tracking System
Includes unique Ticket ID generation and form input validation rules.
"""

import random
import string
from datetime import datetime
from typing import Tuple
import database

def generate_ticket_id() -> str:
    """
    Generate a safe, unique Ticket ID in the format TK-YYYYMMDD-XXXX.
    Ensures no collision with existing Ticket IDs in the database.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    
    while True:
        # Generate 4-character random uppercase alphanumeric code
        rand_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        ticket_id = f"TK-{date_str}-{rand_code}"
        
        # Verify collision avoidance in SQLite
        if not database.ticket_id_exists(ticket_id):
            return ticket_id

def validate_ticket_input(helped_person: str, issue: str, employee_id: int, resolution: str) -> Tuple[bool, str]:
    """
    Validate ticket submission inputs.
    Returns (is_valid: bool, error_message: str).
    """
    if not helped_person or not helped_person.strip():
        return False, "'Who Was Helped' field is required."
    
    if not issue or not issue.strip():
        return False, "'Issue' field is required."
        
    if not employee_id:
        return False, "Please select the 'Employee Who Helped'."
        
    if not resolution or not resolution.strip():
        return False, "'How It Was Resolved' field is required."
        
    return True, ""
