"""
Employees & Settings Page Module
Manages support staff accounts (Add, Edit, Deactivate/Reactivate) and SQLite database backup utilities.
"""

import os
import streamlit as st
import pandas as pd
import database

def render_page():
    st.header("⚙️ Employees & System Settings")
    st.caption("Manage IT support team members and perform database maintenance.")

    tab_emps, tab_backup = st.tabs(["👥 Employee Management", "💾 Database & Backups"])

    # TAB 1: EMPLOYEE MANAGEMENT
    with tab_emps:
        st.subheader("Support Team Members")
        st.markdown(
            "Add, edit, or deactivate support staff. **Deactivated staff members** remain linked to historical tickets "
            "and statistics, but will be excluded from the selection dropdown when entering new tickets."
        )

        employees = database.get_employees(active_only=False)
        tickets_df = database.get_all_tickets_df()

        # Compute ticket counts per employee
        emp_ticket_counts = {}
        if not tickets_df.empty:
            emp_ticket_counts = tickets_df['Employee'].value_counts().to_dict()

        # Display Employee Roster
        emp_table_data = []
        for emp in employees:
            emp_table_data.append({
                "ID": emp['id'],
                "Name": emp['name'],
                "Status": "Active 🟢" if emp['active'] else "Inactive 🔴",
                "Tickets Handled": emp_ticket_counts.get(emp['name'], 0),
                "Added On": emp['created_at']
            })

        emp_df = pd.DataFrame(emp_table_data)
        st.dataframe(emp_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        col_add, col_edit = st.columns(2)

        # ADD EMPLOYEE
        with col_add:
            st.markdown("##### ➕ Add New Employee")
            with st.form(key="add_employee_form", clear_on_submit=True):
                new_emp_name = st.text_input("Employee Name *", placeholder="e.g. John Doe")
                add_submit = st.form_submit_button("Add Team Member", type="primary")

                if add_submit:
                    if not new_emp_name.strip():
                        st.error("❌ Employee name cannot be blank.")
                    else:
                        try:
                            database.add_employee(new_emp_name.strip())
                            st.success(f"✅ Employee **{new_emp_name.strip()}** added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error adding employee (may already exist): {str(e)}")

        # EDIT / DEACTIVATE EMPLOYEE
        with col_edit:
            st.markdown("##### ✏️ Edit or Deactivate Employee")
            if employees:
                emp_options = {emp['name']: emp for emp in employees}
                selected_name = st.selectbox("Select Employee to Modify", options=list(emp_options.keys()))
                target_emp = emp_options[selected_name]

                with st.form(key="edit_employee_form"):
                    edit_name = st.text_input("Employee Name", value=target_emp['name'])
                    is_active = st.checkbox("Active Account", value=bool(target_emp['active']), help="Uncheck to deactivate staff member.")

                    save_emp_submit = st.form_submit_button("Save Employee Changes")

                    if save_emp_submit:
                        if not edit_name.strip():
                            st.error("❌ Employee name cannot be blank.")
                        else:
                            try:
                                database.update_employee(
                                    employee_id=target_emp['id'],
                                    name=edit_name.strip(),
                                    active=1 if is_active else 0
                                )
                                st.success(f"✅ Updated **{edit_name.strip()}** status successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error updating employee: {str(e)}")

    # TAB 2: DATABASE BACKUPS
    with tab_backup:
        st.subheader("Database Backup & Safety")
        st.markdown(
            "SQLite database is stored locally at `data/tickets.db`. "
            "Use the controls below to generate timestamped backup files or download a direct copy."
        )

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("##### 📦 Create Local Backup")
            if st.button("🚀 Create Timestamped DB Backup"):
                try:
                    backup_path = database.create_db_backup()
                    st.success(f"✅ Backup created successfully at:\n`{backup_path}`")
                except Exception as e:
                    st.error(f"❌ Backup failed: {str(e)}")

        with col_b2:
            st.markdown("##### ⬇️ Download Database File")
            db_file_path = database.DB_PATH
            if os.path.exists(db_file_path):
                with open(db_file_path, "rb") as f:
                    db_bytes = f.read()
                
                st.download_button(
                    label="📥 Download tickets.db",
                    data=db_bytes,
                    file_name="tickets.db",
                    mime="application/x-sqlite3"
                )
            else:
                st.warning("Database file not initialized yet.")

if __name__ == "__main__":
    render_page()
