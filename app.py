import streamlit as st
import pandas as pd
import plotly.express as px
from backend import get_dashboard_stats, get_recent_forms, trigger_analysis, start_one_time_analysis, get_report_details, get_analysis_status, clear_analysis_status_message
import base64
import time
import streamlit.components.v1 as components
from streamlit_cookies_manager import CookieManager

st.set_page_config(layout="wide")

# Initialize cookie manager
cookies = CookieManager()

# Check login status from cookie
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""

if cookies.ready():
    if cookies.get('logged_in') == 'true':
        st.session_state.logged_in = True
        st.session_state.email = cookies.get('email', '')


def login_page():
    st.markdown("""
        <style>
        div[data-testid="stForm"] {
            max-width: 400px;
            margin: auto;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email/Name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if not email or not password:
                st.error("Email/Name and Password cannot be empty.")
            else:
                # In a real app, you would validate the credentials here
                st.session_state.logged_in = True
                st.session_state.email = email
                cookies['logged_in'] = 'true'
                cookies['email'] = email
                st.rerun()

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def main_page():
    st.sidebar.title("EXLComply360")
    st.sidebar.write(f"Welcome, {st.session_state.email}")
    if st.sidebar.button("Logout ⏻"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        del cookies['logged_in']
        del cookies['email']
        if "selected_report" in st.session_state:
            del st.session_state.selected_report
        st.rerun()
    page = st.sidebar.radio("Go to", ["Dashboard", "Analyze Files"])

    st.markdown("""
        <style>
        div[data-testid="stMetric"] {
            background-color: #f0f8ff; /* Light blue background */
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 10px;
        }
        /* Style for Plotly charts to appear as cards */
        div[data-testid="stPlotlyChart"] {
            background-color: #f0f8ff; /* Light blue background */
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 10px;
        }
        /* General style for all Streamlit buttons (dark green) */
        .stButton button {
            background-color: #1E8449; /* Dark Green background */
            color: white;
            border-radius: 5px;
            border: none;
            padding: 5px 10px;
        }
        /* Specific override for the logout button to be red */
        div[data-testid="stSidebar"] .stButton button {
            background-color: #ff4b4b !important;
            width: 100%;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # Auto-refreshing component
    components.html("<meta http-equiv='refresh' content='5'>", height=0)

    # Status message bar
    status = get_analysis_status()
    if status and status.get("status_message"):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"Background Task Status: {status['status_message']}")
        with col2:
            if st.button("Clear Message"):
                clear_analysis_status_message()
                st.rerun()

    if page == "Dashboard":
        st.title("Compliance Dashboard")

        stats = get_dashboard_stats()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Forms Analyzed", stats["total_forms_analyzed"])
        col2.metric("Average Compliance Score", f'{stats["average_compliance_score"]:.2f}%')
        col3.metric("Total Alerts Raised", stats["total_alerts_raised"])
        st.divider()
        reports = get_recent_forms()
        if reports:
            df = pd.DataFrame(reports)
            
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Analysis Type Distribution")
                analysis_counts = {
                    "Manual": stats.get("manual_analyses_count", 0),
                    "Automatic": stats.get("auto_analyses_count", 0)
                }
                analysis_df = pd.DataFrame(analysis_counts.items(), columns=["Type", "Count"])
                fig = px.pie(analysis_df, names='Type', values='Count', title='Manual vs. Automatic Analyses')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Risk Severity Distribution")
                alert_counts = {"High": 0, "Medium": 0, "Low": 0}
                for rules in df["missing_rules"]:
                    if isinstance(rules, list):
                        for alert in rules:
                            severity = alert.get("risk_level", "Unknown")
                            if severity in alert_counts:
                                alert_counts[severity] += 1
                
                alert_df = pd.DataFrame(list(alert_counts.items()), columns=["Severity", "Count"])
                fig = px.bar(alert_df, x='Severity', y='Count', color='Severity', title='Alerts by Risk Level')
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            col3, col4 = st.columns(2)

            with col3:
                st.subheader("Compliance Score Over Time")
                df['analysis_date'] = pd.to_datetime(df['analysis_date'])
                df_sorted = df.sort_values('analysis_date')
                fig = px.line(df_sorted, x='analysis_date', y='compliance_score', title='Compliance Score Trend', markers=True)
                fig.update_layout(xaxis_title="Analysis Date", yaxis_title="Compliance Score (%)")
                st.plotly_chart(fig, use_container_width=True)

            with col4:
                st.subheader("Alerts by Regulatory Section")
                section_counts = {}
                for rules in df["missing_rules"]:
                    if isinstance(rules, list):
                        for alert in rules:
                            section = alert.get("section", "Uncategorized")
                            section_counts[section] = section_counts.get(section, 0) + 1
                
                section_df = pd.DataFrame(list(section_counts.items()), columns=["Section", "Count"])
                section_df = section_df.sort_values("Count", ascending=True)
                fig = px.bar(section_df, x='Count', y='Section', title='Most Frequent Alert Sections', orientation='h')
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("Analysis Reports")
            manual_data_tab, automatic_data_tab = st.tabs(["Manual Analysis Data", "Automatic Analysis Data"])

            def render_report_list(report_df, report_type):
                if not report_df.empty:
                    for index, row in report_df.iterrows():
                        with st.container():
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.text(f"File: {row['filename']} | Score: {row['compliance_score']:.2f}%")
                            with col_b:
                                if st.button("View Details", key=f"{report_type}_{row['report_id']}"):
                                    st.session_state.selected_report = get_report_details(row['report_id'])
                        st.divider()
                else:
                    st.info(f"No {report_type} analysis reports available.")

            def render_report_details(key_prefix=""):
                st.subheader("Report Details")
                report = st.session_state.selected_report
                st.write(f"**Filename:** {report['filename']}")
                st.write(f"**Analysis Date:** {report['analysis_date']}")
                st.write(f"**Compliance Score:** {report['compliance_score']:.2f}%")
                
                st.write("**Missing Rules Found:**")
                for rule in report.get("missing_rules", []):
                    st.warning(f"**Section:** {rule.get('section', 'N/A')} | **Risk Level:** {rule.get('risk_level', 'N/A')}")
                    st.markdown(f"> {rule.get('requirement', 'No requirement details.')}")

                if st.button("Clear Details", key=f"{key_prefix}_clear_details"):
                    del st.session_state.selected_report
                    st.rerun()

            with manual_data_tab:
                manual_df = df[df["analysis_type"] == "manual"]
                if "selected_report" in st.session_state and st.session_state.selected_report:
                    col_list, col_details = st.columns(2)
                    with col_list:
                        render_report_list(manual_df, "manual")
                    with col_details:
                        render_report_details(key_prefix="manual")
                else:
                    render_report_list(manual_df, "manual")

            with automatic_data_tab:
                automatic_df = df[df["analysis_type"] == "auto"]
                if "selected_report" in st.session_state and st.session_state.selected_report:
                    col_list, col_details = st.columns(2)
                    with col_list:
                        render_report_list(automatic_df, "auto")
                    with col_details:
                        render_report_details(key_prefix="auto")
                else:
                    render_report_list(automatic_df, "auto")

    elif page == "Analyze Files":
        st.title("Analyze PDF Forms")
        
        manual_tab, automatic_tab = st.tabs(["Manual", "Automatic"])

        with manual_tab:
            if st.button("Start Immediate Analysis"):
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Regulation PDF")
                    show_pdf("data/regulations/regulation.pdf")
                with col2:
                    st.subheader("Form PDF")
                    show_pdf("data/forms/form.pdf")
                
                st.subheader("Analysis Progress")
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.05)
                    progress_bar.progress(i + 1)
                
                results = trigger_analysis()
                
                st.subheader("Analysis Results")
                if results and results.get("analysis_results"):
                    result_data = []
                    for res in results["analysis_results"]:
                        for rule in res.get("missing_elements", []):
                            result_data.append({
                                "Section": rule.get("section"),
                                "Requirement": rule.get("requirement"),
                                "Risk Level": rule.get("risk_level")
                            })
                    result_df = pd.DataFrame(result_data)
                    st.dataframe(result_df, use_container_width=True)
                else:
                    st.warning("No analysis results were returned.")

        with automatic_tab:
            st.write("Schedule a one-time analysis to run after a specified delay.")
            delay = st.number_input("Delay in seconds", min_value=1, value=60)
            if st.button("Schedule Analysis"):
                start_one_time_analysis(delay)
                st.success(f"Analysis scheduled to run in {delay} seconds.")

if st.session_state.logged_in:
    main_page()
else:
    login_page()
