import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Student Application Tracker", layout="wide")

# Custom CSS (unchanged)
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

# Main title with logo (unchanged)
st.markdown("""
    <div style="display: flex; align-items: center;">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
        <h1 style="color: #1E3A8A;">Student Application Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

st.write("Welcome to the Student Application Tracker. The data is fetched from Google Sheets.")

@st.cache_resource
def load_data_from_sheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    
    service = build("sheets", "v4", credentials=credentials)
    sheet_id = st.secrets["private_gsheets_url"].split("/")[5]
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:ZZ1000").execute()
    data = result.get("values", [])
    
    if not data:
        st.error("No data found in the Google Sheet.")
        return None
    
    # Get the header row
    headers = data[0]
    
    # Create DataFrame with dynamic column names
    df = pd.DataFrame(data[1:])
    
    # Assign column names and handle potential mismatch
    if len(df.columns) != len(headers):
        st.warning(f"Mismatch between number of columns in data ({len(df.columns)}) and headers ({len(headers)}). Using available columns.")
        # Use the minimum length to avoid index errors
        min_length = min(len(df.columns), len(headers))
        df.columns = headers[:min_length]
        # If there are more columns in data than headers, name them generically
        if len(df.columns) > min_length:
            for i in range(min_length, len(df.columns)):
                df.columns.values[i] = f"Column_{i+1}"
    else:
        df.columns = headers
    
    df.dropna(how='all', inplace=True)
    
    return df

try:
    data = load_data_from_sheets()
    if data is not None:
        st.session_state['data'] = data
        st.success("Data loaded successfully from Google Sheets!")
        
        # Display summary statistics
        st.subheader("Summary Statistics")
        total_students = len(data)
        
        # Check if 'Visa Result' column exists
        if 'Visa Result' in data.columns:
            pending_applications = data[data['Visa Result'].isnull()].shape[0]
            approved_visas = data[data['Visa Result'].str.lower() == 'approved'].shape[0]
            denied_visas = data[data['Visa Result'].str.lower() == 'denied'].shape[0]
        else:
            pending_applications = approved_visas = denied_visas = "N/A"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", total_students)
        col2.metric("Pending Applications", pending_applications)
        col3.metric("Approved Visas", approved_visas)
        col4.metric("Denied Visas", denied_visas)

        # Display data table with filters
        st.subheader("Student Application Data")
        
        # Filters
        if 'Chosen School' in data.columns:
            chosen_school = st.multiselect("Filter by School", options=sorted(data['Chosen School'].dropna().unique()))
        if 'Visa Result' in data.columns:
            visa_result = st.multiselect("Filter by Visa Result", options=sorted(data['Visa Result'].dropna().unique()))
        
        filtered_data = data
        if 'Chosen School' in data.columns and chosen_school:
            filtered_data = filtered_data[filtered_data['Chosen School'].isin(chosen_school)]
        if 'Visa Result' in data.columns and visa_result:
            filtered_data = filtered_data[filtered_data['Visa Result'].isin(visa_result)]
        
        st.dataframe(filtered_data)

        # Display individual student details
        st.subheader("Individual Student Details")
        if 'First Name' in data.columns and 'Last Name' in data.columns:
            selected_student = st.selectbox("Select a student", options=data['First Name'] + " " + data['Last Name'])
            if selected_student:
                student_data = data[(data['First Name'] + " " + data['Last Name']) == selected_student].iloc[0]
                for column in student_data.index:
                    if pd.notnull(student_data[column]):
                        st.write(f"**{column}:** {student_data[column]}")
        else:
            st.write("Unable to display individual student details due to missing name columns.")

    else:
        st.error("Failed to load data from Google Sheets.")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    st.stop()

# Footer
st.markdown("---")
st.markdown("© 2024 The Us House. All rights reserved.")

