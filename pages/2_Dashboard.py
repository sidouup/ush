import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# The ID of your spreadsheet
SPREADSHEET_ID = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"

@st.cache_resource
def get_google_sheet_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    return gspread.authorize(creds)

def load_sheet(sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet(sheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def main():
    # Set page config
    st.set_page_config(page_title="View Google Sheets", layout="wide")

    # Custom CSS
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
    </style>
    """, unsafe_allow_html=True)

    # Main title with logo
    st.markdown("""
        <div style="display: flex; align-items: center;">
            <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
            <h1 style="color: #1E3A8A;">View Google Sheets</h1>
        </div>
        """, unsafe_allow_html=True)

    st.header("📄 Select a Sheet to View")

    client = get_google_sheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID)

    sheet_names = [ws.title for ws in sheet.worksheets()]
    selected_sheet = st.selectbox("Choose a sheet to view", sheet_names)

    if selected_sheet:
        data = load_sheet(selected_sheet)
        if not data.empty:
            st.dataframe(data)
        else:
            st.info("No data available in this sheet.")

    # Footer
    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()
