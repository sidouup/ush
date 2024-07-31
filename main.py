import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import GSpreadException

# Use Streamlit secrets to load credentials
credentials_dict = {
    "type": st.secrets["gcp_service_account"]["type"],
    "project_id": st.secrets["gcp_service_account"]["project_id"],
    "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
    "private_key": st.secrets["gcp_service_account"]["private_key"],
    "client_email": st.secrets["gcp_service_account"]["client_email"],
    "client_id": st.secrets["gcp_service_account"]["client_id"],
    "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri": st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
}

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
client = gspread.authorize(credentials)

# URL to the Google Sheet
sheet_url = st.secrets["private_gsheets_url"]["url"]
spreadsheet = client.open_by_url(sheet_url)

# Get all the worksheets in the spreadsheet
worksheets = spreadsheet.worksheets()

st.title("Google Sheet Viewer")

# Display the content of each worksheet
for worksheet in worksheets:
    st.header(worksheet.title)
    try:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except GSpreadException as e:
        st.error(f"Error in worksheet '{worksheet.title}': {e}")
        # Attempt to fix by manually setting expected headers if known
        headers = worksheet.row_values(1)
        data = worksheet.get_all_records(expected_headers=headers)
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"An unexpected error occurred in worksheet '{worksheet.title}': {e}")
        continue
    st.dataframe(df)

# Adding a less frequent health check (this might not be necessary on Streamlit Share)
st.set_option('server.healthCheckInterval', 10000)
