"""
Tickets by Month Page Module
Recreates the Excel monthly sheet workflow dynamically by filtering the unified normalized tickets table.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database
import utils

def render_page():
    st.header("📅 Tickets by Month")
    st.caption("Dynamic monthly breakdown replacing separate monthly Excel sheets.")

    df = database.get_all_tickets_df()

    if df.empty:
        st.info("ℹ️ No tickets have been recorded yet. Navigate to 'New Ticket' to log support requests.")
        return

    # Extract available years and months
    years = utils.get_year_range(df)
    current_year = datetime.now().year
    current_month_idx = datetime.now().month - 1  # 0-indexed

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Select Year", options=years, index=0 if current_year in years else 0)
    with col2:
        selected_month_name = st.selectbox("Select Month", options=utils.MONTH_NAMES, index=current_month_idx)

    selected_month_num = utils.MONTH_NAMES.index(selected_month_name) + 1

    # Filter dataframe for selected year and month
    df['Date_dt'] = pd.to_datetime(df['Date'], errors='coerce')
    monthly_df = df[
        (df['Date_dt'].dt.year == selected_year) & 
        (df['Date_dt'].dt.month == selected_month_num)
    ].copy()
    
    if 'Date_dt' in monthly_df.columns:
        monthly_df = monthly_df.drop(columns=['Date_dt'])

    st.markdown("---")

    # Display prominent monthly total ticket count metric card
    m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
    with m_col1:
        st.metric(
            label=f"Total Tickets ({selected_month_name} {selected_year})",
            value=len(monthly_df),
            help=f"Total number of support tickets recorded in {selected_month_name} {selected_year}."
        )

    # Display monthly tickets table
    if monthly_df.empty:
        st.info(f"No tickets logged for **{selected_month_name} {selected_year}**.")
    else:
        display_cols = [
            "Ticket ID", "Date", "Time", "Who Was Helped", "Issue", "Employee", "How It Was Resolved"
        ]
        
        st.dataframe(
            monthly_df[display_cols],
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

        # Monthly Export Options
        st.markdown("##### Export Monthly Report")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_data = utils.export_to_csv(monthly_df[display_cols])
            st.download_button(
                label=f"📄 Download {selected_month_name} {selected_year} CSV",
                data=csv_data,
                file_name=f"tickets_{selected_month_name}_{selected_year}.csv",
                mime="text/csv"
            )
        with col_exp2:
            excel_data = utils.export_to_excel(monthly_df[display_cols])
            st.download_button(
                label=f"📊 Download {selected_month_name} {selected_year} Excel",
                data=excel_data,
                file_name=f"tickets_{selected_month_name}_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    render_page()
