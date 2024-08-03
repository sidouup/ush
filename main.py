import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime, timedelta

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
@st.cache_data(ttl=600)
def load_data(spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Convert 'DATE' column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce', format='%d/%m/%Y %H:%M:%S')
    
    # Convert 'EMBASSY ITW. DATE' to datetime, handling potential errors
    df['EMBASSY ITW. DATE'] = pd.to_datetime(df['EMBASSY ITW. DATE'], errors='coerce', format='%d/%m/%Y %H:%M:%S')
    
    return df

def main_dashboard():
    st.set_page_config(page_title="The Us House - Dashboard", layout="wide")

    # Custom CSS for modern and elegant design
    st.markdown("""
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #3B82F6;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
    }
    .chart-container {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    # App title and logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png", width=150)
        st.markdown("<h1 class='main-title'>The Us House Dashboard</h1>", unsafe_allow_html=True)

    # Load data
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    data = load_data(spreadsheet_id, "ALL")

    # Key Metrics
    st.markdown("<h2 class='sub-title'>Key Metrics</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_students = len(data)
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{total_students}</p>
            <p class='metric-label'>Total Students</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        active_applications = len(data[data['Stage'] != 'CLIENTS'])
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{active_applications}</p>
            <p class='metric-label'>Active Applications</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        visa_approved = len(data[data['Visa Result'] == 'Approved'])
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{visa_approved}</p>
            <p class='metric-label'>Visas Approved</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        now = pd.Timestamp.now()
        upcoming_interviews = len(data[
            (data['EMBASSY ITW. DATE'] > now) & 
            (data['EMBASSY ITW. DATE'] <= now + pd.Timedelta(days=30)) &
            (~data['EMBASSY ITW. DATE'].isna())
        ])
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{upcoming_interviews}</p>
            <p class='metric-label'>Upcoming Interviews (30 days)</p>
        </div>
        """, unsafe_allow_html=True)

    # Charts
    st.markdown("<h2 class='sub-title'>Analytics</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("Application Stages")
        stage_counts = data['Stage'].value_counts()
        fig = px.pie(values=stage_counts.values, names=stage_counts.index, title="Application Stages")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("Top 5 Chosen Schools")
        school_counts = data['Chosen School'].value_counts().nlargest(5)
        fig = px.bar(x=school_counts.index, y=school_counts.values, title="Top 5 Chosen Schools")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Recent Activity
    st.markdown("<h2 class='sub-title'>Recent Activity</h2>", unsafe_allow_html=True)
    recent_activity = data.sort_values('DATE', ascending=False).head(5)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.dataframe(recent_activity[['DATE', 'Student Name', 'Chosen School', 'Stage']], hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Quick Actions
    st.markdown("<h2 class='sub-title'>Quick Actions</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Add New Student"):
            st.switch_page("pages/New_Student.py")
    with col2:
        if st.button("👥 View Student List"):
            st.switch_page("pages/GoogleSheet.py")
    with col3:
        if st.button("📊 View Statistics"):
            st.switch_page("pages/Statistics.py")
    with col4:
        if st.button("🔍 Search Students"):
            st.switch_page("pages/Students.py")

if __name__ == "__main__":
    main_dashboard()
