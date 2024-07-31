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
    /* ... (keep the existing CSS) ... */
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
    
    columns = data[0]
    df = pd.DataFrame(data[1:], columns=columns)
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
        pending_applications = data[data['Visa Result'].isnull()].shape[0]
        approved_visas = data[data['Visa Result'] == 'Approved'].shape[0]
        denied_visas = data[data['Visa Result'] == 'Denied'].shape[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", total_students)
        col2.metric("Pending Applications", pending_applications)
        col3.metric("Approved Visas", approved_visas)
        col4.metric("Denied Visas", denied_visas)

        # Display data table with filters
        st.subheader("Student Application Data")
        
        # Filters
        chosen_school = st.multiselect("Filter by School", options=sorted(data['Chosen School'].unique()))
        visa_result = st.multiselect("Filter by Visa Result", options=sorted(data['Visa Result'].unique()))
        
        filtered_data = data
        if chosen_school:
            filtered_data = filtered_data[filtered_data['Chosen School'].isin(chosen_school)]
        if visa_result:
            filtered_data = filtered_data[filtered_data['Visa Result'].isin(visa_result)]
        
        st.dataframe(filtered_data)

        # Display individual student details
        st.subheader("Individual Student Details")
        selected_student = st.selectbox("Select a student", options=data['First Name'] + " " + data['Last Name'])
        if selected_student:
            student_data = data[data['First Name'] + " " + data['Last Name'] == selected_student].iloc[0]
            st.write(f"**Name:** {student_data['First Name']} {student_data['Last Name']}")
            st.write(f"**Phone:** {student_data['Phone N°']}")
            st.write(f"**Email:** {student_data['E-mail']}")
            st.write(f"**Chosen School:** {student_data['Chosen School']}")
            st.write(f"**Duration:** {student_data['Duration']}")
            st.write(f"**Visa Result:** {student_data['Visa Result']}")

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
