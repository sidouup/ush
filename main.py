import streamlit as st
import pandas as pd
from datetime import datetime

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

st.write("Welcome to the Student Application Tracker. Use the sidebar to navigate between different pages.")

# File uploader in the sidebar
st.sidebar.title("Data Upload")
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    st.session_state['uploaded_file'] = uploaded_file
    st.success("File uploaded successfully! You can now navigate to other pages to view the data.")
else:
    st.info("Please upload an Excel file to proceed.")

# Utility functions
@st.cache_data
def load_and_combine_data(excel_file):
    xls = pd.ExcelFile(excel_file)
    combined_data = pd.DataFrame()
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df['Student Name'] = df.iloc[:, 1].astype(str) + " " + df.iloc[:, 2].astype(str)
        df.dropna(subset=['Student Name'], inplace=True)
        df.dropna(how='all', inplace=True)
        df['Current Step'] = sheet_name
        combined_data = pd.concat([combined_data, df], ignore_index=True)
    
    combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
    combined_data.reset_index(drop=True, inplace=True)
    return combined_data

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

