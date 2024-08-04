import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread
import streamlit as st

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

# Convert DATE columns to datetime
data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
data['School Entry Date'] = pd.to_datetime(data['School Entry Date'], errors='coerce')
data['EMBASSY ITW. DATE'] = pd.to_datetime(data['EMBASSY ITW. DATE'], errors='coerce')

# Get today's date
today = datetime.now()

# Apply rules (as in your original code)
# Rule 1: School payment 40 days before school entry
data['School Payment Due'] = data['School Entry Date'] - timedelta(days=40)
rule_1 = data[(data['School Paid'] != 'Yes') & (data['School Payment Due'] > today)].sort_values(by='DATE').reset_index(drop=True)

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

# Streamlit UI
st.set_page_config(layout="wide", page_title="Student Visa CRM Dashboard")

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
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 5px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #1E88E5;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: #ffffff;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
</style>
""", unsafe_allow_html=True)

st.title("Student Visa CRM Dashboard")

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

def metric_card(title, value):
    return f"""
    <div class="metric-card">
        <h2>{title}</h2>
        <p>{value}</p>
    </div>
    """

with col1:
    st.markdown(metric_card("School Payments Due", len(rule_1)), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("DS-160 Due", len(rule_2)), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("Upcoming Interviews", len(rule_3a)), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("Need SEVIS Payment", len(rule_3b)), unsafe_allow_html=True)

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["School Payments", "DS-160", "Interview Prep", "SEVIS Payment", "Missing Info"])

with tab1:
    st.header("School Payment Due Soon")
    st.dataframe(rule_1[['NAME', 'DATE', 'School Payment Due', 'Stage']], use_container_width=True)

with tab2:
    st.header("DS-160 Step Due Soon")
    st.dataframe(rule_2[['NAME', 'DATE', 'EMBASSY ITW. DATE', 'Stage']], use_container_width=True)

with tab3:
    st.header("Upcoming Embassy Interviews (Need Prep)")
    st.dataframe(rule_3a[['NAME', 'DATE', 'EMBASSY ITW. DATE', 'Stage']], use_container_width=True)

with tab4:
    st.header("Need SEVIS Payment")
    st.dataframe(rule_3b[['NAME', 'DATE', 'EMBASSY ITW. DATE', 'Stage']], use_container_width=True)

with tab5:
    st.header("Missing Information")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("I-20 and School Registration Needed")
        st.dataframe(rule_4[['NAME', 'DATE', 'Stage']], use_container_width=True)
    with col2:
        st.subheader("Embassy Interview Date Missing")
        st.dataframe(rule_5[['NAME', 'DATE', 'Stage']], use_container_width=True)
