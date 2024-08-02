import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials

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

# Function to apply filters
def apply_filters(df, filters):
    for column, value in filters.items():
        if value != "All":
            df = df[df[column] == value]
    return df

# Main function for the new page
def main():
    st.set_page_config(page_title="Student List", layout="wide")

    st.title("Student List")

    # Load data from Google Sheets
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    sheet_name = "ALL"
    df_all = load_data(spreadsheet_id, sheet_name)

    # Define filter options
    columns_to_filter = ["First Name", "Last Name", "Chosen School", "Specialite", "Duration", "Agent", "Stage"]
    filter_options = {col: ["All"] + df_all[col].dropna().unique().tolist() for col in columns_to_filter}

    # Create filter widgets
    filters = {}
    for col, options in filter_options.items():
        filters[col] = st.sidebar.selectbox(f"Filter by {col}", options)

    # Apply filters
    filtered_data = apply_filters(df_all, filters)

    # Display the data in a table
    st.dataframe(filtered_data)

if __name__ == "__main__":
    main()
