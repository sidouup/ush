import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
st.set_page_config(page_title="Student Application Tracker", layout="wide")

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
    }
    .stExpander {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
</style>
""", unsafe_allow_html=True)

# Main title with logo
st.markdown("""
    <div style="display: flex; align-items: center;">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
        <h1 style="color: #1E3A8A;">Student Application Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

st.write("Welcome to the Student Application Tracker. The data is fetched from Google Sheets.")

# Function to load data from Google Sheets
@st.cache_resource
def load_data_from_sheets():
    creds = None
    if "token" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["token"])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                {"installed": st.secrets["oauth_credentials"]},
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            
            st.write("Please visit this URL to authorize the application:")
            st.markdown(f"[Authorization URL]({auth_url})")
            
            code = st.text_input("Enter the authorization code:")
            if code:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state["token"] = creds.to_json()

    if creds:
        service = build("sheets", "v4", credentials=creds)
        sheet_id = st.secrets["private_gsheets_url"].split("/")[5]
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:ZZ1000").execute()
        data = result.get("values", [])

        df = pd.DataFrame(data[1:], columns=data[0])
        df['Student Name'] = df['First Name'] + " " + df['Last Name']
        df.dropna(subset=['Student Name'], inplace=True)
        df.dropna(how='all', inplace=True)
        
        return df
    else:
        return None

# Load data
try:
    data = load_data_from_sheets()
    if data is not None:
        st.session_state['data'] = data
        st.success("Data loaded successfully from Google Sheets!")
    else:
        st.warning("Please authorize the application to access Google Sheets.")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")


# Utility functions
def get_visa_status(result):
    result_mapping = {
        'Denied': 'Denied',
        'Approved': 'Approved',
        'Not our school partner': 'Not our school partner',
    }
    return result_mapping.get(result, 'Unknown')

def calculate_days_until_interview(interview_date):
    try:
        interview_date = pd.to_datetime(interview_date, format='%d/%m/%Y', errors='coerce')
        if pd.isnull(interview_date):
            return None
        today = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
        days_remaining = (interview_date - today).days
        return days_remaining
    except Exception as e:
        return None

# Footer
st.markdown("---")
st.markdown("© 2024 The Us House. All rights reserved.")
