import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load data from Google Sheets
def load_data(spreadsheet_id):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id)
    worksheets = sheet.worksheets()
    combined_data = pd.DataFrame()

    for worksheet in worksheets:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        df['Worksheet'] = worksheet.title
        combined_data = pd.concat([combined_data, df], ignore_index=True)

    return combined_data

# Main function for the statistics page
def statistics_page():
    st.set_page_config(page_title="Student Application Statistics", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

    st.title("Student Application Statistics")
    st.markdown("### Overview of Student Applications")

    spreadsheet_id = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"
    data = load_data(spreadsheet_id)

    if not data.empty:
        # Basic statistics
        st.subheader("Basic Statistics")
        st.write("Total Applications:", len(data))
        st.write("Applications by Current Step:")
        step_counts = data['Worksheet'].value_counts()
        st.write(step_counts)

        # Bar chart of applications by step
        st.subheader("Applications by Step")
        step_chart = px.bar(step_counts, x=step_counts.index, y=step_counts.values, labels={'index': 'Step', 'y': 'Number of Applications'})
        st.plotly_chart(step_chart)

        # Pie chart of visa results
        st.subheader("Visa Results Distribution")
        visa_results = data['Visa Result'].value_counts()
        visa_chart = px.pie(visa_results, names=visa_results.index, values=visa_results.values, labels={'index': 'Visa Result', 'y': 'Count'})
        st.plotly_chart(visa_chart)

        # Time series chart of applications over time
        st.subheader("Applications Over Time")
        data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
        applications_over_time = data.set_index('DATE').resample('M').size()
        time_chart = px.line(applications_over_time, labels={'index': 'Date', 'value': 'Number of Applications'})
        st.plotly_chart(time_chart)
    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

if __name__ == "__main__":
    statistics_page()
