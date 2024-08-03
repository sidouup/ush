import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import streamlit as st
from datetime import datetime
from datetime import datetime, timedelta

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]
@@ -18,21 +18,21 @@ def get_google_sheet_client():
    return gspread.authorize(creds)

# Function to load data from Google Sheets
@st.cache_data(ttl=600)
def load_data(spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Convert 'DATE' column to datetime
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce', format='%d/%m/%Y %H:%M:%S')

    # Convert 'EMBASSY ITW. DATE' to datetime, handling potential errors
    df['EMBASSY ITW. DATE'] = pd.to_datetime(df['EMBASSY ITW. DATE'], errors='coerce', format='%d/%m/%Y %H:%M:%S')

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
@@ -48,210 +48,151 @@ def calculate_visa_approval_rate(data):

    return approval_rate, approved_visas, total_decided

def statistics_page():
    st.set_page_config(page_title="Student Recruitment Statistics", layout="wide")

def main_dashboard():
    st.set_page_config(page_title="The Us House - Dashboard", layout="wide")

    # Custom CSS for modern and elegant design
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
        .stMetric {
            background-color: #ffffff;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #3B82F6;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #6B7280;
    }
    .chart-container {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .stButton>button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Student Recruitment Statistics")
    # App title and logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png", width=150)
        st.markdown("<h1 class='main-title'>The Us House Dashboard</h1>", unsafe_allow_html=True)

    # Load data from Google Sheets
    # Load data
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
    data = load_data(spreadsheet_id, "ALL")

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

    # Key Metrics
    st.markdown("<h2 class='sub-title'>Key Metrics</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        total_students = len(filtered_data)
        st.metric("Total Unique Students", total_students)
        total_students = len(data_clean)
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{total_students}</p>
            <p class='metric-label'>Total Unique Students</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("Visa Approvals", visa_approved)
        overall_approval_rate, visa_approved, total_decisions = calculate_visa_approval_rate(data_clean)
        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{visa_approved}</p>
            <p class='metric-label'>Visa Approvals</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.metric("Visa Approval Rate", f"{overall_approval_rate:.2f}%")

    st.markdown("---")

        st.markdown(f"""
        <div class='metric-card'>
            <p class='metric-value'>{overall_approval_rate:.2f}%</p>
            <p class='metric-label'>Visa Approval Rate</p>
        </div>
        """, unsafe_allow_html=True)

    # Quick Actions
    st.markdown("<h2 class='sub-title'>Quick Actions</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Add New Student"):
            st.switch_page("pages/New_Student.py")
    with col2:
        if st.button("👥 View Student List"):
            st.switch_page("pages/GoogleSheet.py")
    with col3:
        if st.button("📊 View Statistics"):
            st.switch_page("pages/Statistics.py")
    with col4:
        if st.button("🔍 Search Students"):
            st.switch_page("pages/Students.py")

    # Charts
    st.markdown("<h2 class='sub-title'>Analytics</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🏫 Top Chosen Schools")
        school_counts = filtered_data['Chosen School'].value_counts().head(10).reset_index()
        school_counts = data_clean['Chosen School'].value_counts().head(10).reset_index()
        school_counts.columns = ['School', 'Number of Students']
        fig = px.bar(school_counts, x='School', y='Number of Students',
                     labels={'Number of Students': 'Number of Students', 'School': 'School'},
                     title="Top 10 Chosen Schools")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🛂 Student Visa Approval")
        visa_status = filtered_data['Visa Result'].value_counts()
        visa_status = data_clean['Visa Result'].value_counts()
        colors = {'Visa Approved': 'blue', 'Visa Denied': 'red', '0 not yet': 'grey', 'not our school': 'lightblue'}
        fig = px.pie(values=visa_status.values, names=visa_status.index,
                     title="Visa Application Results", color=visa_status.index, 
                     color_discrete_map=colors)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # New section for Visa Approval Rate by School
    st.subheader("🏆 Top 8 Schools by Visa Approval Rate")

    def school_approval_rate(group):
        return calculate_visa_approval_rate(group)[0]

    school_visa_stats = filtered_data.groupby('Chosen School').apply(school_approval_rate).reset_index(name='Approval Rate')

    # Sort by approval rate and get top 8
    top_8_schools = school_visa_stats.sort_values('Approval Rate', ascending=False).head(8)

    fig = px.bar(top_8_schools, x='Chosen School', y='Approval Rate',
                 text='Approval Rate',
                 labels={'Approval Rate': 'Visa Approval Rate (%)', 'Chosen School': 'School'},
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
    st.table(payment_df)
    # Recent Activity
    st.markdown("<h2 class='sub-title'>Recent Activity</h2>", unsafe_allow_html=True)
    recent_activity = data_clean.sort_values('DATE', ascending=False).head(5)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.dataframe(recent_activity[['DATE', 'Student Name', 'Chosen School', 'Stage']], hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    statistics_page()
    main_dashboard()
