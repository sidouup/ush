import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets configuration
private_gsheets_url = "https://docs.google.com/spreadsheets/d/1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ/edit?gid=503506128#gid=503506128"

# Set up Google Sheets credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(credentials)

# Function to load and combine data from all sheets in the Google Sheet
@st.cache_data(ttl=3600)
def load_and_combine_data(gsheets_url, expected_headers):
    sheet = client.open_by_url(gsheets_url)
    combined_data = pd.DataFrame()
    
    for worksheet in sheet.worksheets():
        data = worksheet.get_all_records(expected_headers=expected_headers)  # Use expected headers to ensure uniqueness
        df = pd.DataFrame(data)
        
        df['Student Name'] = df.iloc[:, 1].astype(str) + " " + df.iloc[:, 2].astype(str)
        df.dropna(subset=['Student Name'], inplace=True)
        df.dropna(how='all', inplace=True)
        df['Current Step'] = worksheet.title
        combined_data = pd.concat([combined_data, df], ignore_index=True)
    
    combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
    combined_data.reset_index(drop=True, inplace=True)
    return combined_data

# Function to map visa status based on the 'visa result' column
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

# Set page config
st.set_page_config(page_title="Student Application Tracker", layout="wide")

# Custom CSS for a refined look with better readability and colored button
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

# Load and combine data from all sheets in the Google Sheet
expected_headers = [
    'First Name', 'Last Name', 'Phone N°', 'E-mail', 'Emergency contact N°',
    'Attempts', 'Address', 'Chosen School', 'Duration', 'School Entry Date',
    'Entry Date in the US', 'ADDRESS in the U.S', 'E-MAIL RDV', 'PASSWORD RDV',
    'EMBASSY ITW. DATE', 'DS-160 maker', 'Password DS-160', 'Secret Q.',
    'Visa Result', 'DATE', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?'
]

data = load_and_combine_data(private_gsheets_url, expected_headers)

# Combined search and selection functionality
st.header("👤 Student Search and Details")
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("🔍 Search for a student (First or Last Name)")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add some vertical space
    search_button = st.button("Search", key="search_button", help="Click to search")

# Filter data based on search query
if search_query and search_button:
    filtered_data = data[data['Student Name'].str.contains(search_query, case=False, na=False)]
else:
    filtered_data = data

# Display filtered data with selection capability
if not filtered_data.empty:
    selected_index = st.selectbox(
        "Select a student to view details",
        range(len(filtered_data)),
        format_func=lambda i: f"{filtered_data.iloc[i]['Student Name']} - {filtered_data.iloc[i]['Current Step']}"
    )
    
    selected_student = filtered_data.iloc[selected_index]
    
    # Display student details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.expander("📋 Personal Information", expanded=True):
            st.write(selected_student[['First Name', 'Last Name', 'Phone N°', 'E-mail', 'Emergency contact N°', 'Attempts', 'Address']])
        
        with st.expander("🏫 School Information", expanded=True):
            st.write(selected_student[['Chosen School', 'Duration', 'School Entry Date', 'Entry Date in the US']])
        
        with st.expander("🏛️ Embassy Information", expanded=True):
            st.write(selected_student[['ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV', 'EMBASSY ITW. DATE', 'DS-160 maker', 'Password DS-160', 'Secret Q.']])
    
    with col2:
        st.subheader("Application Status")
        
        # Visa Status
        visa_status = get_visa_status(selected_student['Visa Result'])
        st.metric("Visa Status", visa_status)
        
        # Current Step
        current_step = selected_student['Current Step']
        st.metric("Current Step", current_step)
        
        # Days until interview
        interview_date = selected_student['EMBASSY ITW. DATE']
        days_remaining = calculate_days_until_interview(interview_date)
        if days_remaining is not None:
            st.metric("Days until interview", days_remaining)
        else:
            st.metric("Days until interview", "N/A")
        
        # Payment Information
        with st.expander("💰 Payment Information", expanded=True):
            st.write(selected_student[['DATE','Payment Method ', 'Sevis payment ? ', 'Application payment ?']])
else:
    st.info("No students found matching the search criteria.")

# Dashboard with all clients (moved to the end)
st.header("📊 Dashboard - All Clients")

# Create a bar chart of students per step
step_counts = data['Current Step'].value_counts()
fig = px.bar(step_counts, x=step_counts.index, y=step_counts.values, 
             labels={'x': 'Application Step', 'y': 'Number of Students'},
             title='Students per Application Step')
fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0.05)',
    paper_bgcolor='rgba(0,0,0,0)',
)
st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("© 2024 The Us House. All rights reserved.")
