# File: auth.py

import streamlit as st
import time

def check_password():
    """Returns `True` if the user is logged in or successfully logs in."""
    
    # Check if the user is already logged in
    if "logged_in" in st.session_state and st.session_state.logged_in:
        # Check if the session has expired (e.g., after 12 hours)
        if time.time() - st.session_state.login_time < 12 * 3600:
            return True
        else:
            # Session expired, clear the session state
            st.session_state.clear()
    
    # If not logged in, show the login form
    placeholder = st.empty()
    with placeholder.form("login"):
        st.markdown("#### Enter your credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if (username in st.secrets["passwords"] and
                password == st.secrets["passwords"][username]):
            st.session_state.logged_in = True
            st.session_state.login_time = time.time()
            placeholder.empty()
            st.success("Login successful!")
            return True
        else:
            st.error("Invalid username or password")
    
    return False

# File: main.py

import streamlit as st
from auth import check_password

def main():
    st.set_page_config(page_title="The Us House - Dashboard", layout="wide")

    if check_password():
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center;">
            <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="width: 150px; margin-right: 20px;">
            <h1 class="main-title">The Us House Dashboard</h1>
        </div>
        """, unsafe_allow_html=True)

        import streamlit as st
        import pandas as pd
        from datetime import datetime, timedelta
        from google.oauth2.service_account import Credentials
        import gspread
        
        # Set page config at the very beginning
        st.set_page_config(layout="wide", page_title="Student Visa CRM Dashboard")
        
        
        # Use Streamlit secrets for service account info
        SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
        
        # Define the scopes
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        
        # Authenticate and build the Google Sheets service
        @st.cache_resource
        def get_google_sheet_client():
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
            return gspread.authorize(creds)
        
        # Function to load data from Google Sheets
        def load_data(spreadsheet_id, sheet_name):
            client = get_google_sheet_client()
            sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            return df
        
        # Load data
        spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
        sheet_name = "ALL"
        data = load_data(spreadsheet_id, sheet_name)
        
        # Convert DATE columns to datetime with explicit format
        date_format = "%d/%m/%Y %H:%M:%S"
        data['DATE'] = pd.to_datetime(data['DATE'], format=date_format, errors='coerce')
        data['School Entry Date'] = pd.to_datetime(data['School Entry Date'], format=date_format, errors='coerce')
        data['EMBASSY ITW. DATE'] = pd.to_datetime(data['EMBASSY ITW. DATE'], format=date_format, errors='coerce')
        
        # Get today's date
        today = datetime.now()
        
        # Apply rules (as in your original code)
        # Rule 1: School payment 50 days before school entry, exclude students with Visa Denied
        data['School Payment Due'] = data['School Entry Date'] - timedelta(days=50)
        rule_1 = data[(data['School Paid'] != 'Yes') & (data['School Payment Due'] > today) & (data['Visa Result'] != 'Visa Denied')].sort_values(by='DATE').reset_index(drop=True)
        
        # Rule 2: DS-160 step within 30 days before embassy interview
        ds_160_stages = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep', 'CLIENTS']
        data['DS-160 Due'] = data['EMBASSY ITW. DATE'] - timedelta(days=30)
        rule_2 = data[(data['Stage'].isin(ds_160_stages[:5])) & (data['EMBASSY ITW. DATE'] > today) & (data['EMBASSY ITW. DATE'] <= today + timedelta(days=30))].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)
        
        # Rule 3: Embassy interview in less than 14 days and stage is not CLIENT or SEVIS payment is NO
        rule_3a = data[(data['EMBASSY ITW. DATE'] > today) & (data['EMBASSY ITW. DATE'] <= today + timedelta(days=14)) & (data['Stage'] != 'CLIENT') & (data['Stage'] != 'CLIENTS')].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)
        rule_3b = data[(data['EMBASSY ITW. DATE'] > today) & (data['EMBASSY ITW. DATE'] <= today + timedelta(days=14)) & (data['Sevis payment ?'] == 'NO')].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)
        
        # Rule 4: One week after DATE and School Entry Date is still empty, exclude clients with stage 'CLIENTS'
        rule_4 = data[(data['DATE'] <= today - timedelta(days=7)) & (data['School Entry Date'].isna()) & (data['Stage'] != 'CLIENTS')].sort_values(by='DATE').reset_index(drop=True)
        
        # Rule 5: Two weeks after DATE and EMBASSY ITW. DATE is still empty, exclude clients with stage 'CLIENTS'
        rule_5 = data[(data['DATE'] <= today - timedelta(days=14)) & (data['EMBASSY ITW. DATE'].isna()) & (data['Stage'] != 'CLIENTS')].sort_values(by='DATE').reset_index(drop=True)
        
        # New Rule: EMBASSY ITW. DATE is passed today and Visa Result is empty
        rule_6 = data[(data['EMBASSY ITW. DATE'] < today) & (data['Visa Result'].isna())].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)
        
        
        
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
            
            html {
                font-size: 13.6px; /* Base font size set to 85% of 16px */
            }
            
            body {
                zoom: 0.85;
                -moz-transform: scale(0.85);
                -moz-transform-origin: 0 0;
            }
            
            .stApp {
                background-color: #f0f4f8;
            }
            
            h1 { font-size: 2.6rem; }
            h2 { font-size: 2.1rem; }
            h3 { font-size: 1.8rem; }
            h4 { font-size: 1.6rem; }
            h5 { font-size: 1.3rem; }
            h6 { font-size: 1.1rem; }
            
            .stTabs {
                background-color: #ffffff;
                border-radius: 9px;
                box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
                padding: 17px;
                margin-top: 30px; /* Added space above the tabs */
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 9px;
            }
            
            .stTabs [data-baseweb="tab"] {
                border-radius: 25px;
                padding: 9px 17px;
                font-size: 0.95rem;
            }
            
            .metric-card {
                background-color: #ffffff;
                border-radius: 9px;
                box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
                padding: 17px;
            }
            
            .metric-value {
                font-size: 2.2rem;
            }
            
            .metric-label {
                font-size: 0.95rem;
                margin-top: 5px;
            }
            
            .dataframe {
                font-size: 0.85rem;
            }
            
            .dataframe th, .dataframe td {
                padding: 10px;
            }
            
            .section-header {
                font-size: 1.4rem;
                margin: 17px 0;
                padding-bottom: 9px;
            }
            
            /* Adjust Streamlit's default elements */
            .stButton > button {
                font-size: 0.95rem;
            }
            
            .stSelectbox > div > div {
                font-size: 0.95rem;
            }
            
            .stTextInput > div > div > input {
                font-size: 0.95rem;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Title and introduction
        st.title("📊 Student Visa CRM Dashboard")
        st.markdown("Welcome to the modern and user-friendly Student Visa CRM Dashboard. Here you can track and manage various stages of the student visa process.")
        
        # Function to create a metric card
        def metric_card(label, value, icon):
            return f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{icon} {label}</div>
            </div>
            """
        
        # Overview metrics
        st.markdown("## Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(metric_card("School Payment Due", len(rule_1), "📅"), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card("DS-160 Due", len(rule_2), "📝"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("Upcoming Interviews", len(rule_3a), "🎤"), unsafe_allow_html=True)
        with col4:
            st.markdown(metric_card("Need SEVIS Payment", len(rule_3b), "💳"), unsafe_allow_html=True)
        
        # Add some space before the tabs
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Detailed sections in tabs with emojis
        tabs = st.tabs([
            "📅 School Payment",
            "📝 DS-160",
            "🎤 Interviews",
            "💳 SEVIS Payment",
            "📄 I-20 & Registration",
            "📆 ITW Date",
            "🔍 Visa Result"
        ])
        
        with tabs[0]:
            st.markdown('<div class="section-header">📅 School Payment Due Soon</div>', unsafe_allow_html=True)
            st.write("These students need to complete their school payment at least 50 days before their school entry date.")
            st.dataframe(rule_1[['First Name', 'Last Name', 'DATE', 'School Payment Due', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[1]:
            st.markdown('<div class="section-header">📝 DS-160 Step Due Soon</div>', unsafe_allow_html=True)
            st.write("These students need to complete the DS-160 step within 30 days before their embassy interview date.")
            st.dataframe(rule_2[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[2]:
            st.markdown('<div class="section-header">🎤 Upcoming Embassy Interviews (Need Prep)</div>', unsafe_allow_html=True)
            st.write("These students have embassy interviews scheduled within the next 14 days and they are not prepared yet.")
            st.dataframe(rule_3a[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[3]:
            st.markdown('<div class="section-header">💳 Need SEVIS Payment</div>', unsafe_allow_html=True)
            st.write("These students have embassy interviews scheduled within the next 14 days and they did not pay the SEVIS.")
            st.dataframe(rule_3b[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[4]:
            st.markdown('<div class="section-header">📄 I-20 and School Registration Needed</div>', unsafe_allow_html=True)
            st.write("These students do not have a school entry date recorded one week after the Payment date. They need an I-20 and must mention their entry date in the database.")
            st.dataframe(rule_4[['First Name', 'Last Name', 'DATE', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[5]:
            st.markdown('<div class="section-header">📆 ITW Date Needed</div>', unsafe_allow_html=True)
            st.write("These students do not have an embassy interview date recorded two weeks after their initial registration date. They need to schedule their interview and update the database.")
            st.dataframe(rule_5[['First Name', 'Last Name', 'DATE', 'Stage', 'Agent']], use_container_width=True)
        
        with tabs[6]:
            st.markdown('<div class="section-header">🔍 Visa Result Needed</div>', unsafe_allow_html=True)
            st.write("These students have passed their embassy interview date and still do not have a recorded visa result. Please update their visa result.")
            st.dataframe(rule_6[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)
        
        # Add a footer
        st.markdown("---")
        st.markdown("© 2023 Student Visa CRM Dashboard. All rights reserved.")

if __name__ == "__main__":
    main()

# File: 📊Statistics.py

import streamlit as st
from auth import check_password

def statistics_page():
    if check_password():
        st.title("Statistics Page")
        import pandas as pd
        import plotly.express as px
        from google.oauth2.service_account import Credentials
        import gspread
        import streamlit as st
        from datetime import datetime
        
        # Use Streamlit secrets for service account info
        SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
        
        # Define the scopes
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        
        # Authenticate and build the Google Sheets service
        @st.cache_resource
        def get_google_sheet_client():
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
            return gspread.authorize(creds)
        
        # Function to load data from Google Sheets
        def load_data(spreadsheet_id, sheet_name):
            client = get_google_sheet_client()
            sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            return df
        
        def filter_data_by_date_range(data, start_date, end_date):
            return data[(data['DATE'] >= start_date) & (data['DATE'] <= end_date)]
        
        def filter_data_by_month_year(data, year, month):
            start_date = pd.Timestamp(year=year, month=month, day=1)
            end_date = start_date + pd.offsets.MonthEnd(1)
            return data[(data['DATE'] >= start_date) & (data['DATE'] <= end_date)]
        
        def calculate_visa_approval_rate(data):
            # Filter for applications where a decision has been made
            decided_applications = data[data['Visa Result'].isin(['Visa Approved', 'Visa Denied'])]
            
            # Calculate total decided applications
            total_decided = len(decided_applications)
            
            # Calculate number of approved visas
            approved_visas = len(decided_applications[decided_applications['Visa Result'] == 'Visa Approved'])
            
            # Calculate approval rate
            approval_rate = (approved_visas / total_decided * 100) if total_decided > 0 else 0
            
            return approval_rate, approved_visas, total_decided
        
        def statistics_page():
            st.set_page_config(page_title="Student Recruitment Statistics", layout="wide")
            
            st.markdown("""
            <style>
                .reportview-container {
                    background: #f0f2f6;
                }
                .main .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
                h1, h2, h3 {
                    color: #1E3A8A;
                    font-size: 1.2rem; /* Adjust font size */
                }
                .stMetric {
                    background-color: #ffffff;
                    border-radius: 5px;
                    padding: 10px; /* Adjust padding */
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    font-size: 0.8rem; /* Adjust font size */
                }
                .stMarkdown {
                    font-size: 0.8rem; /* Adjust font size */
                }
            </style>
            """, unsafe_allow_html=True)
        
            st.title("📊 Student Recruitment Statistics")
        
            # Load data from Google Sheets
            spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
            sheet_name = "ALL"
            data = load_data(spreadsheet_id, sheet_name)
        
            # Convert 'DATE' column to datetime and handle NaT values
            data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
        
            # Identify rows with incorrect date format in the original data
            incorrect_date_mask = data['DATE'].isna()
            incorrect_date_count = incorrect_date_mask.sum()
            
            # Create a DataFrame with students having incorrect date format
            students_with_incorrect_dates = data[incorrect_date_mask]
        
            # Remove duplicates for analysis
            data_deduped = data.drop_duplicates(subset=['Student Name', 'Chosen School'], keep='last')
            
            # Remove rows with NaT values in the DATE column for further analysis
            data_clean = data_deduped.dropna(subset=['DATE'])
        
            min_date = data_clean['DATE'].min()
            max_date = data_clean['DATE'].max()
            years = list(range(min_date.year, max_date.year + 1))
            months = list(range(1, 13))
        
            # Filter selection
            st.sidebar.subheader("Filter Options")
            filter_option = st.sidebar.radio("Select Filter Method", ("Date Range", "Month and Year"))
        
            min_date = min_date.to_pydatetime() if not pd.isna(min_date) else datetime(2022, 1, 1)
            max_date = max_date.to_pydatetime() if not pd.isna(max_date) else datetime(2022, 12, 31)
        
            if filter_option == "Date Range":
                start_date = st.sidebar.date_input("Start Date", min_date)
                end_date = st.sidebar.date_input("End Date", max_date)
                
                # Convert date inputs to pandas Timestamp objects
                start_date = pd.Timestamp(start_date)
                end_date = pd.Timestamp(end_date)
                
                filtered_data = filter_data_by_date_range(data_clean, start_date, end_date)
            else:
                selected_year = st.sidebar.selectbox("Year", years)
                selected_month = st.sidebar.selectbox("Month", months, format_func=lambda x: datetime(2023, x, 1).strftime('%B'))
                filtered_data = filter_data_by_month_year(data_clean, selected_year, selected_month)
        
            # Calculate overall visa approval rate
            overall_approval_rate, visa_approved, total_decisions = calculate_visa_approval_rate(filtered_data)
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                total_students = len(filtered_data)
                st.metric("Total Unique Students", total_students)
        
            with col2:
                st.metric("Visa Approvals", visa_approved)
        
            with col3:
                st.metric("Visa Approval Rate", f"{overall_approval_rate:.2f}%")
        
            st.markdown("---")
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.subheader("🏫 Top Chosen Schools")
                school_counts = filtered_data['Chosen School'].value_counts().head(10).reset_index()
                school_counts.columns = ['School', 'Number of Students']
                fig = px.bar(school_counts, x='School', y='Number of Students',
                             labels={'Number of Students': 'Number of Students', 'School': 'School'},
                             title="Top 10 Chosen Schools")
                st.plotly_chart(fig, use_container_width=True)
        
            with col2:
                st.subheader("🛂 Student Visa Approval")
                visa_status = filtered_data['Visa Result'].value_counts()
                colors = {'Visa Approved': 'blue', 'Visa Denied': 'red', '0 not yet': 'grey', 'not our school': 'lightblue'}
                fig = px.pie(values=visa_status.values, names=visa_status.index,
                             title="Visa Application Results", color=visa_status.index, 
                             color_discrete_map=colors)
                st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            # New section for Visa Approval Rate by School
            st.subheader("🏆 Top 8 Schools by Visa Approval Rate")
            
            def school_approval_rate(group):
                return calculate_visa_approval_rate(group)[0]
            
            school_visa_stats = filtered_data.groupby('Chosen School').apply(school_approval_rate).reset_index()
            school_visa_stats.columns = ['School', 'Approval Rate']
            
            # Sort by approval rate and get top 8
            top_8_schools = school_visa_stats.sort_values('Approval Rate', ascending=False).head(8)
            
            fig = px.bar(top_8_schools, x='School', y='Approval Rate',
                         text='Approval Rate',
                         labels={'Approval Rate': 'Visa Approval Rate (%)', 'School': 'School'},
                         title="Top 8 Schools by Visa Approval Rate")
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.subheader("📅 Applications Over Time")
                monthly_apps = filtered_data.groupby(filtered_data['DATE'].dt.to_period("M")).size().reset_index(name='count')
                monthly_apps['DATE'] = monthly_apps['DATE'].dt.to_timestamp()
                fig = px.line(monthly_apps, x='DATE', y='count',
                              labels={'count': 'Number of Applications', 'DATE': 'Date'},
                              title="Monthly Application Trend")
                st.plotly_chart(fig, use_container_width=True)
        
            with col2:
                st.subheader("💰 Payment Methods")
                payment_counts = filtered_data['Payment Type'].value_counts()
                fig = px.pie(values=payment_counts.values, names=payment_counts.index,
                             title="Payment Method Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.subheader("👥 Gender Distribution")
                gender_counts = filtered_data['Gender'].value_counts()
                fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                             title="Gender Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
            with col2:
                st.subheader("🔄 Application Attempts")
                attempts_counts = filtered_data['Attempts'].value_counts().reset_index()
                attempts_counts.columns = ['Attempt', 'Number of Students']
                fig = px.bar(attempts_counts, x='Attempt', y='Number of Students',
                             labels={'Number of Students': 'Number of Students', 'Attempt': 'Attempt'},
                             title="Application Attempts Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            st.subheader("🏆 Top Performing Agents")
            agent_performance = filtered_data['Agent'].value_counts().head(5).reset_index()
            agent_performance.columns = ['Agent', 'Number of Students']
            fig = px.bar(agent_performance, x='Agent', y='Number of Students',
                         labels={'Number of Students': 'Number of Students', 'Agent': 'Agent'},
                         title="Top 5 Agents by Number of Students")
            st.plotly_chart(fig, use_container_width=True)
        
            st.markdown("---")
        
            # New Payment Amount Statistics Section
            st.header("💰 Top 5 Payment Types")
        
            # Count the number of payments in each category and get the top 5
            payment_counts = filtered_data['Payment Amount'].value_counts().nlargest(5)
        
            # Create a bar chart for top 5 payment categories
            fig = px.bar(x=payment_counts.index, y=payment_counts.values,
                         labels={'x': 'Payment Amount', 'y': 'Number of Payments'},
                         title="Top 5 Payment Types")
            fig.update_traces(text=payment_counts.values, textposition='outside')
            fig.update_layout(xaxis_title="Payment Amount",
                              yaxis_title="Number of Payments",
                              bargap=0.2)
            
            st.plotly_chart(fig, use_container_width=True)
        
            # Display the data in a table format as well
            st.subheader("Top 5 Payment Types Distribution")
            payment_df = pd.DataFrame({'Payment Amount': payment_counts.index, 'Number of Payments': payment_counts.values})
            st.dataframe(payment_df)
        
        if __name__ == "__main__":
            statistics_page()

if __name__ == "__main__":
    statistics_page()

# File: 👥Students.py

import streamlit as st
from auth import check_password

def students_page():
    if check_password():
        st.title("Students Page")
        import os
        import json
        import gspread
        import streamlit as st
        import pandas as pd
        from datetime import datetime, timedelta
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import plotly.express as px
        import functools
        import logging
        import asyncio
        import aiohttp
        import threading
        import numpy as np
        import string
        import time
        import re
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        def on_student_select():
            st.session_state.student_changed = True
        
        def reload_data(spreadsheet_id):
            data = load_data(spreadsheet_id)
            st.session_state['data'] = data
            return data
        
        # Caching decorator
        def cache_with_timeout(timeout_minutes=60):
            def decorator(func):
                cache = {}
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    key = str(args) + str(kwargs)
                    if key in cache:
                        result, timestamp = cache[key]
                        if datetime.now() - timestamp < timedelta(minutes=timeout_minutes):
                            return result
                    result = func(*args, **kwargs)
                    cache[key] = (result, datetime.now())
                    return result
                return wrapper
            return decorator
        
        
        # Use Streamlit secrets for service account info
        SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
        
        # Define the scopes
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        
        # Authenticate and build the Google Drive service
        @st.cache_resource
        @cache_with_timeout(timeout_minutes=60)
        def get_google_drive_service():
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)
        
        # Authenticate and build the Google Sheets service
        @st.cache_resource
        @cache_with_timeout(timeout_minutes=60)
        def get_google_sheet_client():
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
            return gspread.authorize(creds)
        
        # Function to upload a file to Google Drive
        @cache_with_timeout(timeout_minutes=5)
        def upload_file_to_drive(file_path, mime_type, folder_id=None):
            service = get_google_drive_service()
            file_metadata = {'name': os.path.basename(file_path)}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id').execute()
            file_id = file.get('id')
            if file_id:
                st.session_state.upload_success = True
                return file_id
            return None
        
        def load_data(spreadsheet_id):
            sheet_headers = {
                'ALL': [
                    'DATE','First Name', 'Last Name','Age', 'Phone N°', 'Address', 'E-mail', 
                    'Emergency contact N°', 'Chosen School', 'Specialite', 'Duration', 
                    'Payment Amount', 'Sevis payment ?', 'Application payment ?', 'DS-160 maker', 
                    'Password DS-160', 'Secret Q.', 'School Entry Date', 'Entry Date in the US', 
                    'ADDRESS in the U.S', 'E-MAIL RDV', 'PASSWORD RDV', 'EMBASSY ITW. DATE', 
                    'Attempts', 'Visa Result', 'Agent', 'Note', 'Stage','Gender','BANK','Prep ITW','School Paid'
                ]
            }
            
            try:
                client = get_google_sheet_client()
                sheet = client.open_by_key(spreadsheet_id)
                
                combined_data = pd.DataFrame()
                
                for worksheet in sheet.worksheets():
                    title = worksheet.title
                    expected_headers = sheet_headers.get(title, None)
                    
                    if expected_headers:
                        data = worksheet.get_all_records(expected_headers=expected_headers, value_render_option='UNFORMATTED_VALUE')
                    else:
                        data = worksheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
                    
                    df = pd.DataFrame(data)
                    if not df.empty:
                        # Ensure phone numbers and other text fields are treated as strings
                        text_columns = ['First Name', 'Last Name', 'Phone N°', 'Emergency contact N°', 'E-mail', 'Address']
                        for col in text_columns:
                            if col in df.columns:
                                df[col] = df[col].astype(str)
                        
                        # Create Student Name column
                        if 'First Name' in df.columns and 'Last Name' in df.columns:
                            df['Student Name'] = df['First Name'] + " " + df['Last Name']
                        
                        # Parse dates
                        date_columns = ['DATE', 'School Entry Date', 'Entry Date in the US', 'EMBASSY ITW. DATE']
                        for col in date_columns:
                            if col in df.columns:
                                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                        
                        df.dropna(subset=['Student Name'], inplace=True)
                        df.dropna(how='all', inplace=True)
                        combined_data = pd.concat([combined_data, df], ignore_index=True)
                
                combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
                combined_data.reset_index(drop=True, inplace=True)
        
                return combined_data
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                return pd.DataFrame()
        
        # Function to save data to Google Sheets (batch up)
        def save_data(df, spreadsheet_id, sheet_name, student_name):
            def replace_invalid_floats(val):
                if isinstance(val, float):
                    if pd.isna(val) or np.isinf(val):
                        return None
                return val
        
            # Get the row of the specific student
            student_row = df[df['Student Name'] == student_name].iloc[0]
        
            # Replace NaN and inf values with None for this student's data
            student_row = student_row.apply(replace_invalid_floats)
        
            # Replace [pd.NA, pd.NaT, float('inf'), float('-inf')] with None
            student_row = student_row.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], None)
        
            # Format the date columns to ensure consistency
            date_columns = ['DATE', 'School Entry Date', 'Entry Date in the US', 'EMBASSY ITW. DATE']
            for col in date_columns:
                if col in student_row.index:
                    value = student_row[col]
                    if pd.notna(value):
                        try:
                            # Convert to datetime and format as string
                            formatted_date = pd.to_datetime(value).strftime('%d/%m/%Y %H:%M:%S')
                            student_row[col] = formatted_date
                        except:
                            student_row[col] = ""
        
            client = get_google_sheet_client()
            sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            
            # Find the row of the student in the sheet
            cell = sheet.find(student_name)
            if cell is None:
                logger.error(f"Student {student_name} not found in the sheet.")
                return
        
            row_number = cell.row
        
            # Prepare the data for update
            values = [student_row.tolist()]
            
            # Calculate the last column letter
            num_columns = len(student_row)
            if num_columns <= 26:
                last_column = string.ascii_uppercase[num_columns - 1]
            else:
                last_column = string.ascii_uppercase[(num_columns - 1) // 26 - 1] + string.ascii_uppercase[(num_columns - 1) % 26]
        
            # Update only the specific student's row
            sheet.update(f'A{row_number}:{last_column}{row_number}', values)
        
            logger.info(f"Updated data for student: {student_name}")
        
        def format_date(date_string):
            if pd.isna(date_string) or date_string == 'NaT':
                return "Not set"
            try:
                # Parse the date string, assuming day first format
                date = pd.to_datetime(date_string, errors='coerce', dayfirst=True)
                return date.strftime('%d %B %Y') if not pd.isna(date) else "Invalid Date"
            except:
                return "Invalid Date"
        
        
        
        
        def clear_cache_and_rerun():
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()
        
        # Function to calculate days until interview
        def calculate_days_until_interview(interview_date):
            try:
                # Parse the interview date, assuming day first format
                interview_date = pd.to_datetime(interview_date, format='%d/%m/%Y %H:%M:%S', dayfirst=True)
                if pd.isnull(interview_date):
                    return None
                today = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
                days_remaining = (interview_date - today).days
                return days_remaining
            except Exception as e:
                logger.error(f"Error calculating days until interview: {str(e)}")
                return None
        
        
        # Function to get visa status
        def get_visa_status(result):
            result_mapping = {
                'Denied': 'Denied',
                'Approved': 'Approved',
                'Not our school partner': 'Not our school partner',
            }
            return result_mapping.get(result, 'Unknown')
        
        @cache_with_timeout(timeout_minutes=5)
        def check_folder_exists(folder_name, parent_id=None):
            try:
                service = get_google_drive_service()
                query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
                if parent_id:
                    query += f" and '{parent_id}' in parents"
        
                results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                folders = results.get('files', [])
                if folders:
                    return folders[0].get('id')
                else:
                    return None
            except Exception as e:
                logger.error(f"An error occurred while checking if folder exists: {str(e)}")
                return None
        
        # Function to create a new folder in Google Drive
        def create_folder_in_drive(folder_name, parent_id=None):
            service = get_google_drive_service()
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
        
        # Function to check if a file exists in a folder
        from googleapiclient.errors import HttpError
        
        @cache_with_timeout(timeout_minutes=5)
        def check_file_exists(file_name, student_folder_id, document_type):
            service = get_google_drive_service()
            
            # First, find the document type folder within the student folder
            document_folder_query = f"name = '{document_type}' and '{student_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            document_folder_results = service.files().list(q=document_folder_query, spaces='drive', fields='files(id)').execute()
            document_folders = document_folder_results.get('files', [])
            
            if not document_folders:
                logger.info(f"Document folder '{document_type}' not found in student folder.")
                return False
            
            document_folder_id = document_folders[0]['id']
            
            # Now check for the file within the document type folder
            file_query = f"name = '{file_name}' and '{document_folder_id}' in parents and trashed = false"
            try:
                results = service.files().list(
                    q=file_query,
                    spaces='drive',
                    fields='files(id, name)',
                    pageSize=1
                ).execute()
                files = results.get('files', [])
                file_exists = len(files) > 0
                logger.info(f"File '{file_name}' exists: {file_exists}")
                return file_exists
            except HttpError as error:
                logger.error(f"An error occurred while checking if file exists: {error}")
                return False
        
        
        # Function to handle file upload and folder creation
        def handle_file_upload(student_name, document_type, uploaded_file):
            parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'  # Use the provided parent folder ID
            
            # Check if student folder exists, if not create it
            student_folder_id = check_folder_exists(student_name, parent_folder_id)
            if not student_folder_id:
                student_folder_id = create_folder_in_drive(student_name, parent_folder_id)
                logger.info(f"Created new folder for student: {student_name}")
            
            # Check if document type folder exists within student folder, if not create it
            document_folder_id = check_folder_exists(document_type, student_folder_id)
            if not document_folder_id:
                document_folder_id = create_folder_in_drive(document_type, student_folder_id)
                logger.info(f"Created new folder for document type: {document_type}")
            
            file_name = uploaded_file.name
            
            # Ensure no double extensions
            if file_name.lower().endswith('.pdf.pdf'):
                file_name = file_name[:-4]
            
            file_exists = check_file_exists(file_name, student_folder_id, document_type)
            if not file_exists:
                with st.spinner(f"Uploading {file_name}..."):
                    temp_file_path = f"/tmp/{file_name}"
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    mime_type = uploaded_file.type
                    file_id = upload_file_to_drive(temp_file_path, mime_type, document_folder_id)
                    os.remove(temp_file_path)
                if file_id:
                    st.success(f"{file_name} uploaded successfully!")
                    if 'document_status_cache' in st.session_state:
                        st.session_state['document_status_cache'].pop(student_name, None)
                    st.rerun()
                    return file_id
            else:
                st.warning(f"{file_name} already exists for this student in the {document_type} folder.")
            
            return None
        
        
        
        async def fetch_document_status(session, document_type, student_folder_id, service):
            document_folder_id = await check_folder_exists_async(document_type, student_folder_id, service)
            if document_folder_id:
                files = await list_files_in_folder_async(document_folder_id, service)
                return document_type, bool(files), files
            return document_type, False, []
        
        async def check_document_status_async(student_name, service):
            parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'
            student_folder_id = await check_folder_exists_async(student_name, parent_folder_id, service)
            
            document_types = ["Passport", "Bank Statement", "Financial Letter", 
                              "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                              "SEVIS Receipt", "I20"]
            document_status = {doc_type: {'status': False, 'files': []} for doc_type in document_types}
        
            if not student_folder_id:
                logger.info(f"Student folder not found for {student_name}")
                return document_status
        
            async with aiohttp.ClientSession() as session:
                tasks = [
                    fetch_document_status(session, document_type, student_folder_id, service)
                    for document_type in document_types
                ]
                results = await asyncio.gather(*tasks)
                for doc_type, status, files in results:
                    document_status[doc_type] = {'status': status, 'files': files}
                    logger.info(f"Document status for {doc_type}: {status}, Files: {files}")
            
            return document_status
        
        async def check_folder_exists_async(folder_name, parent_id, service):
            try:
                query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
                if parent_id:
                    query += f" and '{parent_id}' in parents"
        
                results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                folders = results.get('files', [])
                return folders[0].get('id') if folders else None
            except Exception as e:
                logger.error(f"An error occurred while checking if folder exists: {str(e)}")
                return None
        
        async def list_files_in_folder_async(folder_id, service):
            try:
                query = f"'{folder_id}' in parents and trashed=false"
                results = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
                return results.get('files', [])
            except Exception as e:
                logger.error(f"An error occurred while listing files in folder: {str(e)}")
                return []
        
        def trash_file_in_drive(file_id, student_name):
            service = get_google_drive_service()
            try:
                # Move the file to the trash
                file = service.files().update(
                    fileId=file_id,
                    body={"trashed": True}
                ).execute()
                
                # Clear the document status cache for this student
                if 'document_status_cache' in st.session_state:
                    st.session_state['document_status_cache'].pop(student_name, None)
                
                return True
            
            except Exception as e:
                st.error(f"An error occurred while moving the file to trash: {str(e)}")
                return False
        
        def get_document_status(student_name):
            if 'document_status_cache' not in st.session_state:
                st.session_state['document_status_cache'] = {}
            if student_name in st.session_state['document_status_cache']:
                return st.session_state['document_status_cache'][student_name]
            else:
                service = get_google_drive_service()
                document_status = asyncio.run(check_document_status_async(student_name, service))
                st.session_state['document_status_cache'][student_name] = document_status
                return document_status
        
        # Debouncing inputs for edit mode
        debounce_lock = threading.Lock()
        
        def debounce(func, wait=0.5):
            def debounced(*args, **kwargs):
                def call_it():
                    with debounce_lock:
                        func(*args, **kwargs)
                if hasattr(debounced, '_timer'):
                    debounced._timer.cancel()
                debounced._timer = threading.Timer(wait, call_it)
                debounced._timer.start()
            return debounced
        
        @debounce
        def update_student_data(*args, **kwargs):
            pass
        
        # Main function
        def main():
            st.set_page_config(page_title="Student Application Tracker", layout="wide")
            
            if 'student_changed' not in st.session_state:
                st.session_state.student_changed = False
            if 'upload_success' not in st.session_state:
                st.session_state.upload_success = False
            if 'selected_student' not in st.session_state:
                st.session_state.selected_student = ""
            if 'active_tab' not in st.session_state:
                st.session_state.active_tab = "Personal"
            # Initialize other session state variables
            for key in ['visa_status', 'current_step', 'payment_date', 'payment_method', 'payment_type', 'compte', 'sevis_payment', 'application_payment']:
                if key not in st.session_state:
                    st.session_state[key] = None
        
            # Check if we need to refresh the page
            if st.session_state.upload_success:
                st.session_state.upload_success = False
                st.rerun()
        
            st.markdown("""
            <style>
                .reportview-container {
                    background: #f0f2f6;
                }
                .main .block-container {
                    padding-top: 2rem;
                    padding-bottom: 2rem;
                }
                h1, h2, h3 {
                    color: #1E3A8A;
                }
                .stSelectbox, .stTextInput {
                    background-color: white;
                    color: #2c3e50;
                    border-radius: 5px;
                    padding: 10px;
                }
                .stExpander {
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 10px;
                }
                .css-1544g2n {
                    padding: 2rem;
                }
                .stMetric {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }
                .stMetric .metric-label {
                    font-weight: bold;
                }
                .stButton>button {
                    background-color: #ff7f50;
                    color: white;
                    font-weight: bold;
                }
                .stButton>button:hover {
                    background-color: #ff6347;
                }
                .stTextInput input {
                    font-size: 1rem;
                    padding: 10px;
                    margin-bottom: 10px;
                }
                .progress-container {
                    width: 100%;
                    background-color: #e0e0e0;
                    border-radius: 10px;
                    margin-bottom: 1rem;
                }
                .progress-bar {
                    height: 20px;
                    background-color: #4caf50;
                    border-radius: 10px;
                    transition: width 0.5s ease-in-out;
                    text-align: center;
                    line-height: 20px;
                    color: white;
                    font-weight: bold;
                }
            </style>
            """, unsafe_allow_html=True)
        
            st.markdown("""
            <div class="stCard" style="text-align: center;">
                <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" width="150" height="150">
                <h1>The Us House</h1>
            </div>
            """, unsafe_allow_html=True)
        
            spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
            
            if 'data' not in st.session_state or st.session_state.get('reload_data', False):
                data = load_data(spreadsheet_id)
                st.session_state['data'] = data
                st.session_state['reload_data'] = False
            else:
                data = st.session_state['data']
        
            if not data.empty:
                current_steps = ["All"] + list(data['Stage'].unique())
                agents = ["All", "Nesrine", "Hamza", "Djazila"]
                school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English ",
                                  "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                                  "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
                attempts_options = ["All", "1 st Try", "2 nd Try", "3 rd Try"]
                Gender_options = ["Male", "Female"]
        
                st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
        
                with col1:
                    status_filter = st.selectbox("Filter by Stage", current_steps, key="status_filter")
                with col2:
                    agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
                with col3:
                    school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
                with col4:
                    attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")
        
                # Apply filters
                filtered_data = data
                if status_filter != "All":
                    filtered_data = filtered_data[filtered_data['Stage'] == status_filter]
                if agent_filter != "All":
                    filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
                if school_filter != "All":
                    filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
                if attempts_filter != "All":
                    filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]
                
                student_names = filtered_data['Student Name'].tolist()
                
                if not filtered_data.empty:
                    st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
                    col2, col1, col3 = st.columns([3, 2, 3])
                
                    with col2:
                        search_query = st.selectbox(
                            "🔍 Search for a student (First or Last Name)",
                            options=student_names,
                            key="search_query",
                            index=student_names.index(st.session_state.selected_student) if st.session_state.selected_student in student_names else 0,
                            on_change=on_student_select
                        )
                        # After the selectbox:
                        if st.session_state.student_changed or st.session_state.selected_student != search_query:
                            st.session_state.selected_student = search_query
                            st.session_state.student_changed = False
                            st.rerun()
                        st.subheader("📝 Student Notes")
                        
                        # Get the current note for the selected student
                        selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                        current_note = selected_student['Note'] if 'Note' in selected_student else ""
                    
                        # Create a text area for note input
                        new_note = st.text_area("Enter/Edit Note:", value=current_note, height=150, key="note_input")
                    
                        # Save button for the note
                        if st.button("Save Note"):
                            # Update the note in the DataFrame
                            filtered_data.loc[filtered_data['Student Name'] == search_query, 'Note'] = new_note
                            
                            # Save the updated data back to Google Sheets
                            save_data(filtered_data, spreadsheet_id, 'ALL', search_query)
                            
                            st.success("Note saved successfully!")
                            
                            # Set a flag to reload data on next run
                            st.session_state['reload_data'] = True
                            
                            # Rerun the app to show updated data
                            st.rerun()
                      
        
                    
                    with col1:
                        st.subheader("Application Status")
                        selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                        steps = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.',  'CLIENTS ']
                        current_step = selected_student['Stage']
                        step_index = steps.index(current_step) if current_step in steps else 0
                        progress = ((step_index + 1) / len(steps)) * 100
                
                        progress_bar = f"""
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {progress}%;">
                                {int(progress)}%
                            </div>
                        </div>
                        """
                        st.markdown(progress_bar, unsafe_allow_html=True)
                        
                        payment_date_str = selected_student['DATE']
                        try:
                            payment_date = pd.to_datetime(payment_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                            payment_date_value = payment_date.strftime('%d %B %Y') if not pd.isna(payment_date) else "Not set"
                        except AttributeError:
                            payment_date_value = "Not set"
                        
                        st.write(f"**📆 Date of Payment:** {payment_date_value}")
                
                        st.write(f"**🚩 Current Stage:** {current_step}")
                
                        # Agent
                        agent = selected_student['Agent']
                        st.write(f"**🧑‍💼 Agent:** {agent}")
                        
                        # SEVIS Payment
                        sevis_payment = selected_student['Sevis payment ?']
                        sevis_icon = "✅" if selected_student['Sevis payment ?'] == "YES" else "❌"
                        st.write(f"**💲 SEVIS Payment:** {sevis_icon} ({sevis_payment})")
                
                        # Application Payment
                        application_payment = selected_student['Application payment ?']
                        application_icon = "✅" if selected_student['Application payment ?'] == "YES" else "❌"
                        st.write(f"**💸 Application Payment:** {application_icon} ({application_payment})")
                
                        # Visa Status
                        visa_status = selected_student['Visa Result']
                        st.write(f"**🛂 Visa Status:** {visa_status}")
                
                        # Find the section where we display the school entry date
                        entry_date = format_date(selected_student['School Entry Date'])
                        st.write(f"**🏫 School Entry Date:** {entry_date}")
                
                        # Days until Interview
                        interview_date = selected_student['EMBASSY ITW. DATE']
                        days_remaining = calculate_days_until_interview(interview_date)
                        if days_remaining is not None:
                            st.metric("📅 Days until interview", days_remaining)
                        else:
                            st.metric("📅 Days until interview", "N/A")
                
                    with col3:
                        student_name = selected_student['Student Name']
                        document_status = get_document_status(student_name)
                        st.subheader("Document Status")
                
                        for doc_type, status_info in document_status.items():
                            icon = "✅" if status_info['status'] else "❌"
                            col1, col2 = st.columns([9, 1])
                            with col1:
                                st.markdown(f"**{icon} {doc_type}**")
                                for file in status_info['files']:
                                    st.markdown(f"- [{file['name']}]({file['webViewLink']})")
                            if status_info['status']:
                                with col2:
                                    if st.button("🗑️", key=f"delete_{status_info['files'][0]['id']}", help="Delete file"):
                                        file_id = status_info['files'][0]['id']
                                        if trash_file_in_drive(file_id, student_name):
                                            st.session_state['reload_data'] = True
                                            clear_cache_and_rerun()
                
                else:
                    st.info("No students found matching the search criteria.")
        
                                            
                if not filtered_data.empty:
                    selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                    student_name = selected_student['Student Name']
        
                    edit_mode = st.toggle("Edit Mode", value=False)
        
        
        
                    # Tabs for student information
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Personal", "School", "Embassy", "Payment","Stage", "Documents"])
                    
                    # Options for dropdowns
                    school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                                      "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago","BEA Huston","BIA Huston","OHLA Miami", "UCDEA","HAWAII","Not Partner", "Not yet"]
                    
                    payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
                    School_paid_opt = ["YES", "NO"]
                    Prep_ITW_opt = ["YES", "NO"]
        
        
                    payment_type_options = ["Cash", "CCP", "Baridimob", "Bank"]
                    compte_options = ["Mohamed", "Sid Ali"]
                    yes_no_options = ["YES", "NO"]
                    attempts_options = ["1st Try", "2nd Try", "3rd Try"]
                    Gender_options = ["","Male", "Female"]
        
                    
                    with tab1:
                        st.markdown('<div class="stCard">', unsafe_allow_html=True)
                        st.subheader("📋 Personal Information")
                        if edit_mode:
                            first_name = st.text_input("First Name", selected_student['First Name'], key="first_name", on_change=update_student_data)
                            last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name", on_change=update_student_data)
                            Age = st.text_input("Age", selected_student['Age'], key="Age", on_change=update_student_data)
                            Gender = st.selectbox(
                                "Gender", 
                                Gender_options, 
                                index=Gender_options.index(selected_student['Gender']) if selected_student['Gender'] in Gender_options else 0,
                                key="Gender", 
                                on_change=update_student_data
                            )
                    
                            # Updated phone number input
                            phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number", on_change=update_student_data)
                            if phone_number and not re.match(r'^\+?[0-9]+$', phone_number):
                                st.warning("Phone number should only contain digits, and optionally start with a '+'")
                            
                            email = st.text_input("Email", selected_student['E-mail'], key="email", on_change=update_student_data)
                            
                            # Updated emergency contact input
                            emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact", on_change=update_student_data)
                            if emergency_contact and not re.match(r'^\+?[0-9]+$', emergency_contact):
                                st.warning("Emergency contact number should only contain digits, and optionally start with a '+'")
                            
                            address = st.text_input("Address", selected_student['Address'], key="address", on_change=update_student_data)
                            attempts = st.selectbox(
                                "Attempts", 
                                attempts_options, 
                                index=attempts_options.index(selected_student['Attempts']) if selected_student['Attempts'] in attempts_options else 0,
                                key="attempts", 
                                on_change=update_student_data
                            )
                            agentss = st.selectbox(
                            "Agent", 
                            agents, 
                            index=agents.index(selected_student['Agent']) if selected_student['Agent'] in attempts_options else 0,
                            key="Agent", 
                            on_change=update_student_data
                        )
                        else:
                            st.write(f"**First Name:** {selected_student['First Name']}")
                            st.write(f"**Last Name:** {selected_student['Last Name']}")
                            st.write(f"**Age:** {selected_student['Age']}")
                            st.write(f"**Gender:** {selected_student['Gender']}")
                            st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                            st.write(f"**Email:** {selected_student['E-mail']}")
                            st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                            st.write(f"**Address:** {selected_student['Address']}")
                            st.write(f"**Attempts:** {selected_student['Attempts']}")
                            st.write(f"**Agent:** {selected_student['Agent']}")
                        st.markdown('</div>', unsafe_allow_html=True)
                            
                        with tab2:
                            st.markdown('<div class="stCard">', unsafe_allow_html=True)
                            st.subheader("🏫 School Information")
                            if edit_mode:
                                chosen_school = st.selectbox("Chosen School", school_options, index=school_options.index(selected_student['Chosen School']) if selected_student['Chosen School'] in school_options else 0, key="chosen_school", on_change=update_student_data)
                                specialite = st.text_input("Specialite", selected_student['Specialite'], key="specialite", on_change=update_student_data)
                                duration = st.text_input("Duration", selected_student['Duration'], key="duration", on_change=update_student_data)
                                Bankstatment = st.text_input("BANK", selected_student['BANK'], key="Bankstatment", on_change=update_student_data)
                        
                                school_entry_date = pd.to_datetime(selected_student['School Entry Date'], errors='coerce', dayfirst=True)
                                school_entry_date = st.date_input(
                                    "School Entry Date",
                                    value=school_entry_date if not pd.isna(school_entry_date) else None,
                                    key="school_entry_date",
                                    on_change=update_student_data
                                )
                                
                                entry_date_in_us = pd.to_datetime(selected_student['Entry Date in the US'], errors='coerce', dayfirst=True)
                                entry_date_in_us = st.date_input(
                                    "Entry Date in the US",
                                    value=entry_date_in_us if not pd.isna(entry_date_in_us) else None,
                                    key="entry_date_in_us",
                                    on_change=update_student_data
                                )
                                School_Paid = st.selectbox(
                                    "School Paid", 
                                    School_paid_opt, 
                                    index=School_paid_opt.index(selected_student['School Paid']) if selected_student['School Paid'] in School_paid_opt else 0,
                                    key="School_Paid",  # Note the capitalization here
                                    on_change=update_student_data
                                )
                            else:
                                st.write(f"**Chosen School:** {selected_student['Chosen School']}")
                                st.write(f"**Specialite:** {selected_student['Specialite']}")
                                st.write(f"**Duration:** {selected_student['Duration']}")
                                st.write(f"**Bank:** {selected_student['BANK']}")
                                st.write(f"**School Entry Date:** {format_date(selected_student['School Entry Date'])}")
                                st.write(f"**Entry Date in the US:** {format_date(selected_student['Entry Date in the US'])}")
                                st.write(f"**School Paid:** {selected_student['School Paid']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab3:
                        st.markdown('<div class="stCard">', unsafe_allow_html=True)
                        st.subheader("🏛️ Embassy Information")
                        if edit_mode:
                            address_us = st.text_input("Address in the U.S", selected_student['ADDRESS in the U.S'], key="address_us", on_change=update_student_data)
                            email_rdv = st.text_input("E-mail RDV", selected_student['E-MAIL RDV'], key="email_rdv", on_change=update_student_data)
                            password_rdv = st.text_input("Password RDV", selected_student['PASSWORD RDV'], key="password_rdv", on_change=update_student_data)
                            
                            # Handle embassy interview date
                            embassy_itw_date_str = selected_student['EMBASSY ITW. DATE']
                            try:
                                embassy_itw_date = pd.to_datetime(embassy_itw_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                                embassy_itw_date_value = embassy_itw_date.date() if not pd.isna(embassy_itw_date) else None
                            except AttributeError:
                                embassy_itw_date_value = None
                
                            embassy_itw_date = st.date_input(
                                "Embassy Interview Date", 
                                value=embassy_itw_date_value,
                                key="embassy_itw_date", 
                                on_change=update_student_data
                            )
                
                            ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker", on_change=update_student_data)
                            password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160", on_change=update_student_data)
                            secret_q = st.text_input("Secret Question", selected_student['Secret Q.'], key="secret_q", on_change=update_student_data)
                            Prep_ITW = st.selectbox(
                                "Prep ITW", 
                                Prep_ITW_opt, 
                                index=Prep_ITW_opt.index(selected_student['Prep ITW']) if selected_student['Prep ITW'] in Prep_ITW_opt else 0,
                                key="Prep_ITW",  # Note the capitalization here
                                on_change=update_student_data
                            )
        
                        else:
                            st.write(f"**Address in the U.S:** {selected_student['ADDRESS in the U.S']}")
                            st.write(f"**E-mail RDV:** {selected_student['E-MAIL RDV']}")
                            st.write(f"**Password RDV:** {selected_student['PASSWORD RDV']}")
                            st.write(f"**Embassy Interview Date:** {format_date(selected_student['EMBASSY ITW. DATE'])}")
                            st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                            st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                            st.write(f"**Secret Question:** {selected_student['Secret Q.']}")
                            st.write(f"**ITW Prep:** {selected_student['Prep ITW']}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with tab4:
                        st.markdown('<div class="stCard">', unsafe_allow_html=True)
                        st.subheader("💰 Payment Information")
                        if edit_mode:
                            payment_date_str = selected_student['DATE']
                            try:
                                payment_date = pd.to_datetime(payment_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                                payment_date_value = payment_date if not pd.isna(payment_date) else None
                            except AttributeError:
                                payment_date_value = None
                    
                            payment_date = st.date_input(
                                "Payment Date", 
                                value=payment_date_value,
                                key="payment_date", 
                                on_change=update_student_data
                            )
                    
                            payment_method = st.selectbox("Payment Method", payment_amount_options, index=payment_amount_options.index(selected_student['Payment Amount']) if selected_student['Payment Amount'] in payment_amount_options else 0, key="payment_method", on_change=update_student_data)
                            payment_type = st.selectbox("Payment Type", payment_type_options, key="payment_type", on_change=update_student_data)
                            compte = st.selectbox("Compte", compte_options, key="compte", on_change=update_student_data)
                            sevis_payment = st.selectbox("Sevis Payment", yes_no_options, index=yes_no_options.index(selected_student['Sevis payment ?']) if selected_student['Sevis payment ?'] in yes_no_options else 0, key="sevis_payment", on_change=update_student_data)
                            application_payment = st.selectbox("Application Payment", yes_no_options, index=yes_no_options.index(selected_student['Application payment ?']) if selected_student['Application payment ?'] in yes_no_options else 0, key="application_payment", on_change=update_student_data)
                        else:
                            st.write(f"**Payment Date:** {format_date(selected_student['DATE'])}")
                            st.write(f"**Payment Method:** {selected_student['Payment Amount']}")
                            st.write(f"**Payment Type:** {selected_student['Payment Type']}")
                            st.write(f"**Compte:** {selected_student['Compte']}")
                            st.write(f"**Sevis Payment:** {selected_student['Sevis payment ?']}")
                            st.write(f"**Application Payment:** {selected_student['Application payment ?']}")
                        st.markdown('</div>', unsafe_allow_html=True)
            
                        
                    with tab6:
                        st.markdown('<div class="stCard">', unsafe_allow_html=True)
                        st.subheader("📂 Document Upload and Status")
                        document_type = st.selectbox("Select Document Type", 
                                                     ["Passport", "Bank Statement", "Financial Letter", 
                                                      "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                                                      "SEVIS Receipt", "I20"], 
                                                     key="document_type")
                        uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png", "pdf"], key="uploaded_file")
                        
                        if uploaded_file and st.button("Upload Document"):
                            file_id = handle_file_upload(student_name, document_type, uploaded_file)
                            if file_id:
                                st.success(f"{document_type} uploaded successfully!")
                                if 'document_status_cache' in st.session_state:
                                    st.session_state['document_status_cache'].pop(student_name, None)
                                clear_cache_and_rerun()  # Clear cache and rerun the app
                            else:
                                st.error("An error occurred while uploading the document.")
                    with tab5:
                        st.markdown('<div class="stCard">', unsafe_allow_html=True)
                        st.subheader("🚩 Current Stage")
                    
                        # Define the stages
                        stages = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.',  'CLIENTS']
                    
                        if edit_mode:
                            current_stage = st.selectbox(
                                "Current Stage",
                                stages,
                                index=stages.index(selected_student['Stage']) if selected_student['Stage'] in stages else 0,
                                key="current_stage",
                                on_change=update_student_data
                            )
                        else:
                            st.write(f"**Current Stage:** {selected_student['Stage']}")
                    
                        # Display progress bar
                        step_index = stages.index(selected_student['Stage']) if selected_student['Stage'] in stages else 0
                        progress = ((step_index + 1) / len(stages)) * 100
                    
                        progress_bar = f"""
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {progress}%;">
                                {int(progress)}%
                            </div>
                        </div>
                        """
                        st.markdown(progress_bar, unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)
            
                    if edit_mode and st.button("Save Changes", key="save_changes_button"):
                        updated_student = {
                            'First Name': st.session_state.get('first_name', ''),
                            'Last Name': st.session_state.get('last_name', ''),
                            'Phone N°': st.session_state.get('phone_number', ''),
                            'E-mail': st.session_state.get('email', ''),
                            'Emergency contact N°': st.session_state.get('emergency_contact', ''),
                            'Address': st.session_state.get('address', ''),
                            'Attempts': st.session_state.get('attempts', ''),
                            'Chosen School': st.session_state.get('chosen_school', ''),
                            'Specialite': st.session_state.get('specialite', ''),
                            'Duration': st.session_state.get('duration', ''),
                            'School Entry Date': st.session_state.get('school_entry_date', ''),
                            'Entry Date in the US': st.session_state.get('entry_date_in_us', ''),
                            'ADDRESS in the U.S': st.session_state.get('address_us', ''),
                            'E-MAIL RDV': st.session_state.get('email_rdv', ''),
                            'PASSWORD RDV': st.session_state.get('password_rdv', ''),
                            'EMBASSY ITW. DATE': st.session_state.get('embassy_itw_date', ''),
                            'DS-160 maker': st.session_state.get('ds160_maker', ''),
                            'Password DS-160': st.session_state.get('password_ds160', ''),
                            'Secret Q.': st.session_state.get('secret_q', ''),
                            'Visa Result': st.session_state.get('visa_status', ''),
                            'Stage': st.session_state.get('current_stage', ''),  # Add this line
                            'DATE': st.session_state.get('payment_date', ''),
                            'BANK': st.session_state.get('Bankstatment', ''),
                            'Gender': st.session_state.get('Gender', ''),
                            'Payment Amount': st.session_state.get('payment_method', ''),
                            'Payment Type': st.session_state.get('payment_type', ''),
                            'Compte': st.session_state.get('compte', ''),
                            'School Paid': st.session_state.get('School_Paid', ''),
                            'Prep ITW': st.session_state.get('Prep_ITW', ''),
                            'Age': st.session_state.get('Age', ''),
                            'Sevis payment ?': st.session_state.get('sevis_payment', ''),
                            'Agent': st.session_state.get('Agent', ''),
                            'Application payment ?': st.session_state.get('application_payment', ''),
                        }
                    
                        # Update the data in the DataFrame
                        for key, value in updated_student.items():
                            filtered_data.loc[filtered_data['Student Name'] == student_name, key] = value
                    
                        # Save the updated data back to Google Sheets
                        save_data(filtered_data, spreadsheet_id, 'ALL', student_name)
                        st.success("Changes saved successfully!")
                        
                        # Set a flag to reload data on next run
                        st.session_state['reload_data'] = True
                        
                        # Exit edit mode
                        st.session_state['edit_mode'] = False
                        
                        # Rerun the app to show updated data
                        st.rerun()
                    
            
        
            else:
                st.error("No data available. Please check your Google Sheets connection and data.")
        
            st.markdown("---")
            st.markdown("© 2024 The Us House. All rights reserved.")
        
        if __name__ == "__main__":
            main()

if __name__ == "__main__":
    students_page()

# File: ➕New Student.py

import streamlit as st
from auth import check_password

def new_student_page():
    if check_password():
        st.title("Add New Student")
        import streamlit as st
        import pandas as pd
        from datetime import datetime
        from google.oauth2.service_account import Credentials
        import gspread
        import time
        
        # Use Streamlit secrets for service account info
        SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
        
        # Define the scopes
        SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
        
        # Authenticate and build the Google Sheets service
        @st.cache_resource
        def get_google_sheet_client():
            creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
            return gspread.authorize(creds)
        
        # Function to add a new student to the Google Sheet
        def add_student_to_sheet(student_data):
            client = get_google_sheet_client()
            sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
            sheet.append_row(list(student_data.values()))
        
        # Function to load data from Google Sheets
        @st.cache_data(ttl=5)
        def load_data():
            try:
                client = get_google_sheet_client()
                sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
                expected_headers = ["DATE", "First Name", "Last Name", "Age", "Gender", "Phone N°", "Address", "E-mail", 
                                    "Emergency contact N°", "Chosen School", "Specialite", "Duration", "Payment Amount", 
                                    "Payment Type", "Compte", "Sevis payment ?", "Application payment ?", "DS-160 maker", 
                                    "Password DS-160", "Secret Q.", "School Entry Date", "Entry Date in the US", 
                                    "ADDRESS in the U.S", "E-MAIL RDV", "PASSWORD RDV", "EMBASSY ITW. DATE", "Attempts", 
                                    "Visa Result", "Agent", "Note", "Stage", "BANK", "Student Name"]
                data = sheet.get_all_records(expected_headers=expected_headers)
                return pd.DataFrame(data)
            except Exception as e:
                st.error(f"Error loading data from Google Sheet: {e}")
                raise e
        
        # Custom CSS to make the app beautiful and modern
        def load_css():
            st.markdown("""
            <style>
            .stApp {
                background-color: #f0f2f6;
            }
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            h1, h2, h3 {
                color: #1E3A8A;
            }
            .stTextInput, .stSelectbox, .stDateInput, .stTextArea {
                background-color: white;
                color: #2c3e50;
                border-radius: 5px;
                padding: 10px;
                border: 1px solid #bdc3c7;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .stButton>button {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #2980b9;
            }
            .success-message {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 5px;
                animation: fadeIn 0.5s;
            }
            @keyframes fadeIn {
                0% {opacity: 0;}
                100% {opacity: 1;}
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Streamlit app
        def main():
            st.set_page_config(page_title="Add New Student", layout="wide")
            load_css()
        
            st.title("🎓 Add New Student")
            st.markdown("Fill in the form below to add a new student to the database.")
        
            # Initialize session state
            if 'form_submitted' not in st.session_state:
                st.session_state.form_submitted = False
            if 'success_message' not in st.session_state:
                st.session_state.success_message = None
        
            # Create form
            with st.form("student_form"):
                col1, col2 = st.columns(2)
        
                with col1:
                    date = st.date_input("📅 Date", datetime.now())
                    first_name = st.text_input("👤 First Name")
                    last_name = st.text_input("👤 Last Name")
                    gender = st.selectbox("⚧ Gender", ["Male", "Female"])
                    phone = st.text_input("📞 Phone Number")
                    address = st.text_input("🏠 Address")
                    email = st.text_input("📧 Email")
                    emergency_contact = st.text_input("🆘 Emergency Contact Number")
        
                with col2:
                    age = st.text_input("👤 Age")
                    school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                                      "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                                      "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
                    chosen_school = st.selectbox("🏫 Chosen School", school_options)
                    specialite = st.text_input("📚 Specialite")
                    duration = st.text_input("⏳ Duration")
                    payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
                    payment_amount = st.selectbox("💰 Payment Amount", payment_amount_options)
                    payment_type = st.selectbox("💳 Payment Type", ["Cash", "CCP", "Baridimob", "Bank"])
                    compte = st.selectbox("🏦 Compte", ["Mohamed", "Sid Ali"])
                    agent_options = ["Nesrine", "Hamza", "Djazila"]
                    agent = st.selectbox("👨‍💼 Agent", agent_options)
        
                submit_button = st.form_submit_button("Add Student")
        
            if submit_button:
                # Show a spinner while processing
                with st.spinner('Adding student to database...'):
                    # Prepare student data
                    student_data = {
                        "DATE": date.strftime("%d/%m/%Y %H:%M:%S"),
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Age": age,
                        "Gender": gender,
                        "Phone N°": phone,
                        "Address": address,
                        "E-mail": email,
                        "Emergency contact N°": emergency_contact,
                        "Chosen School": chosen_school,
                        "Specialite": specialite,
                        "Duration": duration,
                        "BANK": "",
                        "Payment Amount": payment_amount,
                        "Payment Type": payment_type,
                        "Compte": compte,
                        "Sevis payment ?": "NO",
                        "Application payment ?": "NO",
                        "DS-160 maker": "",
                        "Password DS-160": "",
                        "Secret Q.": "",
                        "School Entry Date": "",
                        "Entry Date in the US": "",
                        "ADDRESS in the U.S": "",
                        "E-MAIL RDV": "",
                        "PASSWORD RDV": "",
                        "EMBASSY ITW. DATE": "",
                        "Attempts": "1st Try",
                        "Visa Result": "",
                        "Agent": agent,
                        "Prep ITW": "NO",
                        "School Paid": "NO",
                        "Visa Result": "",
                        "Note": "",
                        "Stage": "PAYMENT & MAIL",
                        "BANK": "",
                        "Student Name": f"{first_name} {last_name}"
                    }
        
                    # Add student to sheet
                    add_student_to_sheet(student_data)
                    time.sleep(1)  # Simulate processing time
        
                # Set success message
                st.session_state.success_message = f"✅ Student {first_name} {last_name} added successfully!"
                st.session_state.form_submitted = True
        
                # Clear the form by resetting the session state
                for key in st.session_state.keys():
                    if key not in ['form_submitted', 'success_message']:
                        del st.session_state[key]
        
                # Rerun the app to show the success message and clear the form
                st.rerun()
        
            # Display success message if it exists
            if st.session_state.success_message:
                st.markdown(f'<p class="success-message">{st.session_state.success_message}</p>', unsafe_allow_html=True)
                st.session_state.success_message = None  # Clear the message after displaying
        
            # Display the latest data
            st.subheader("Latest Students")
            data = load_data()
            st.dataframe(data.tail(5))  # Show the last 5 entries
        
        if __name__ == "__main__":
            main()

if __name__ == "__main__":
    new_student_page()

