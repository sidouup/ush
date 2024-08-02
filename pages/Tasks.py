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

def load_data(file_path):
    try:
        # Load data from the provided Excel file
        df = pd.read_excel(file_path, sheet_name='ALL')
        
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

def tasks_and_emergencies_page(df):
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
    .stDataFrame {
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        padding: 1px;
    }
    .dashboard-item {
        background-color: #F5F5F5;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">📋 Tasks and Emergencies Dashboard</p>', unsafe_allow_html=True)

    today = datetime.now()

    # Create a 2-column layout
    col1, col2 = st.columns(2)

    with col1:
        # Urgent matters
        with st.container():
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown('<p class="medium-font">🚨 Urgent Matters</p>', unsafe_allow_html=True)
            
            # Students with appointment in 30 days but not past DS-160 stage
            st.markdown('<p class="small-font">Appointment in 30 days, DS-160 Not Completed</p>', unsafe_allow_html=True)
            thirty_days = today + timedelta(days=30)
            urgent_ds160 = df[
                (df['EMBASSY ITW. DATE'] <= thirty_days) &
                (df['EMBASSY ITW. DATE'] >= today) &
                (df['Stage'].isin(['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV']))
            ]
            st.dataframe(urgent_ds160[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=200)
            st.markdown('</div>', unsafe_allow_html=True)

        # Upcoming Interviews
        with st.container():
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown('<p class="medium-font">🗓️ Upcoming Embassy Interviews (Next 15 Days)</p>', unsafe_allow_html=True)
            fifteen_days = today + timedelta(days=15)
            upcoming_interviews = df[
                (df['EMBASSY ITW. DATE'] <= fifteen_days) &
                (df['EMBASSY ITW. DATE'] >= today)
            ]
            st.dataframe(upcoming_interviews[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=200)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Students with upcoming school entry
        with st.container():
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown('<p class="medium-font">🏫 Students with School Entry Date in the Next 40 Days</p>', unsafe_allow_html=True)
            forty_days = today + timedelta(days=40)
            upcoming_entry = df[
                (df['School Entry Date'] > today) &
                (df['School Entry Date'] <= forty_days)
            ].sort_values('School Entry Date')
            st.dataframe(upcoming_entry[['Student Name', 'School Entry Date', 'Chosen School', 'Stage']], height=200)
            st.markdown('</div>', unsafe_allow_html=True)

        # Students in final stages without visa results
        with st.container():
            st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
            st.markdown('<p class="medium-font">🏁 Students in Final Stages Without Visa Results</p>', unsafe_allow_html=True)
            final_stages = df[
                (df['Stage'].isin(['ITW Prep.', 'SEVIS'])) &
                (df['Visa Result'].isna() | (df['Visa Result'] == ''))
            ]
            st.dataframe(final_stages[['Student Name', 'Stage', 'EMBASSY ITW. DATE']], height=200)
            st.markdown('</div>', unsafe_allow_html=True)

    # Full-width sections
    st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
    st.markdown('<p class="medium-font">📅 All Upcoming Events</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Embassy Appointments", "School Entry Dates", "Missing Information"])
    
    with tab1:
        st.markdown('<p class="small-font">Students Sorted by Upcoming Embassy Appointment Date</p>', unsafe_allow_html=True)
        embassy_sorted = df[df['EMBASSY ITW. DATE'] > today].sort_values('EMBASSY ITW. DATE')
        st.dataframe(embassy_sorted[['Student Name', 'EMBASSY ITW. DATE', 'Stage']], height=300)
    
    with tab2:
        st.markdown('<p class="small-font">Students Sorted by Upcoming School Entry Date</p>', unsafe_allow_html=True)
        school_sorted = df[df['School Entry Date'] > today].sort_values('School Entry Date')
        st.dataframe(school_sorted[['Student Name', 'School Entry Date', 'Chosen School']], height=300)
    
    with tab3:
        st.markdown('<p class="small-font">Applicants Without School Entry Date</p>', unsafe_allow_html=True)
        no_entry_date = df[df['School Entry Date'].isna()]
        st.dataframe(no_entry_date[['Student Name', 'Chosen School', 'Stage']], height=300)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Duplicate Students
    st.markdown('<div class="dashboard-item">', unsafe_allow_html=True)
    st.markdown('<p class="medium-font">👥 Duplicate Students</p>', unsafe_allow_html=True)
    duplicates = df[df.duplicated(subset=['Student Name'], keep=False)]
    if not duplicates.empty:
        st.dataframe(duplicates[['Student Name', 'DATE', 'Stage']], height=200)
        st.markdown('<p class="small-font highlight">⚠️ Please review and resolve these duplicate entries in the "ALL" sheet.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="small-font">✅ No duplicate students found.</p>')
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Student Application Tracker", layout="wide")
    
    # Add a new option in your sidebar or navigation
    page = st.sidebar.selectbox("Choose a page", ["Student Tracker", "Tasks and Emergencies"])
    
    # Load the data once and pass it to both pages
    data = load_data('/mnt/data/Updated sheet 3 (2).xlsx')
    
    if page == "Student Tracker":
        student_tracker_page(data)  # Your existing main page function
    elif page == "Tasks and Emergencies":
        tasks_and_emergencies_page(data)

def student_tracker_page(data):
    # Placeholder for the student tracker page
    st.title("Student Tracker")
    st.write("This page is under construction.")
    # Implement the tracker page logic here

if __name__ == "__main__":
    main()
