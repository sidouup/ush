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
    st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
        color: #1E88E5;
    }
    .medium-font {
        font-size:20px !important;
        font-weight: bold;
        color: #43A047;
    }
    .small-font {
        font-size:14px !important;
        color: #212121;
    }
    .highlight {
        background-color: #FFF176;
        padding: 5px;
        border-radius: 5px;
    }
    .dataframe {
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">📋 Tasks and Emergencies Dashboard</p>', unsafe_allow_html=True)

    # Load data
    data = load_data("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI")
    
    today = datetime.now()

    # 1. List of students sorted by embassy appointment date (future dates only)
    st.markdown('<p class="medium-font">🗓️ Students Sorted by Upcoming Embassy Appointment Date</p>', unsafe_allow_html=True)
    embassy_sorted = data[data['EMBASSY ITW. DATE'] > today].sort_values('EMBASSY ITW. DATE')
    st.dataframe(embassy_sorted[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=300)

    # 2. List of students sorted by school entry date (future dates only)
    st.markdown('<p class="medium-font">🏫 Students Sorted by Upcoming School Entry Date</p>', unsafe_allow_html=True)
    school_sorted = data[data['School Entry Date'] > today].sort_values('School Entry Date')
    st.dataframe(school_sorted[['Student Name', 'School Entry Date', 'Chosen School']], height=300)

    # 3. Students with school entry date within the next 40 days
    st.markdown('<p class="medium-font">⏰ Students with School Entry Date in the Next 40 Days</p>', unsafe_allow_html=True)
    forty_days = today + timedelta(days=40)
    upcoming_entry = data[
        (data['School Entry Date'] > today) &
        (data['School Entry Date'] <= forty_days)
    ].sort_values('School Entry Date')
    st.dataframe(upcoming_entry[['Student Name', 'School Entry Date', 'Chosen School', 'Stage']], height=300)

    # 4. Students with appointment in 30 days but not past DS-160 stage
    st.markdown('<p class="medium-font">🚨 Urgent: Appointment in 30 days, DS-160 Not Completed</p>', unsafe_allow_html=True)
    thirty_days = today + timedelta(days=30)
    urgent_ds160 = data[
        (data['EMBASSY ITW. DATE'] <= thirty_days) &
        (data['EMBASSY ITW. DATE'] >= today) &
        (data['Stage'].isin(['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV']))
    ]
    st.dataframe(urgent_ds160[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=300)

    # 5. Applicants without a school entry date
    st.markdown('<p class="medium-font">❓ Applicants Without School Entry Date</p>', unsafe_allow_html=True)
    no_entry_date = data[data['School Entry Date'].isna()]
    st.dataframe(no_entry_date[['Student Name', 'Chosen School', 'Stage']], height=300)

    # 6. Additional Important Information
    st.markdown('<p class="medium-font">ℹ️ Additional Important Information</p>', unsafe_allow_html=True)

    # Students with upcoming embassy interviews (next 15 days)
    st.markdown('<p class="small-font">🗺️ Upcoming Embassy Interviews (Next 15 Days)</p>', unsafe_allow_html=True)
    fifteen_days = today + timedelta(days=15)
    upcoming_interviews = data[
        (data['EMBASSY ITW. DATE'] <= fifteen_days) &
        (data['EMBASSY ITW. DATE'] >= today)
    ]
    st.dataframe(upcoming_interviews[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=300)

    # Students in final stages without visa results
    st.markdown('<p class="small-font">🏁 Students in Final Stages Without Visa Results</p>', unsafe_allow_html=True)
    final_stages = data[
        (data['Stage'].isin(['ITW Prep.', 'SEVIS'])) &
        (data['Visa Result'].isna() | (data['Visa Result'] == ''))
    ]
    st.dataframe(final_stages[['Student Name', 'Stage', 'EMBASSY ITW. DATE']], height=300)

    # 7. Duplicate Students
    st.markdown('<p class="medium-font">👥 Duplicate Students</p>', unsafe_allow_html=True)
    duplicates = data[data.duplicated(subset=['Student Name'], keep=False)]
    if not duplicates.empty:
        st.dataframe(duplicates[['Student Name', 'DATE', 'Stage']], height=300)
        st.markdown('<p class="small-font highlight">⚠️ Please review and resolve these duplicate entries in the "ALL" sheet.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="small-font">✅ No duplicate students found.</p>', unsafe_allow_html=True)

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
