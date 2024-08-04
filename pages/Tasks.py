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
st.title("Task Dashboard")

st.header("School Payment Due Soon")
st.write("These students need to complete their school payment at least 40 days before their school entry date.")
st.dataframe(rule_1)

st.header("DS-160 Step Due Soon")
st.write("These students need to complete the DS-160 step within 30 days before their embassy interview date.")
st.dataframe(rule_2)

st.header("Upcoming Embassy Interviews (Need Prep)")
st.write("These students have embassy interviews scheduled within the next 14 days and they are not prepared yet.")
st.dataframe(rule_3a)

st.header("Upcoming Embassy Interviews (SEVIS Payment NO)")
st.write("These students have embassy interviews scheduled within the next 14 days and they did not pay the SEVIS.")
st.dataframe(rule_3b)

st.header("I-20 and school registration Needed")
st.write("These students do not have a school entry date recorded one week after the Payment date, They Need an I20 and Mention their Entry Date in the DATABASE.")
st.dataframe(rule_4)

st.header("Embassy Interview Date Missing (After Two Weeks)")
st.write("These students do not have an embassy interview date recorded two weeks after the initial date, and their stage is not CLIENTS.")
st.dataframe(rule_5)
