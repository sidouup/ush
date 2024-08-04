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

# Rule 1: School payment 40 days before school entry
data['School Payment Due'] = data['School Entry Date'] - timedelta(days=40)
rule_1 = data[(data['School Paid'] != 'Yes') & (data['School Payment Due'] > today)].sort_values(by='DATE').reset_index(drop=True)

# Rule 2: DS-160 step 30 days before embassy interview
ds_160_stages = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep', 'CLIENTS']
data['DS-160 Due'] = data['EMBASSY ITW. DATE'] - timedelta(days=30)
rule_2 = data[(data['Stage'].isin(ds_160_stages[:5])) & (data['DS-160 Due'] > today)].sort_values(by='DATE').reset_index(drop=True)

# Rule 3: Embassy interview in less than 7 days and stage is not CLIENT or SEVIS payment is NO
rule_3a = data[(data['EMBASSY ITW. DATE'] > today) & (data['EMBASSY ITW. DATE'] <= today + timedelta(days=7)) & (data['Stage'] != 'CLIENT') & (data['Stage'] != 'CLIENTS')].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)
rule_3b = data[(data['EMBASSY ITW. DATE'] > today) & (data['EMBASSY ITW. DATE'] <= today + timedelta(days=7)) & (data['Sevis payment ?'] == 'NO')].sort_values(by='EMBASSY ITW. DATE').reset_index(drop=True)

# Rule 4: One week after DATE and School Entry Date is still empty, exclude clients with stage 'CLIENTS'
rule_4 = data[(data['DATE'] <= today - timedelta(days=7)) & (data['School Entry Date'].isna()) & (data['Stage'] != 'CLIENTS')].sort_values(by='DATE').reset_index(drop=True)

# Rule 5: Two weeks after DATE and EMBASSY ITW. DATE is still empty, exclude clients with stage 'CLIENTS'
rule_5 = data[(data['DATE'] <= today - timedelta(days=14)) & (data['EMBASSY ITW. DATE'].isna()) & (data['Stage'] != 'CLIENTS')].sort_values(by='DATE').reset_index(drop=True)

# Streamlit UI
st.title("Task Dashboard")

st.header("Tasks Due")
st.subheader("Rule 1: School payment due")
st.dataframe(rule_1)

st.subheader("Rule 2: DS-160 step due")
st.dataframe(rule_2)

st.subheader("Rule 3a: Embassy interview soon (Stage is not CLIENT)")
st.dataframe(rule_3a)

st.subheader("Rule 3b: Embassy interview soon (Sevis payment is NO)")
st.dataframe(rule_3b)

st.subheader("Rule 4: School Entry Date missing after one week")
st.dataframe(rule_4)

st.subheader("Rule 5: Embassy interview date missing after two weeks")
st.dataframe(rule_5)
