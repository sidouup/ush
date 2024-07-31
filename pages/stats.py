import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread

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
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'APPLICATION': [
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'SCAN & SEND': [
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'ARAMEX & RDV': [
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'DS-160': [
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
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
        
def plot_insights(data):
    # Ensure the DATE column is datetime type
    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')

    st.title("Student Application Insights")

    # Overview of the data
    st.header("Data Overview")
    st.write(data.describe(include='all'))

    # Distribution of students by chosen school
    st.header("Distribution by Chosen School")
    school_count = data['Chosen School'].value_counts()
    fig1 = px.bar(school_count, x=school_count.index, y=school_count.values, labels={'x': 'Chosen School', 'y': 'Count'})
    st.plotly_chart(fig1)

    # Payment methods distribution
    st.header("Distribution of Payment Methods")
    payment_method_count = data['Payment Method '].value_counts()
    fig2 = px.pie(payment_method_count, values=payment_method_count.values, names=payment_method_count.index, title='Payment Methods Distribution')
    st.plotly_chart(fig2)

    # Visa result over time
    st.header("Visa Results Over Time")
    visa_results = data.dropna(subset=['Visa Result'])
    fig3 = px.histogram(visa_results, x='DATE', color='Visa Result', title='Visa Results Over Time')
    st.plotly_chart(fig3)

    # Applications by agent
    st.header("Applications by Agent")
    agent_count = data['Agent'].value_counts()
    fig4 = px.bar(agent_count, x=agent_count.index, y=agent_count.values, labels={'x': 'Agent', 'y': 'Applications Count'})
    st.plotly_chart(fig4)

    # School entry dates
    st.header("School Entry Dates")
    school_entry_dates = data.dropna(subset=['School Entry Date'])
    fig5 = px.histogram(school_entry_dates, x='School Entry Date', title='School Entry Dates')
    st.plotly_chart(fig5)

    # Distribution of durations
    st.header("Duration of Study Programs")
    duration_count = data['Duration'].value_counts()
    fig6 = px.bar(duration_count, x=duration_count.index, y=duration_count.values, labels={'x': 'Duration', 'y': 'Count'})
    st.plotly_chart(fig6)

    # Emergency contacts overview
    st.header("Emergency Contacts Overview")
    emergency_contact_count = data['Emergency contact N°'].nunique()
    st.write(f"Number of unique emergency contacts: {emergency_contact_count}")

    # Entry dates in the US
    st.header("Entry Dates in the US")
    entry_dates_us = data.dropna(subset=['Entry Date in the US'])
    fig7 = px.histogram(entry_dates_us, x='Entry Date in the US', title='Entry Dates in the US')
    st.plotly_chart(fig7)

# Example of how to call the function with loaded data
spreadsheet_id = 'your_spreadsheet_id_here'  # Replace with your Google Sheets ID
data = load_data(spreadsheet_id)
plot_insights(data)
if __name__ == "__main__":
    statistics_page()
