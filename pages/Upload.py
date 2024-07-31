import os
import json
import gspread
import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import plotly.express as px
import logging


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

# Function to upload a file to Google Drive
def upload_file_to_drive(file_path, mime_type, folder_id=None):
    service = get_google_drive_service()
    file_metadata = {'name': os.path.basename(file_path)}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, mimetype=mime_type)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id').execute()
    
    return file.get('id')

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
        st.write("Google Sheets client initialized successfully.")
        sheet = client.open_by_key(spreadsheet_id)
        st.write("Opened spreadsheet successfully.")
        
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
        st.write("Data loaded successfully.")
        return combined_data
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

# Function to save data to Google Sheets
def save_data(df, spreadsheet_id, sheet_name):
    df = df.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], '')

    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.worksheet(sheet_name)
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

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

# Function to create a new folder in Google Drive
def create_folder_in_drive(folder_name, parent_id=None):
    service = get_google_drive_service()
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        folder_metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

# Function to check if a file exists in a folder
def check_file_exists(file_name, folder_id):
    service = get_google_drive_service()
    query = f"name='{file_name}' and '{folder_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return bool(files)

# Function to handle file upload and folder creation
def handle_file_upload(student_name, document_type, uploaded_files):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'  # Use the provided parent folder ID
    
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    if not student_folder_id:
        student_folder_id = create_folder_in_drive(student_name, parent_folder_id)
    st.write(f"Student folder ID for {student_name}: {student_folder_id}")

    document_folder_id = check_folder_exists(document_type, student_folder_id)
    if not document_folder_id:
        document_folder_id = create_folder_in_drive(document_type, student_folder_id)
    st.write(f"Document folder ID for {document_type}: {document_folder_id}")

    uploaded_file_ids = []
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        
        # Ensure no double extensions
        if file_name.lower().endswith('.pdf.pdf'):
            file_name = file_name[:-4]
        st.write(f"File name to be uploaded: {file_name}")

        if not check_file_exists(file_name, document_folder_id):
            with st.spinner(f"Uploading {file_name}..."):
                temp_file_path = f"/tmp/{file_name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                mime_type = uploaded_file.type
                file_id = upload_file_to_drive(temp_file_path, mime_type, document_folder_id)
                if file_id:
                    uploaded_file_ids.append(file_id)
                os.remove(temp_file_path)
            st.success(f"{file_name} uploaded successfully!")
        else:
            st.warning(f"{file_name} already exists for this student.")
    
    return uploaded_file_ids
def check_document_status(student_name):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    if not student_folder_id:
        return {}

    document_types = ["Passport", "Bank Statement", "Financial Letter", "Transcripts", "Diplomas", "English Test"]
    document_status = {}
    for document_type in document_types:
        document_folder_id = check_folder_exists(document_type, student_folder_id)
        document_status[document_type] = bool(document_folder_id and check_file_exists_in_folder(document_folder_id))
    
    return document_status

def check_file_exists_in_folder(folder_id):
    service = get_google_drive_service()
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    return bool(results.get('files', []))

# Main function
def main():
    st.set_page_config(page_title="Student Application Tracker", layout="wide")

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
            font-weight: bold.
        }
        .stButton>button:hover {
            background-color: #ff6347.
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="display: flex; align-items: center;">
            <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
            <h1 style="color: #1E3A8A;">Student Application Tracker</h1>
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
                    first_name = st.text_input("First Name", selected_student['First Name'], key="first_name")
                    last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name")
                    phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number")
                    email = st.text_input("Email", selected_student['E-mail'], key="email")
                    emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact")
                    address = st.text_input("Address", selected_student['Address'], key="address")
                    attempts = st.text_input("Attempts", selected_student['Attempts'], key="attempts")
                
                with st.expander("🏫 School Information", expanded=True):
                    chosen_school = st.text_input("Chosen School", selected_student['Chosen School'], key="chosen_school")
                    duration = st.text_input("Duration", selected_student['Duration'], key="duration")
                    school_entry_date = st.text_input("School Entry Date", selected_student['School Entry Date'], key="school_entry_date")
                    entry_date_in_us = st.text_input("Entry Date in the US", selected_student['Entry Date in the US'], key="entry_date_in_us")
                
                with st.expander("🏛️ Embassy Information", expanded=True):
                    address_us = st.text_input("Address in the U.S", selected_student['ADDRESS in the U.S'], key="address_us")
                    email_rdv = st.text_input("E-mail RDV", selected_student[' E-MAIL RDV'], key="email_rdv")
                    password_rdv = st.text_input("Password RDV", selected_student['PASSWORD RDV'], key="password_rdv")
                    embassy_itw_date = st.text_input("Embassy Interview Date", selected_student['EMBASSY ITW. DATE'], key="embassy_itw_date")
                    ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker")
                    password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160")
                    secret_q = st.text_input("Secret Question", selected_student['Secret Q.'], key="secret_q")
                
                with st.expander("📂 Upload Documents", expanded=True):
                    document_type = st.selectbox("Select Document Type", ["Passport", "Bank Statement", "Financial Letter", "Transcripts", "Diplomas", "English Test"], key="document_type")
                    uploaded_files = st.file_uploader("Upload Student Documents", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True, key="uploaded_files")
                
                    if st.button("Upload Files"):
                        if uploaded_files:
                            uploaded_file_ids = handle_file_upload(student_name, document_type, uploaded_files)
                            if uploaded_file_ids:
                                st.success(f"Files uploaded successfully! File IDs: {', '.join(uploaded_file_ids)}")
                            else:
                                st.error("An error occurred while uploading files.")
                        else:
                            st.error("Please select files to upload.")
                                            
            with col2:
                st.subheader("Application Status")
                
                visa_status = st.selectbox(
                    "Visa Status",
                    ['Denied', 'Approved', 'Not our school partner', 'Unknown'],
                    index=['Denied', 'Approved', 'Not our school partner', 'Unknown'].index(get_visa_status(selected_student.get('Visa Result', 'Unknown'))),
                    key="visa_status"
                )
                
                current_step = st.text_input("Current Step", selected_student['Current Step'], key="current_step")
                
                interview_date = st.text_input("Embassy Interview Date", selected_student['EMBASSY ITW. DATE'], key="interview_date")
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("Days until interview", days_remaining)
                else:
                    st.metric("Days until interview", "N/A")
                
                with st.expander("💰 Payment Information", expanded=True):
                    payment_date = st.text_input("Payment Date", selected_student['DATE'], key="payment_date")
                    payment_method = st.text_input("Payment Method", selected_student['Payment Method '], key="payment_method")
                    sevis_payment = st.text_input("Sevis Payment", selected_student['Sevis payment ? '], key="sevis_payment")
                    application_payment = st.text_input("Application Payment", selected_student['Application payment ?'], key="application_payment")

                # Display document status here
                document_status = check_document_status(student_name)
                st.subheader("Document Status")
                for doc_type, status in document_status.items():
                    color = "green" if status else "red"
                    st.write(f"{doc_type}: <span style='color:{color};'>{'✔️' if status else '❌'}</span>", unsafe_allow_html=True)

            if st.button("Save Changes"):
                updated_student = {
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Phone N°': phone_number,
                    'E-mail': email,
                    'Emergency contact N°': emergency_contact,
                    'Address': address,
                    'Attempts': attempts,
                    'Chosen School': chosen_school,
                    'Duration': duration,
                    'School Entry Date': school_entry_date,
                    'Entry Date in the US': entry_date_in_us,
                    'ADDRESS in the U.S': address_us,
                    ' E-MAIL RDV': email_rdv,
                    'PASSWORD RDV': password_rdv,
                    'EMBASSY ITW. DATE': embassy_itw_date,
                    'DS-160 maker': ds160_maker,
                    'Password DS-160': password_ds160,
                    'Secret Q.': secret_q,
                    'Visa Result': visa_status,
                    'Current Step': current_step,
                    'DATE': payment_date,
                    'Payment Method ': payment_method,
                    'Sevis payment ? ': sevis_payment,
                    'Application payment ?': application_payment,
                }
                
                for key, value in updated_student.items():
                    data.at[selected_index, key] = value

                save_data(data, spreadsheet_id, selected_student['Current Step'])
                st.success("Changes saved successfully!")

        else:
            st.info("No students found matching the search criteria.")

        st.header("📊 Dashboard - All Clients")

        # Ensure the data frame is not empty before creating the chart
        if not data.empty and 'Current Step' in data.columns:
            step_counts = data['Current Step'].value_counts()
            st.write("Step counts calculated successfully.")

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
                st.write("Chart rendered successfully.")
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
