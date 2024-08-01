import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import calendar

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

def load_data(spreadsheet_id):
    sheet_headers = {
        'PAYMENT & MAIL': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'APPLICATION': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'SCAN & SEND': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'ARAMEX & RDV': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'DS-160': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'ITW Prep.': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'SEVIS': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'CLIENTS ': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ]
    }

    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(spreadsheet_id)

        combined_data = pd.DataFrame()

        for worksheet in sheet.worksheets():
            title = worksheet.title
            expected_headers = sheet_headers.get(title, None)

            if expected_headers:
                data = worksheet.get_all_records(expected_headers=expected_headers)
            else:
                data = worksheet.get_all_records()

            df = pd.DataFrame(data)
            if not df.empty:
                if 'First Name' in df.columns and 'Last Name' in df.columns:
                    df['First Name'] = df['First Name'].astype(str)
                    df['Last Name'] = df['Last Name'].astype(str)
                    df['Student Name'] = df['First Name'] + " " + df['Last Name']
                df.dropna(subset=['Student Name'], inplace=True)
                df.dropna(how='all', inplace=True)
                df['Current Step'] = title
                combined_data = pd.concat([combined_data, df], ignore_index=True)

        combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
        combined_data.reset_index(drop=True, inplace=True)

        return combined_data
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

# Set page config
st.set_page_config(page_title="Student Recruitment CRM", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stplot {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 1rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stSelectbox label, .stMultiSelect label {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title('📊 Student Recruitment CRM Dashboard')

    # Sidebar
    st.sidebar.title('📌 Navigation')
    page = st.sidebar.radio('Go to', ['Overview', 'Student Details', 'School Analytics', 'Visa Statistics'])

    # Google Sheets ID
    spreadsheet_id = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"

    if spreadsheet_id:
        data = load_data(spreadsheet_id)

        if not data.empty:
            # Data preprocessing
            data['DATE'] = pd.to_datetime(data['DATE'], format='%d/%m/%Y', errors='coerce')
            data = data[data['DATE'].notnull()]
            data = data.drop_duplicates(subset=['First Name', 'Last Name'])
            data['Year'] = data['DATE'].dt.year
            data['Month'] = data['DATE'].dt.month_name()

            if page == 'Overview':
                st.header('📈 Recruitment Overview')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Students", len(data))
                with col2:
                    st.metric("This Year's Recruits", len(data[data['Year'] == datetime.now().year]))
                with col3:
                    st.metric("Visa Approval Rate", f"{(data['Visa Result'] == 'Visa Approved').mean():.2%}")

                # Monthly recruitment trend
                st.subheader('Monthly Recruitment Trend')
                monthly_trend = data.groupby(['Year', 'Month']).size().reset_index(name='Count')
                monthly_trend['Date'] = pd.to_datetime(monthly_trend['Year'].astype(str) + ' ' + monthly_trend['Month'], format='%Y %B')
                monthly_trend = monthly_trend.sort_values('Date')
                fig_trend = px.line(monthly_trend, x='Date', y='Count', title='Monthly Recruitment Trend')
                st.plotly_chart(fig_trend, use_container_width=True)

                # Top schools
                st.subheader('Top Schools')
                top_schools = data['Chosen School'].value_counts().reset_index()
                top_schools.columns = ['School', 'Count']
                top_schools = top_schools.head(5)  # Get top 5 schools
                fig_schools = px.bar(top_schools, x='School', y='Count', title='Top 5 Schools')
                st.plotly_chart(fig_schools, use_container_width=True)

            # Student Details Page
            elif page == 'Student Details':
                st.header('👨‍🎓 Student Details')
                
                # Search functionality
                search_term = st.text_input('🔍 Search for a student (First Name or Last Name)')
                if search_term:
                    filtered_data = data[data['First Name'].str.contains(search_term, case=False) | 
                                         data['Last Name'].str.contains(search_term, case=False)]
                else:
                    filtered_data = data

                # Display student details
                for _, student in filtered_data.iterrows():
                    with st.expander(f"{student['First Name']} {student['Last Name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Email:** {student['E-mail']}")
                            st.write(f"**Phone:** {student['Phone N°']}")
                            st.write(f"**School:** {student['Chosen School']}")
                        with col2:
                            st.write(f"**Visa Result:** {student['Visa Result']}")
                            st.write(f"**Current Step:** {student['Current Step']}")
                            st.write(f"**Agent:** {student['Agent']}")

            # School Analytics Page
            elif page == 'School Analytics':
                st.header('🏫 School Analytics')
                
                # School selection
                selected_school = st.selectbox('Select a school', data['Chosen School'].unique())
                school_data = data[data['Chosen School'] == selected_school]

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Students", len(school_data))
                with col2:
                    st.metric("Visa Approval Rate", f"{(school_data['Visa Result'] == 'Visa Approved').mean():.2%}")

                # Monthly trend for the selected school
                monthly_school_trend = school_data.groupby(['Year', 'Month']).size().reset_index(name='Count')
                monthly_school_trend['Date'] = pd.to_datetime(monthly_school_trend['Year'].astype(str) + ' ' + monthly_school_trend['Month'], format='%Y %B')
                monthly_school_trend = monthly_school_trend.sort_values('Date')
                fig_school_trend = px.line(monthly_school_trend, x='Date', y='Count', title=f'Monthly Trend for {selected_school}')
                st.plotly_chart(fig_school_trend, use_container_width=True)

            # Visa Statistics Page
            elif page == 'Visa Statistics':
                st.header('🛂 Visa Statistics')
                
                # Overall visa statistics
                visa_stats = data['Visa Result'].value_counts()
                fig_visa = px.pie(values=visa_stats.values, names=visa_stats.index, title='Overall Visa Results')
                st.plotly_chart(fig_visa, use_container_width=True)

                # Visa approval rate by school
                visa_by_school = data.groupby('Chosen School')['Visa Result'].apply(lambda x: (x == 'Visa Approved').mean()).sort_values(ascending=False)
                fig_visa_school = px.bar(visa_by_school, x=visa_by_school.index, y=visa_by_school.values, title='Visa Approval Rate by School')
                fig_visa_school.update_layout(yaxis_title='Approval Rate', xaxis_title='School')
                st.plotly_chart(fig_visa_school, use_container_width=True)

                # Visa approval trend
                visa_trend = data.groupby(['Year', 'Month'])['Visa Result'].apply(lambda x: (x == 'Visa Approved').mean()).reset_index(name='Approval Rate')
                visa_trend['Date'] = pd.to_datetime(visa_trend['Year'].astype(str) + ' ' + visa_trend['Month'], format='%Y %B')
                visa_trend = visa_trend.sort_values('Date')
                fig_visa_trend = px.line(visa_trend, x='Date', y='Approval Rate', title='Visa Approval Rate Trend')
                st.plotly_chart(fig_visa_trend, use_container_width=True)

if __name__ == "__main__":
    main()
