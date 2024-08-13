import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the required scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate with Google Sheets
def get_gsheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

client = get_gsheet_client()

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI/edit?gid=693781323#gid=693781323"

# Function to load data from Google Sheets
def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y %H:%M:%S', errors='coerce')  # Convert DATE to datetime with dayfirst=True
    df['Months'] = df['DATE'].dt.strftime('%B %Y')  # Create a new column 'Months' for filtering
    return df

# Function to save data to Google Sheets
def save_data(df, edited_df, spreadsheet_url):
    logger.info("Attempting to save changes")
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        sheet = spreadsheet.sheet1
        
        # Identify the modified rows
        modified_rows = df[df.ne(edited_df)].dropna(how='all')
        
        if modified_rows.empty:
            logger.info("No changes detected.")
            return False
        
        # Ensure the correct date format for "School Entry Date" and "Entry Date in the US"
        date_columns = ["School Entry Date", "Entry Date in the US"]
        for col in date_columns:
            if col in modified_rows.columns:
                modified_rows[col] = pd.to_datetime(modified_rows[col], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                modified_rows[col] = modified_rows[col].dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Replace problematic values with a placeholder
        modified_rows.replace([np.inf, -np.inf, np.nan], 'NaN', inplace=True)

        # Update the specific rows in Google Sheets
        for idx, row in modified_rows.iterrows():
            sheet.update(f"A{idx+2}:Z{idx+2}", [row.tolist()])  # Update the row with changes

        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False


# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.original_data = st.session_state.data.copy()  # Keep a copy of the original data
    st.session_state.reload_data = False

# Display the editable dataframe
st.title("Student List")

# Filters
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    agents = ["All", "Nesrine", "Hamza", "Djazila", "Nada"]
    selected_agents = st.multiselect('Filter by Agent', options=agents)

with col2:
    # Sort months chronologically
    all_months = sorted(st.session_state.data['Months'].unique(), 
                        key=lambda x: datetime.strptime(x, '%B %Y'))
    months_years = ["All"] + list(all_months)
    selected_months = st.multiselect('Filter by Month', options=months_years, default=["All"])

with col3:
    stages = ["All", 'PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.', 'CLIENTS']
    selected_stages = st.multiselect('Filter by Stage', options=stages)

with col4:
    school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                      "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                      "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
    selected_schools = st.multiselect('Filter by Chosen School', options=school_options)

with col5:
    attempts_options = ["All", "1 st Try", "2 nd Try", "3 rd Try"]
    selected_attempts = st.multiselect('Filter by Attempts', options=attempts_options)

filtered_data = st.session_state.data.copy()

if selected_agents and "All" not in selected_agents:
    filtered_data = filtered_data[filtered_data['Agent'].isin(selected_agents)]
if selected_months and "All" not in selected_months:
    filtered_data = filtered_data[filtered_data['Months'].isin(selected_months)]
if selected_stages and "All" not in selected_stages:
    filtered_data = filtered_data[filtered_data['Stage'].isin(selected_stages)]
if selected_schools and "All" not in selected_schools:
    filtered_data = filtered_data[filtered_data['Chosen School'].isin(selected_schools)]
if selected_attempts and "All" not in selected_attempts:
    filtered_data = filtered_data[filtered_data['Attempts'].isin(selected_attempts)]

# Sort filtered data for display using DATE as day-first
filtered_data['DATE'] = pd.to_datetime(filtered_data['DATE'], dayfirst=True, errors='coerce')
filtered_data.sort_values(by='DATE', inplace=True)

# Ensure all columns are treated as strings for editing
filtered_data = filtered_data.astype(str)

# Use a key for the data_editor to ensure proper updates
edited_df = st.data_editor(filtered_data, num_rows="dynamic", key="student_data")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        # Ensure correct date format for "School Entry Date" and "Entry Date in the US"
        date_columns = ["School Entry Date", "Entry Date in the US"]
        for col in date_columns:
            if col in edited_df.columns:
                edited_df[col] = pd.to_datetime(edited_df[col], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                edited_df[col] = edited_df[col].dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Save only modified rows
        if save_data(st.session_state.original_data, edited_df, spreadsheet_url):
            st.session_state.data = load_data()  # Reload the data to ensure consistency
            st.success("Changes saved successfully!")
            
            # Use a spinner while waiting for changes to propagate
            with st.spinner("Refreshing data..."):
                time.sleep(2)  # Wait for 2 seconds to allow changes to propagate
            
            st.session_state.reload_data = True
            st.rerun()
        else:
            st.warning("No changes detected or failed to save changes.")
    except Exception as e:
        st.error(f"An error occurred while saving: {str(e)}")
