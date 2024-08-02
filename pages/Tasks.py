import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

def load_data(spreadsheet_id):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(spreadsheet_id).worksheet('ALL')
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Create Student Name column
        df['Student Name'] = df['First Name'] + " " + df['Last Name']
        
        # Parse dates
        date_columns = ['DATE', 'School Entry Date', 'Entry Date in the US', 'EMBASSY ITW. DATE']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
        
        return df
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

def tasks_and_emergencies_page():
    st.title("Tasks and Emergencies")

    # Load data
    data = load_data("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI")

    # 1. List of students sorted by embassy appointment date
    st.header("1. Students Sorted by Embassy Appointment Date")
    embassy_sorted = data.sort_values('EMBASSY ITW. DATE').dropna(subset=['EMBASSY ITW. DATE'])
    st.dataframe(embassy_sorted[['Student Name', 'EMBASSY ITW. DATE', 'Stage']])

    # 2. List of students sorted by school entry date
    st.header("2. Students Sorted by School Entry Date")
    school_sorted = data.sort_values('School Entry Date').dropna(subset=['School Entry Date'])
    st.dataframe(school_sorted[['Student Name', 'School Entry Date', 'Chosen School']])

    # 3. Students with appointment in 30 days but not past DS-160 stage
    st.header("3. Urgent: Appointment in 30 days, DS-160 Not Completed")
    today = datetime.now()
    thirty_days = today + timedelta(days=30)
    urgent_ds160 = data[
        (data['EMBASSY ITW. DATE'] <= thirty_days) &
        (data['EMBASSY ITW. DATE'] >= today) &
        (data['Stage'].isin(['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV']))
    ]
    st.dataframe(urgent_ds160[['Student Name', 'EMBASSY ITW. DATE', 'Stage']])

    # 4. Applicants without a school entry date
    st.header("4. Applicants Without School Entry Date")
    no_entry_date = data[data['School Entry Date'].isna()]
    st.dataframe(no_entry_date[['Student Name', 'Chosen School', 'Stage']])

    # 5. Additional Important Information
    st.header("5. Additional Important Information")

    # Students with upcoming embassy interviews (next 7 days)
    st.subheader("Upcoming Embassy Interviews (Next 7 Days)")
    seven_days = today + timedelta(days=7)
    upcoming_interviews = data[
        (data['EMBASSY ITW. DATE'] <= seven_days) &
        (data['EMBASSY ITW. DATE'] >= today)
    ]
    st.dataframe(upcoming_interviews[['Student Name', 'EMBASSY ITW. DATE', 'Stage']])

    # Students in final stages without visa results
    st.subheader("Students in Final Stages Without Visa Results")
    final_stages = data[
        (data['Stage'].isin(['ITW Prep.', 'SEVIS'])) &
        (data['Visa Result'].isna() | (data['Visa Result'] == ''))
    ]
    st.dataframe(final_stages[['Student Name', 'Stage', 'EMBASSY ITW. DATE']])

def main():
    st.set_page_config(page_title="Student Application Tracker", layout="wide")
    
    # Add a new option in your sidebar or navigation
    page = st.sidebar.selectbox("Choose a page", ["Student Tracker", "Tasks and Emergencies"])
    
    if page == "Student Tracker":
        student_tracker_page()  # Your existing main page function
    elif page == "Tasks and Emergencies":
        tasks_and_emergencies_page()

def student_tracker_page():
    # Your existing student tracker page code here
    # This function should contain all the code for your current main page
    pass

if __name__ == "__main__":
    main()