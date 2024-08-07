import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import streamlit as st
from datetime import datetime

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

def filter_data_by_date_range(data, start_date, end_date):
    return data[(data['DATE'] >= start_date) & (data['DATE'] <= end_date)]

def filter_data_by_month_year(data, year, month):
    start_date = pd.Timestamp(year=year, month=month, day=1)
    end_date = start_date + pd.offsets.MonthEnd(1)
    return data[(data['DATE'] >= start_date) & (data['DATE'] <= end_date)]

def calculate_visa_approval_rate(data):
    # Filter for applications where a decision has been made
    decided_applications = data[data['Visa Result'].isin(['Visa Approved', 'Visa Denied'])]
    
    # Calculate total decided applications
    total_decided = len(decided_applications)
    
    # Calculate number of approved visas
    approved_visas = len(decided_applications[decided_applications['Visa Result'] == 'Visa Approved'])
    
    # Calculate approval rate
    approval_rate = (approved_visas / total_decided * 100) if total_decided > 0 else 0
    
    return approval_rate, approved_visas, total_decided

def statistics_page():
    st.set_page_config(page_title="Student Recruitment Statistics", layout="wide")
    
    st.markdown("""
    <style>
        .reportview-container {
            background: #f0f2f6;
        }
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        h1, h2, h3 {
            color: #1E3A8A;
            font-size: 1.2rem; /* Adjust font size */
        }
        .stMetric {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px; /* Adjust padding */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 0.8rem; /* Adjust font size */
        }
        .stMarkdown {
            font-size: 0.8rem; /* Adjust font size */
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Student Recruitment Statistics")

    # Load data from Google Sheets
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    sheet_name = "ALL"
    data = load_data(spreadsheet_id, sheet_name)

    # Convert 'DATE' column to datetime and handle NaT values
    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')

    # Identify rows with incorrect date format in the original data
    incorrect_date_mask = data['DATE'].isna()
    incorrect_date_count = incorrect_date_mask.sum()
    
    # Create a DataFrame with students having incorrect dates
    students_with_incorrect_dates = data[incorrect_date_mask]

    # Remove duplicates for analysis
    data_deduped = data.drop_duplicates(subset=['Student Name', 'Chosen School'], keep='last')
    
    # Remove rows with NaT values in the DATE column for further analysis
    data_clean = data_deduped.dropna(subset=['DATE'])

    # (Rest of the code remains the same until the "Applications Over Time" section)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Applications Over Time")
        # Use 'Months' column instead of DATE
        monthly_apps = data_clean['Months'].value_counts().sort_index().reset_index()
        monthly_apps.columns = ['Month', 'count']
        # Convert 'Month' to datetime for proper sorting
        monthly_apps['Month'] = pd.to_datetime(monthly_apps['Month'], format='%B %Y')
        monthly_apps = monthly_apps.sort_values('Month')
        fig = px.line(monthly_apps, x='Month', y='count',
                      labels={'count': 'Number of Applications', 'Month': 'Month'},
                      title="Monthly Application Trend")
        fig.update_xaxes(tickformat="%b %Y")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Payment Methods")
        # Use deduplicated data for counting
        payment_counts = data_clean['Payment Type'].value_counts()
        fig = px.pie(values=payment_counts.values, names=payment_counts.index,
                     title="Payment Method Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # (Rest of the code remains the same until the "Top Payment Types" section)

    st.header("💰 Top 5 Payment Types")

    # Count the number of payments in each category and get the top 5
    # Use deduplicated data for counting
    payment_counts = data_clean['Payment Amount'].value_counts().nlargest(5)

    # Create a bar chart for top 5 payment categories
    fig = px.bar(x=payment_counts.index, y=payment_counts.values,
                 labels={'x': 'Payment Amount', 'y': 'Number of Payments'},
                 title="Top 5 Payment Types")
    fig.update_traces(text=payment_counts.values, textposition='outside')
    fig.update_layout(xaxis_title="Payment Amount",
                      yaxis_title="Number of Payments",
                      bargap=0.2)
    
    st.plotly_chart(fig, use_container_width=True)

    # Display the data in a table format as well
    st.subheader("Top 5 Payment Types Distribution")
    payment_df = pd.DataFrame({'Payment Amount': payment_counts.index, 'Number of Payments': payment_counts.values})
    st.dataframe(payment_df)

    # (The rest of the code remains the same)

if __name__ == "__main__":
    statistics_page()

