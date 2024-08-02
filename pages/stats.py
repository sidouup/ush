import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure
from google.oauth2.service_account import Credentials
import gspread

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

def filter_data_by_date(data, start_date, end_date):
    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
    return data[(data['DATE'] >= start_date) & (data['DATE'] <= end_date)]

def statistics_page():
    st.set_page_config(page_title="Student Recruitment Statistics", layout="wide")
    
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
        .stMetric {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Student Recruitment Statistics")

    # Load data from Google Sheets
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    sheet_name = "ALL"
    data = load_data(spreadsheet_id, sheet_name)

    # Date filter options
    st.sidebar.subheader("Filter by Date")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime(data['DATE'].min()))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime(data['DATE'].max()))
    filtered_data = filter_data_by_date(data, start_date, end_date)

    # Calculate visa approval rate
    visa_approved = len(filtered_data[filtered_data['Visa Result'] == 'Visa Approved'])
    visa_denied = len(filtered_data[filtered_data['Visa Result'] == 'Visa Denied'])
    visa_not_yet = len(filtered_data[filtered_data['Visa Result'] == '0 not yet'])
    visa_not_our_school = len(filtered_data[filtered_data['Visa Result'] == 'not our school'])
    total_decisions = visa_approved + visa_denied
    visa_approval_rate = (visa_approved / total_decisions * 100) if total_decisions > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        total_students = len(filtered_data)
        st.metric("Total Students", total_students)

    with col2:
        st.metric("Visa Approvals", visa_approved)

    with col3:
        st.metric("Visa Approval Rate", f"{visa_approval_rate:.2f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏫 Top Chosen Schools")
        school_counts = filtered_data['Chosen School'].value_counts().head(10)
        fig = px.bar(school_counts, x=school_counts.index, y=school_counts.values,
                     labels={'y': 'Number of Students', 'x': 'School'},
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
        attempts_counts = filtered_data['Attempts'].value_counts()
        fig = px.bar(attempts_counts, x=attempts_counts.index, y=attempts_counts.values,
                     labels={'y': 'Number of Students', 'x': 'Attempt'},
                     title="Application Attempts Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🏆 Top Performing Agents")
    agent_performance = filtered_data['Agent'].value_counts().head(5)
    fig = px.bar(agent_performance, x=agent_performance.index, y=agent_performance.values,
                 labels={'y': 'Number of Students', 'x': 'Agent'},
                 title="Top 5 Agents by Number of Students")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    statistics_page()
