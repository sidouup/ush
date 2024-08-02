import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

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
    df = df.astype(str)  # Convert all columns to strings
    return df


def statistics_page():
    st.set_page_config(page_title="Student Recruitment Statistics", layout="wide")
    
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
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Student Recruitment Statistics")

    data = load_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        total_students = len(data)
        st.metric("Total Students", total_students)

    with col2:
        visa_approved = len(data[data['Visa Result'] == 'Visa Approved'])
        st.metric("Visa Approvals", visa_approved)

    with col3:
        visa_approval_rate = (visa_approved / total_students) * 100
        st.metric("Visa Approval Rate", f"{visa_approval_rate:.2f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏫 Top Schools")
        school_counts = data['Chosen School'].value_counts().head(10)
        fig = px.bar(school_counts, x=school_counts.index, y=school_counts.values,
                     labels={'y': 'Number of Students', 'x': 'School'},
                     title="Top 10 Chosen Schools")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🌎 Student Distribution by Country")
        # Assuming you have a 'Country' column. If not, you might need to extract it from another column
        if 'Country' in data.columns:
            country_counts = data['Country'].value_counts()
        else:
            country_counts = pd.Series({'United States': len(data)})  # Placeholder if no country data
        fig = px.pie(values=country_counts.values, names=country_counts.index,
                     title="Student Distribution by Country")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Applications Over Time")
        data['DATE'] = pd.to_datetime(data['DATE'])
        monthly_apps = data.resample('M', on='DATE').size()
        fig = px.line(monthly_apps, x=monthly_apps.index, y=monthly_apps.values,
                      labels={'y': 'Number of Applications', 'x': 'Date'},
                      title="Monthly Application Trend")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Payment Methods")
        payment_counts = data['Payment Type'].value_counts()
        fig = px.pie(values=payment_counts.values, names=payment_counts.index,
                     title="Payment Method Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎓 Program Types")
        program_counts = data['Specialite'].value_counts().head(5)
        fig = px.bar(program_counts, x=program_counts.index, y=program_counts.values,
                     labels={'y': 'Number of Students', 'x': 'Program'},
                     title="Top 5 Program Types")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👥 Gender Distribution")
        gender_counts = data['Gender'].value_counts()
        fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                     title="Gender Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.subheader("🔄 Application Attempts")
        attempts_counts = data['Attempts'].value_counts()
        fig = px.bar(attempts_counts, x=attempts_counts.index, y=attempts_counts.values,
                     labels={'y': 'Number of Students', 'x': 'Attempt'},
                     title="Application Attempts Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🏆 Top Performing Agents")
    agent_performance = data.groupby('Agent')['Visa Result'].apply(lambda x: (x == 'Visa Approved').sum() / len(x) * 100).sort_values(ascending=False).head(5)
    fig = px.bar(agent_performance, x=agent_performance.index, y=agent_performance.values,
                 labels={'y': 'Approval Rate (%)', 'x': 'Agent'},
                 title="Top 5 Agents by Visa Approval Rate")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    statistics_page()
