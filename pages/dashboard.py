"""
Dashboard Page Module
Provides executive metrics, Plotly visualizations, employee activity analytics, and recent ticket highlights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as gg
from datetime import datetime, date
import database

def render_page():
    st.header("📊 IT Support Dashboard")
    st.caption("Operational statistics and workload analytics for the IT support team.")

    df = database.get_all_tickets_df()

    if df.empty:
        st.info("ℹ️ No tickets recorded yet. High-level dashboard charts will populate once tickets are added.")
        return

    # Parse timestamps for analytics
    df['Date_dt'] = pd.to_datetime(df['Date'], errors='coerce')
    today_date = date.today()
    current_year = today_date.year
    current_month = today_date.month

    # --- METRICS CALCULATIONS ---
    total_tickets = len(df)
    
    tickets_today = len(df[df['Date_dt'].dt.date == today_date])
    
    tickets_this_month = len(df[
        (df['Date_dt'].dt.year == current_year) & 
        (df['Date_dt'].dt.month == current_month)
    ])
    
    active_employees_count = df['Employee'].nunique()

    # Display Top KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="Total Tickets All-Time", value=total_tickets)
    with kpi2:
        st.metric(label="Tickets This Month", value=tickets_this_month)
    with kpi3:
        st.metric(label="Tickets Today", value=tickets_today)
    with kpi4:
        st.metric(label="Active Support Staff", value=active_employees_count)

    st.markdown("---")

    # --- PLOTLY VISUALIZATIONS ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Tickets Handled by Employee")
        emp_counts = df['Employee'].value_counts().reset_index()
        emp_counts.columns = ['Employee', 'Tickets']
        
        fig_emp = px.bar(
            emp_counts,
            x='Tickets',
            y='Employee',
            orientation='h',
            text='Tickets',
            color_discrete_sequence=['#2563EB'],
            labels={'Tickets': 'Number of Tickets', 'Employee': 'Support Staff'}
        )
        fig_emp.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Ticket Count",
            yaxis_title=None,
            height=320,
            showlegend=False
        )
        fig_emp.update_traces(textposition='outside')
        st.plotly_chart(fig_emp, use_container_width=True)

    with chart_col2:
        st.subheader("Tickets by Month (Current Year)")
        df_cy = df[df['Date_dt'].dt.year == current_year].copy()
        if not df_cy.empty:
            df_cy['Month_Name'] = df_cy['Date_dt'].dt.strftime('%b')
            df_cy['Month_Num'] = df_cy['Date_dt'].dt.month
            
            monthly_summary = df_cy.groupby(['Month_Num', 'Month_Name']).size().reset_index(name='Tickets')
            monthly_summary = monthly_summary.sort_values('Month_Num')

            fig_month = px.bar(
                monthly_summary,
                x='Month_Name',
                y='Tickets',
                text='Tickets',
                color_discrete_sequence=['#0D9488'],
                labels={'Month_Name': 'Month', 'Tickets': 'Tickets Handled'}
            )
            fig_month.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title=None,
                yaxis_title="Ticket Count",
                height=320
            )
            fig_month.update_traces(textposition='outside')
            st.plotly_chart(fig_month, use_container_width=True)
        else:
            st.info(f"No ticket data available for calendar year {current_year}.")

    # --- TICKET VOLUME OVER TIME ---
    st.subheader("Ticket Volume Over Time (Daily)")
    daily_counts = df.groupby(df['Date_dt'].dt.date).size().reset_index(name='Ticket Count')
    daily_counts.columns = ['Date', 'Ticket Count']
    daily_counts = daily_counts.sort_values('Date')

    fig_time = px.area(
        daily_counts,
        x='Date',
        y='Ticket Count',
        markers=True,
        color_discrete_sequence=['#4F46E5'],
        title=None
    )
    fig_time.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Date",
        yaxis_title="Daily Tickets",
        height=300
    )
    st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # --- SUMMARY TABLES ---
    sum_col1, sum_col2 = st.columns([1, 2])

    with sum_col1:
        st.subheader("🏆 Most Active Employees")
        emp_summary = df['Employee'].value_counts().reset_index()
        emp_summary.columns = ['Employee', 'Total Tickets']
        emp_summary['Share %'] = (emp_summary['Total Tickets'] / total_tickets * 100).round(1).astype(str) + '%'
        st.dataframe(emp_summary, use_container_width=True, hide_index=True)

    with sum_col2:
        st.subheader("⏱️ Recent Tickets")
        recent_cols = ["Ticket ID", "Date", "Who Was Helped", "Employee", "Issue"]
        st.dataframe(
            df[recent_cols].head(5),
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    render_page()
