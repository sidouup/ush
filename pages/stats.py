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

# Main app logic
def main():
    st.title('Student Payments Analysis')
    st.sidebar.title('Settings')

    # Google Sheets ID
    spreadsheet_id = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"

    if spreadsheet_id:
        data = load_data(spreadsheet_id)

        if not data.empty:
            st.write("Loaded data from Google Sheets:")
            st.write(data.head())

            # Convert DATE column to datetime
            data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
            st.write("Data with DATE column converted to datetime:")
            st.write(data.head())

            # Extract Year and Month
            data['Year'] = data['DATE'].dt.year
            data['Month'] = data['DATE'].dt.month_name()  # Convert month number to month name
            st.write("Data with Year and Month extracted:")
            st.write(data.head())

            # Filter data for the year 2024
            data_2024 = data[data['Year'] == 2024]
            st.write("Filtered data for 2024:")
            st.write(data_2024.head())

            # Group by Month to get payment counts
            monthly_payments_2024 = data_2024.groupby('Month').size().reset_index(name='Number of Payments')
            st.write("Monthly payment counts before sorting:")
            st.write(monthly_payments_2024)

            # Ensure months are in the correct order
            month_order = [
                'January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            monthly_payments_2024['Month'] = pd.Categorical(monthly_payments_2024['Month'], categories=month_order, ordered=True)
            monthly_payments_2024 = monthly_payments_2024.sort_values('Month')
            st.write("Monthly payment counts after sorting:")
            st.write(monthly_payments_2024)

            st.write("Monthly Payments for 2024:")
            st.write(monthly_payments_2024)

            # Plotting the data for 2024
            fig = px.bar(monthly_payments_2024, x='Month', y='Number of Payments',
                         title="Monthly Payments Distribution for 2024",
                         labels={'Month': 'Month', 'Number of Payments': 'Number of Payments'})
            fig.update_layout(xaxis_title='Month', yaxis_title='Number of Payments')
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
