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

# Custom CSS for a modern look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    .stApp {
        background-color: #f0f2f6;
    }
    
    .main {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    h1 {
        color: #1E88E5;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 20px;
    }
    
    .section-header {
        font-size: 2rem;
        font-weight: 600;
        color: #1E88E5;
        margin: 20px 0;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    .metric-card h2 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #1E88E5;
    }
    
    .metric-card p {
        font-size: 2rem;
        font-weight: 700;
        color: #333;
    }
    
    .dataframe {
        font-size: 0.9rem;
    }
    
    .dataframe th {
        background-color: #1E88E5;
        color: white;
        font-weight: 500;
        text-align: left;
    }
    
    .dataframe td {
        background-color: #ffffff;
    }
    
    .icon {
        font-size: 1.5rem;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Student Visa CRM Dashboard")

# Overview metrics
st.markdown("### Overview")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

def metric_card(title, value, icon):
    return f"""
    <div class="metric-card">
        <h2>{icon} {title}</h2>
        <p>{value}</p>
    </div>
    """

with col1:
    st.markdown(metric_card("School Payments Due", len(rule_1), "📅"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("Emergency DS-160", len(rule_2), "📝"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("Emergency Interviews", len(rule_3a), "🎤"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("Emergency SEVIS Payment", len(rule_3b), "💳"), unsafe_allow_html=True)
with col5:
    st.markdown(metric_card("Visa Result Needed", len(rule_6), "❓"), unsafe_allow_html=True)
with col6:
    st.markdown(metric_card("I-20s Needed", len(rule_4), "📄"), unsafe_allow_html=True)
with col7:
    st.markdown(metric_card("Embassy Interviews Needed", len(rule_5), "📅"), unsafe_allow_html=True)

# Detailed sections
st.markdown("### Detailed Information")

# School Payment Due Soon
st.markdown('<div class="section-header">📅 School Payment Due Soon</div>', unsafe_allow_html=True)
st.write("These students need to complete their school payment at least 50 days before their school entry date.")
st.dataframe(rule_1[['First Name', 'Last Name', 'DATE', 'School Payment Due', 'Stage', 'Agent']], use_container_width=True)

# DS-160 Step Due Soon
st.markdown('<div class="section-header">📝 DS-160 Step Due Soon</div>', unsafe_allow_html=True)
st.write("These students need to complete the DS-160 step within 30 days before their embassy interview date.")
st.dataframe(rule_2[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)

# Upcoming Embassy Interviews (Need Prep)
st.markdown('<div class="section-header">🎤 Upcoming Embassy Interviews (Need Prep)</div>', unsafe_allow_html=True)
st.write("These students have embassy interviews scheduled within the next 14 days and they are not prepared yet.")
st.dataframe(rule_3a[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)

# Need SEVIS Payment
st.markdown('<div class="section-header">💳 Need SEVIS Payment</div>', unsafe_allow_html=True)
st.write("These students have embassy interviews scheduled within the next 14 days and they did not pay the SEVIS.")
st.dataframe(rule_3b[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)

# I-20 and School Registration Needed
st.markdown('<div class="section-header">❓ I-20 and School Registration Needed</div>', unsafe_allow_html=True)
st.write("These students do not have a school entry date recorded one week after the Payment date. They need an I-20 and must mention their entry date in the database.")
st.dataframe(rule_4[['First Name', 'Last Name', 'DATE', 'Stage', 'Agent']], use_container_width=True)

# Embassy Interview Date Missing (After Two Weeks)
st.markdown('<div class="section-header">❓ Embassy Interview Date Missing (After Two Weeks)</div>', unsafe_allow_html=True)
st.write("These students do not have an embassy interview date recorded two weeks after the initial date, and their stage is not CLIENTS.")
st.dataframe(rule_5[['First Name', 'Last Name', 'DATE', 'Stage', 'Agent']], use_container_width=True)

# Visa Result Needed
st.markdown('<div class="section-header">❓ Visa Result Needed</div>', unsafe_allow_html=True)
st.write("These students have passed their embassy interview date and still do not have a recorded visa result. Please update their visa result.")
st.dataframe(rule_6[['First Name', 'Last Name', 'DATE', 'EMBASSY ITW. DATE', 'Stage', 'Agent']], use_container_width=True)
