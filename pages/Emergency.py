import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# Set page config at the very beginning
st.set_page_config(layout="wide", page_title="Student Visa CRM Dashboard",
    initial_sidebar_state="collapsed")

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

# Custom CSS for a modern look with 3D effect
import streamlit as st

# Custom CSS for improved tab styling
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Set page config
st.set_page_config(layout="wide", page_title="Student Visa CRM Dashboard")

# Custom CSS for a modern and beautiful design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background-color: #f0f4f8;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #1a237e;
    }
    
    .stTabs {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 10px 20px;
        font-weight: 600;
        background-color: #e8eaf6;
        color: #3f51b5;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3f51b5;
        color: #ffffff;
    }
    
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #3f51b5;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #757575;
        margin-top: 5px;
    }
    
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background-color: #3f51b5;
        color: white;
        font-weight: 600;
        text-align: left;
        padding: 12px;
    }
    
    .dataframe td {
        background-color: #ffffff;
        padding: 12px;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f8f8f8;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a237e;
        margin: 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
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

# Detailed sections in tabs
tabs = st.tabs([
    "School Payment",
    "DS-160",
    "Interviews",
    "SEVIS Payment",
    "I-20 & Registration",
    "ITW Date",
    "Visa Result"
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
    st.markdown('<div class="section-header">📅 ITW Date Needed</div>', unsafe_allow_html=True)
    st.write("These students do not have an embassy interview date recorded two weeks after their initial registration date. They need to schedule their interview and update the database.")
    st.dataframe(rule_5[['First Name', 'Last Name', 'DATE', 'Stage', 'Agent']], use_container_width=True)

with tabs[6]:
    st.markdown('<div class="section-header">❓ Visa Result Needed</div>', unsafe_allow_html=True)
    st.write("These students have passed their embassy interview date and still do not have a recorded visa result. Please update their visa result.")
    st.dataframe(rule_6[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)

