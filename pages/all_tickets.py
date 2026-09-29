"""
All Tickets Page Module
Provides searchable, filterable table view of tickets with editing, deletion confirmation, and CSV/Excel exports.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import database
import models
import utils

def render_page():
    st.header("📋 All IT Tickets")
    st.caption("Search, filter, edit, or export historical support tickets.")

    # Load tickets DataFrame
    df = database.get_all_tickets_df()

    if df.empty:
        st.info("ℹ️ No tickets have been recorded yet. Navigate to the 'New Ticket' page to create one.")
        return

    # Load all employees (active + inactive for historical filtering)
    employees = database.get_employees(active_only=False)
    emp_map = {emp['name']: emp['id'] for emp in employees}
    emp_names_list = ["All Employees"] + sorted(list(emp_map.keys()))

    # --- FILTER SECTION ---
    with st.expander("🔍 Filter & Search Controls", expanded=True):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        # Date filter setup
        min_db_date = pd.to_datetime(df['Date']).min().date() if not df.empty else date.today()
        max_db_date = pd.to_datetime(df['Date']).max().date() if not df.empty else date.today()

        with col1:
            date_range = st.date_input(
                "Date Range",
                value=(min_db_date, max_db_date),
                min_value=min_db_date,
                max_value=max_db_date,
                key="filter_date_range"
            )

        with col2:
            selected_emp = st.selectbox(
                "Filter by Employee",
                options=emp_names_list,
                key="filter_employee"
            )

        with col3:
            search_person = st.text_input(
                "Person Helped",
                placeholder="Search recipient...",
                key="filter_person"
            )

        with col4:
            search_keyword = st.text_input(
                "Keyword Search",
                placeholder="Search issue / resolution...",
                key="filter_keyword"
            )

        col_clear, _ = st.columns([1, 4])
        with col_clear:
            if st.button("🔄 Clear Filters"):
                st.session_state.filter_date_range = (min_db_date, max_db_date)
                st.session_state.filter_employee = "All Employees"
                st.session_state.filter_person = ""
                st.session_state.filter_keyword = ""
                st.rerun()

    # Apply Filters
    filtered_df = df.copy()

    # 1. Date Range Filter
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df['Date_dt'] = pd.to_datetime(filtered_df['Date']).dt.date
        filtered_df = filtered_df[(filtered_df['Date_dt'] >= start_d) & (filtered_df['Date_dt'] <= end_d)]
        filtered_df = filtered_df.drop(columns=['Date_dt'])

    # 2. Employee Filter
    if selected_emp != "All Employees":
        filtered_df = filtered_df[filtered_df['Employee'] == selected_emp]

    # 3. Person Helped Filter
    if search_person.strip():
        filtered_df = filtered_df[filtered_df['Who Was Helped'].str.contains(search_person.strip(), case=False, na=False)]

    # 4. Keyword Search (Issue & Resolution)
    if search_keyword.strip():
        kw = search_keyword.strip()
        issue_match = filtered_df['Issue'].str.contains(kw, case=False, na=False)
        res_match = filtered_df['How It Was Resolved'].str.contains(kw, case=False, na=False)
        filtered_df = filtered_df[issue_match | res_match]

    st.markdown(f"**Displaying {len(filtered_df)} of {len(df)} total tickets**")

    # --- MAIN TABLE DISPLAY ---
    # Prepare display columns
    display_cols = [
        "Ticket ID", "Date", "Time", "Who Was Helped", "Issue", "Employee", "How It Was Resolved"
    ]
    if "Updated At" in filtered_df.columns and filtered_df["Updated At"].notna().any():
        display_cols.append("Updated At")

    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticket ID": st.column_config.TextColumn("Ticket ID", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Time": st.column_config.TextColumn("Time", width="small"),
            "Who Was Helped": st.column_config.TextColumn("Who Was Helped", width="medium"),
            "Issue": st.column_config.TextColumn("Issue", width="large"),
            "Employee": st.column_config.TextColumn("Employee", width="medium"),
            "How It Was Resolved": st.column_config.TextColumn("How It Was Resolved", width="large"),
        }
    )

    st.markdown("---")

    # --- ACTIONS: EXPORT & EDIT & DELETE ---
    action_tab1, action_tab2, action_tab3 = st.tabs(["📥 Export Data", "✏️ Edit Ticket", "🗑️ Delete Ticket"])

    # TAB 1: EXPORTS
    with action_tab1:
        st.subheader("Export Options")
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            st.markdown("##### Current Filtered Tickets")
            csv_data_filtered = utils.export_to_csv(filtered_df[display_cols])
            excel_data_filtered = utils.export_to_excel(filtered_df[display_cols])

            st.download_button(
                label="📄 Export Filtered to CSV",
                data=csv_data_filtered,
                file_name=f"tickets_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.download_button(
                label="📊 Export Filtered to Excel (.xlsx)",
                data=excel_data_filtered,
                file_name=f"tickets_filtered_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_exp2:
            st.markdown("##### All Tickets System Export")
            csv_data_all = utils.export_to_csv(df[display_cols])
            excel_data_all = utils.export_to_excel(df[display_cols])

            st.download_button(
                label="📄 Export ALL Tickets to CSV",
                data=csv_data_all,
                file_name=f"all_tickets_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            st.download_button(
                label="📊 Export ALL Tickets to Excel (.xlsx)",
                data=excel_data_all,
                file_name=f"all_tickets_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # TAB 2: EDIT TICKET
    with action_tab2:
        st.subheader("Edit Ticket Details")
        all_ticket_ids = df['Ticket ID'].tolist()
        
        selected_edit_id = st.selectbox("Select Ticket ID to Edit", options=all_ticket_ids, key="edit_ticket_select")
        
        ticket_data = database.get_ticket_by_id(selected_edit_id)
        if ticket_data:
            st.caption(f"Created on: {ticket_data['created_at']} | Original Ticket ID: {ticket_data['ticket_id']}")
            
            # Active & current employee list for edit dropdown
            active_emps = database.get_employees(active_only=True)
            active_emp_map = {e['name']: e['id'] for e in active_emps}
            # Include current ticket employee if inactive so it displays properly
            if ticket_data['employee_name'] not in active_emp_map:
                active_emp_map[ticket_data['employee_name']] = ticket_data['employee_id']

            edit_emp_names = sorted(list(active_emp_map.keys()))
            current_emp_idx = edit_emp_names.index(ticket_data['employee_name']) if ticket_data['employee_name'] in edit_emp_names else 0

            with st.form(key="edit_ticket_form"):
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    edit_helped = st.text_input("Who Was Helped", value=ticket_data['helped_person'])
                with ecol2:
                    edit_emp_name = st.selectbox("Employee Who Helped", options=edit_emp_names, index=current_emp_idx)
                
                edit_issue = st.text_area("Issue Description", value=ticket_data['issue'], height=100)
                edit_resolution = st.text_area("How It Was Resolved", value=ticket_data['resolution'], height=100)

                submit_edit = st.form_submit_button("💾 Save Ticket Changes", type="primary")

                if submit_edit:
                    is_valid, err_msg = models.validate_ticket_input(
                        edit_helped, edit_issue, active_emp_map[edit_emp_name], edit_resolution
                    )
                    if not is_valid:
                        st.error(f"❌ Cannot save: {err_msg}")
                    else:
                        update_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        database.update_ticket(
                            ticket_id=selected_edit_id,
                            helped_person=edit_helped,
                            issue=edit_issue,
                            employee_id=active_emp_map[edit_emp_name],
                            resolution=edit_resolution,
                            updated_at=update_ts
                        )
                        st.success(f"✅ Ticket **{selected_edit_id}** updated successfully!")
                        st.rerun()

    # TAB 3: DELETE TICKET
    with action_tab3:
        st.subheader("Delete Ticket")
        st.warning("⚠️ Deleting a ticket is permanent and cannot be undone.")
        
        del_ticket_id = st.selectbox("Select Ticket ID to Delete", options=all_ticket_ids, key="delete_ticket_select")
        
        confirm_check = st.checkbox(f"I confirm I want to permanently delete ticket **{del_ticket_id}**")
        
        if st.button("🗑️ Permanently Delete Ticket", type="primary", disabled=not confirm_check):
            if database.delete_ticket(del_ticket_id):
                st.success(f"✅ Ticket **{del_ticket_id}** has been deleted.")
                st.rerun()
            else:
                st.error("❌ Failed to delete ticket.")

if __name__ == "__main__":
    render_page()
