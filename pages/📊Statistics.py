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
    
    # Create a DataFrame with students having incorrect date format
    students_with_incorrect_dates = data[incorrect_date_mask]

    # Remove duplicates for analysis
    data_deduped = data.drop_duplicates(subset=['Student Name', 'Chosen School'], keep='last')
    
    # Remove rows with NaT values in the DATE column for further analysis
    data_clean = data_deduped.dropna(subset=['DATE'])

    min_date = data_clean['DATE'].min()
    max_date = data_clean['DATE'].max()
    years = list(range(min_date.year, max_date.year + 1))
    months = list(range(1, 13))

    # Filter selection
    st.sidebar.subheader("Filter Options")
    filter_option = st.sidebar.radio("Select Filter Method", ("Date Range", "Month and Year"))

    min_date = min_date.to_pydatetime() if not pd.isna(min_date) else datetime(2022, 1, 1)
    max_date = max_date.to_pydatetime() if not pd.isna(max_date) else datetime(2022, 12, 31)

    if filter_option == "Date Range":
        start_date = st.sidebar.date_input("Start Date", min_date)
        end_date = st.sidebar.date_input("End Date", max_date)
        
        # Convert date inputs to pandas Timestamp objects
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        filtered_data = filter_data_by_date_range(data_clean, start_date, end_date)
    else:
        selected_year = st.sidebar.selectbox("Year", years)
        selected_month = st.sidebar.selectbox("Month", months, format_func=lambda x: datetime(2023, x, 1).strftime('%B'))
        filtered_data = filter_data_by_month_year(data_clean, selected_year, selected_month)

    # Calculate overall visa approval rate
    overall_approval_rate, visa_approved, total_decisions = calculate_visa_approval_rate(filtered_data)

    col1, col2, col3 = st.columns(3)

    with col1:
        total_students = len(filtered_data)
        st.metric("Total Unique Students", total_students)

    with col2:
        st.metric("Visa Approvals", visa_approved)

    with col3:
        st.metric("Visa Approval Rate", f"{overall_approval_rate:.2f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏫 Top Chosen Schools")
        school_counts = filtered_data['Chosen School'].value_counts().head(10).reset_index()
        school_counts.columns = ['School', 'Number of Students']
        fig = px.bar(school_counts, x='School', y='Number of Students',
                     labels={'Number of Students': 'Number of Students', 'School': 'School'},
                     title="Top 10 Chosen Schools")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🛂 Student Visa Approval")
        visa_status = filtered_data['Visa Result'].value_counts()
        colors = {'Visa Approved': 'blue', 'Visa Denied': 'red', '0 not yet': 'grey', 'not our school': 'lightblue'}
        fig = px.pie(values=visa_status.values, names=visa_status.index,
                     title="Visa Application Results", color=visa_status.index, 
                     color_discrete_map=colors)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # New section for Visa Approval Rate by School
    st.subheader("🏆 Top 8 Schools by Visa Approval Rate")
    
    def school_approval_rate(group):
        return calculate_visa_approval_rate(group)[0]
    
    school_visa_stats = filtered_data.groupby('Chosen School').apply(school_approval_rate).reset_index()
    school_visa_stats.columns = ['School', 'Approval Rate']
    
    # Sort by approval rate and get top 8
    top_8_schools = school_visa_stats.sort_values('Approval Rate', ascending=False).head(8)
    
    fig = px.bar(top_8_schools, x='School', y='Approval Rate',
                 text='Approval Rate',
                 labels={'Approval Rate': 'Visa Approval Rate (%)', 'School': 'School'},
                 title="Top 8 Schools by Visa Approval Rate")
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Applications Over Time")
        monthly_apps = filtered_data.groupby(filtered_data['DATE'].dt.to_period("M")).size().reset_index(name='count')
        monthly_apps['DATE'] = monthly_apps['DATE'].dt.to_timestamp()
        fig = px.line(monthly_apps, x='DATE', y='count',
                      labels={'count': 'Number of Applications', 'DATE': 'Date'},
                      title="Monthly Application Trend")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Payment Methods")
        payment_counts = filtered_data['Payment Type'].value_counts()
        fig = px.pie(values=payment_counts.values, names=payment_counts.index,
                     title="Payment Method Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Gender Distribution")
        gender_counts = filtered_data['Gender'].value_counts()
        fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                     title="Gender Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🔄 Application Attempts")
        attempts_counts = filtered_data['Attempts'].value_counts().reset_index()
        attempts_counts.columns = ['Attempt', 'Number of Students']
        fig = px.bar(attempts_counts, x='Attempt', y='Number of Students',
                     labels={'Number of Students': 'Number of Students', 'Attempt': 'Attempt'},
                     title="Application Attempts Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🏆 Top Performing Agents")
    agent_performance = filtered_data['Agent'].value_counts().head(5).reset_index()
    agent_performance.columns = ['Agent', 'Number of Students']
    fig = px.bar(agent_performance, x='Agent', y='Number of Students',
                 labels={'Number of Students': 'Number of Students', 'Agent': 'Agent'},
                 title="Top 5 Agents by Number of Students")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # New Payment Amount Statistics Section
    st.header("💰 Top 5 Payment Types")

    # Count the number of payments in each category and get the top 5
    payment_counts = filtered_data['Payment Amount'].value_counts().nlargest(5)

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

if __name__ == "__main__":
    statistics_page()
