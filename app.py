"""
IT Ticket Tracking System - Main Application Entry Point
Built with Streamlit, SQLite, Pandas, and Plotly.
"""

import streamlit as st
import database
import pages.new_ticket as new_ticket_view
import pages.all_tickets as all_tickets_view
import pages.monthly_tickets as monthly_tickets_view
import pages.dashboard as dashboard_view
import pages.employees as employees_view

# Page Config
st.set_page_config(
    page_title="IT Ticket Tracker",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
        /* Modern Header Banner */
        .main-header {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 0.95rem;
            color: #64748B;
            margin-bottom: 1.5rem;
        }
        /* Metric card styling */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            font-weight: 700;
            color: #0F172A;
        }
        /* Buttons styling */
        .stButton>button {
            border-radius: 6px;
            font-weight: 600;
        }
        /* Clean table text wrapping */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    # Initialize SQLite Database & Schema
    try:
        database.init_db()
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        return

    # Render Sidebar Brand
    st.sidebar.markdown("### 🎫 IT Support Desk")
    st.sidebar.caption("Internal Ticket Tracking System")
    st.sidebar.markdown("---")

    # Define Navigation Pages using Streamlit Pages API
    try:
        page_new = st.Page(
            new_ticket_view.render_page,
            title="New Ticket",
            icon="➕",
            default=True
        )
        page_all = st.Page(
            all_tickets_view.render_page,
            title="All Tickets",
            icon="📋"
        )
        page_monthly = st.Page(
            monthly_tickets_view.render_page,
            title="Tickets by Month",
            icon="📅"
        )
        page_dashboard = st.Page(
            dashboard_view.render_page,
            title="Dashboard",
            icon="📊"
        )
        page_employees = st.Page(
            employees_view.render_page,
            title="Employees / Settings",
            icon="⚙️"
        )

        pg = st.navigation(
            {
                "Ticket Management": [page_new, page_all, page_monthly],
                "Analytics & Settings": [page_dashboard, page_employees]
            }
        )
        pg.run()
    except Exception:
        # Fallback to standard sidebar radio if st.navigation encounters unexpected issue
        choice = st.sidebar.radio(
            "Main Menu",
            ["New Ticket", "All Tickets", "Tickets by Month", "Dashboard", "Employees / Settings"],
            index=0
        )
        if choice == "New Ticket":
            new_ticket_view.render_page()
        elif choice == "All Tickets":
            all_tickets_view.render_page()
        elif choice == "Tickets by Month":
            monthly_tickets_view.render_page()
        elif choice == "Dashboard":
            dashboard_view.render_page()
        elif choice == "Employees / Settings":
            employees_view.render_page()

    # Sidebar Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 | Persistent SQLite Storage")

if __name__ == "__main__":
    main()
