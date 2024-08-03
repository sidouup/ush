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
    .stButton>button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .centered-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # App title and logo
    st.markdown("""
    <div class="centered-content">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" width="150">
        <h1 class='main-title'>The Us House Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    data = load_data(spreadsheet_id, "ALL")

    # Remove duplicates for analysis
    data_deduped = data.drop_duplicates(subset=['Student Name', 'Chosen School'], keep='last')
    
    # Remove rows with NaT values in the DATE column for further analysis
    data_clean = data_deduped.dropna(subset=['DATE'])

    # Key Metrics
    st.markdown("<h2 class='sub-title'>Key Metrics</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        total_students = len(data_clean)
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{total_students}</p>
            <p class='metric-label'>Total Unique Students</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        overall_approval_rate, visa_approved, total_decisions = calculate_visa_approval_rate(data_clean)
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{visa_approved}</p>
            <p class='metric-label'>Visa Approvals</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{overall_approval_rate:.2f}%</p>
            <p class='metric-label'>Visa Approval Rate</p>
        </div>
        """, unsafe_allow_html=True)

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

    # Charts
    st.markdown("<h2 class='sub-title'>Analytics</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🏫 Top Chosen Schools")
        school_counts = data_clean['Chosen School'].value_counts().head(10).reset_index()
        school_counts.columns = ['School', 'Number of Students']
        fig = px.bar(school_counts, x='School', y='Number of Students',
                     labels={'Number of Students': 'Number of Students', 'School': 'School'},
                     title="Top 10 Chosen Schools")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🛂 Student Visa Approval")
        visa_status = data_clean['Visa Result'].value_counts()
        colors = {'Visa Approved': 'blue', 'Visa Denied': 'red', '0 not yet': 'grey', 'not our school': 'lightblue'}
        fig = px.pie(values=visa_status.values, names=visa_status.index,
                     title="Visa Application Results", color=visa_status.index, 
                     color_discrete_map=colors)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Recent Activity
    st.markdown("<h2 class='sub-title'>Recent Activity</h2>", unsafe_allow_html=True)
    recent_activity = data_clean.sort_values('DATE', ascending=False).head(5)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.dataframe(recent_activity[['DATE', 'Student Name', 'Chosen School', 'Stage']], hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main_dashboard()
