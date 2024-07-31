import os
import json
import gspread
import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import plotly.express as px
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Drive service
@st.cache_resource
def get_google_drive_service():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load data from Google Sheets
def load_data(spreadsheet_id):
    sheet_headers = {
        'PAYMENT & MAIL': [
            'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'APPLICATION': [
            'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'SCAN & SEND': [
            'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'ARAMEX & RDV': [
            'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
            'Duration', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?', 'DS-160 maker', 'Password DS-160',
            'Secret Q.', 'School Entry Date', 'Entry Date in the US', 'ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV',
            'EMBASSY ITW. DATE', 'Attempts', 'Visa Result', 'Agent', 'Note'
        ],
        'DS-160': [
            'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 'Emergency contact N°', 'Chosen School',
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

# Function to calculate days until interview
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

# Function to get visa status
def get_visa_status(result):
    result_mapping = {
        'Denied': 'Denied',
        'Approved': 'Approved',
        'Not our school partner': 'Not our school partner',
    }
    return result_mapping.get(result, 'Unknown')

# Function to check if a folder exists in Google Drive
def check_folder_exists(folder_name, parent_id=None):
    service = get_google_drive_service()
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    return folders[0].get('id') if folders else None

# Function to list files in a folder
def list_files_in_folder(folder_id):
    service = get_google_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
    return results.get('files', [])

# Function to check document status and get file links
def check_document_status(student_name):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    
    document_types = ["Passport", "Bank Statement", "Financial Letter", "Transcripts", "Diplomas", "English Test"]
    document_status = {doc_type: {'status': False, 'files': []} for doc_type in document_types}

    if not student_folder_id:
        return document_status

    for document_type in document_types:
        document_folder_id = check_folder_exists(document_type, student_folder_id)
        if document_folder_id:
            files = list_files_in_folder(document_folder_id)
            document_status[document_type]['status'] = bool(files)
            document_status[document_type]['files'] = files
    
    return document_status

# Main function
def main():
    st.set_page_config(page_title="Student Application Viewer", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="display: flex; align-items: center;">
            <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
            <h1 style="color: #1E3A8A;">Student Application Viewer</h1>
        </div>
        """, unsafe_allow_html=True)

    spreadsheet_id = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"
    data = load_data(spreadsheet_id)

    if not data.empty:
        st.header("👤 Student Search and Details")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search for a student (First or Last Name)", key="search_query")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_button = st.button("Search", key="search_button", help="Click to search")
        
        if search_query and search_button:
            filtered_data = data[data['Student Name'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_data = data

        if not filtered_data.empty:
            selected_index = st.selectbox(
                "Select a student to view details",
                range(len(filtered_data)),
                format_func=lambda i: f"{filtered_data.iloc[i]['Student Name']} - {filtered_data.iloc[i]['Current Step']}",
                key="selected_index"
            )
        
            selected_student = filtered_data.iloc[selected_index]
            student_name = selected_student['Student Name']
        
            col1, col2 = st.columns([2, 1])
            with col1:
                with st.expander("📋 Personal Information", expanded=True):
                    st.write(f"**First Name:** {selected_student['First Name']}")
                    st.write(f"**Last Name:** {selected_student['Last Name']}")
                    st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                    st.write(f"**Email:** {selected_student['E-mail']}")
                    st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                    st.write(f"**Address:** {selected_student['Address']}")
                    st.write(f"**Attempts:** {selected_student['Attempts']}")
                
                with st.expander("🏫 School Information", expanded=True):
                    st.write(f"**Chosen School:** {selected_student['Chosen School']}")
                    st.write(f"**Duration:** {selected_student['Duration']}")
                    st.write(f"**School Entry Date:** {selected_student['School Entry Date']}")
                    st.write(f"**Entry Date in the US:** {selected_student['Entry Date in the US']}")
                
                with st.expander("🏛️ Embassy Information", expanded=True):
                    st.write(f"**Address in the U.S:** {selected_student['ADDRESS in the U.S']}")
                    st.write(f"**E-mail RDV:** {selected_student[' E-MAIL RDV']}")
                    st.write(f"**Password RDV:** {selected_student['PASSWORD RDV']}")
                    st.write(f"**Embassy Interview Date:** {selected_student['EMBASSY ITW. DATE']}")
                    st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                    st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                    st.write(f"**Secret Question:** {selected_student['Secret Q.']}")
                
            with col2:
                st.subheader("Application Status")
                steps = [
                    'PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 
                    'ARAMEX & RDV', 'DS-160', 'ITW Prep.', 'SEVIS', 'CLIENTS '
                ]
                
                # Calculate the current step and progress
                current_step = selected_student['Current Step']
                step_index = steps.index(current_step) if current_step in steps else 0
                progress = (step_index + 1) / len(steps)
                
                # HTML and CSS for a custom progress bar
                progress_html = f"""
                <style>
                .progress-container {{
                  width: 100%;
                  background-color: #f3f3f3;
                  border-radius: 25px;
                  overflow: hidden;
                }}
                
                .progress-bar {{
                  width: {progress * 100}%;
                  height: 30px;
                  background-color: green;
                  text-align: center;
                  line-height: 30px;
                  color: white;
                  border-radius: 25px;
                }}
                </style>
                <div class="progress-container">
                  <div class="progress-bar">{int(progress * 100)}%</div>
                </div>
                """
                
                # Display the custom progress bar
                st.components.v1.html(progress_html, height=50)
                
                st.write(f"**Visa Status:** {get_visa_status(selected_student.get('Visa Result', 'Unknown'))}")
                st.write(f"**Current Step:** {selected_student['Current Step']}")
                
                interview_date = selected_student['EMBASSY ITW. DATE']
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("Days until interview", days_remaining)
                else:
                    st.metric("Days until interview", "N/A")
                
                with st.expander("💰 Payment Information", expanded=True):
                    st.write(f"**Payment Date:** {selected_student['DATE']}")
                    st.write(f"**Payment Method:** {selected_student['Payment Method ']}")
                    st.write(f"**Sevis Payment:** {selected_student['Sevis payment ? ']}")
                    st.write(f"**Application Payment:** {selected_student['Application payment ?']}")

                # Display document status here
                document_status = check_document_status(student_name)
                st.subheader("Document Status")
                for doc_type, status_info in document_status.items():
                    color = "green" if status_info['status'] else "red"
                    st.write(f"{doc_type}: <span style='color:{color};'>{'✔️' if status_info['status'] else '❌'}</span>", unsafe_allow_html=True)
                    if status_info['status']:
                        for file in status_info['files']:
                            st.write(f"- [{file['name']}]({file['webViewLink']})")

        else:
            st.info("No students found matching the search criteria.")

        st.header("📊 Dashboard - All Clients")

        # Ensure the data frame is not empty before creating the chart
        if not data.empty and 'Current Step' in data.columns:
            step_counts = data['Current Step'].value_counts()

            try:
                fig = px.bar(
                    step_counts,
                    x=step_counts.index,
                    y=step_counts.values,
                    labels={'x': 'Application Step', 'y': 'Number of Students'},
                    title='Students per Application Step'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0.05)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"An error occurred while creating the chart: {str(e)}")
        else:
            st.error("No data available for creating the chart. Please check your Google Sheets connection and data.")

    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()
