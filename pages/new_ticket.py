"""
New Ticket Page Module
Optimized for rapid data entry with form validation, automatic timestamping, and unique Ticket ID generation.
"""

import streamlit as st
from datetime import datetime
import database
import models

def render_page():
    st.header("➕ Create New IT Ticket")
    st.caption("Fast ticket entry system replacing manual Excel workbook logs.")

    # Fetch active employees from DB
    employees = database.get_employees(active_only=True)
    
    if not employees:
        st.warning("⚠️ No active employees found in the system. Please add or activate employees in the Employees/Settings page before creating tickets.")
        return

    employee_options = {emp['name']: emp['id'] for emp in employees}

    # Initialize form state variables if not present
    if "helped_person" not in st.session_state:
        st.session_state.helped_person = ""
    if "issue" not in st.session_state:
        st.session_state.issue = ""
    if "resolution" not in st.session_state:
        st.session_state.resolution = ""
    if "selected_emp_name" not in st.session_state or st.session_state.selected_emp_name not in employee_options:
        st.session_state.selected_emp_name = list(employee_options.keys())[0]

    # Show recent submission notification if stored in session state
    if "last_created_ticket" in st.session_state:
        ticket_info = st.session_state.last_created_ticket
        st.success(
            f"🎉 **Ticket Successfully Added!**\n\n"
            f"**Ticket ID:** `{ticket_info['id']}` | **Created:** `{ticket_info['created_at']}` | **Helped:** `{ticket_info['helped_person']}`"
        )
        # Clear notification on next action
        del st.session_state.last_created_ticket

    st.markdown("---")

    with st.form(key="new_ticket_form", clear_on_submit=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            helped_person_input = st.text_input(
                "Who Was Helped *",
                value=st.session_state.helped_person,
                placeholder="e.g. Jane Smith (Sales)",
                help="Name and department/role of the person who requested support."
            )
            
        with col2:
            emp_names = list(employee_options.keys())
            emp_index = emp_names.index(st.session_state.selected_emp_name) if st.session_state.selected_emp_name in emp_names else 0
            selected_emp_name_input = st.selectbox(
                "Employee Who Helped *",
                options=emp_names,
                index=emp_index,
                help="Select the IT support team member who resolved this ticket."
            )

        issue_input = st.text_area(
            "Issue Description *",
            value=st.session_state.issue,
            height=120,
            placeholder="e.g. Outlook crashing on startup after OS update. User unable to send emails.",
            help="Provide a clear description of the reported problem."
        )

        resolution_input = st.text_area(
            "How It Was Resolved *",
            value=st.session_state.resolution,
            height=120,
            placeholder="e.g. Rebuilt Outlook profile, cleared app cache, and restarted service. Verified mail flow working.",
            help="Provide details on how the issue was resolved."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.form_submit_button(label="🚀 Add Ticket", type="primary", use_container_width=True)

    if submit_button:
        # Form Validation
        emp_id = employee_options[selected_emp_name_input]
        is_valid, err_msg = models.validate_ticket_input(
            helped_person_input,
            issue_input,
            emp_id,
            resolution_input
        )

        if not is_valid:
            st.error(f"❌ Validation Error: {err_msg}")
        else:
            try:
                # Capture exact current local timestamp
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Generate safe unique Ticket ID
                ticket_id = models.generate_ticket_id()
                
                # Save to database
                database.add_ticket(
                    ticket_id=ticket_id,
                    helped_person=helped_person_input.strip(),
                    issue=issue_input.strip(),
                    employee_id=emp_id,
                    resolution=resolution_input.strip(),
                    created_at=now_str
                )
                
                # Store success info in session state
                st.session_state.last_created_ticket = {
                    "id": ticket_id,
                    "created_at": now_str,
                    "helped_person": helped_person_input.strip()
                }
                
                # Reset form session state values
                st.session_state.helped_person = ""
                st.session_state.issue = ""
                st.session_state.resolution = ""
                
                st.rerun()

            except Exception as e:
                st.error(f"❌ Database error while saving ticket: {str(e)}")

if __name__ == "__main__":
    render_page()
