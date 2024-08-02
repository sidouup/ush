import os
import json
import gspread
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import plotly.express as px
import functools
import logging
import asyncio
import aiohttp
import threading
import numpy as np
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def on_student_select():
    st.session_state.student_changed = True

def reload_data(spreadsheet_id):
    data = load_data(spreadsheet_id)
    st.session_state['data'] = data
    return data

# Caching decorator
def cache_with_timeout(timeout_minutes=60):
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if datetime.now() - timestamp < timedelta(minutes=timeout_minutes):
                    return result
            result = func(*args, **kwargs)
            cache[key] = (result, datetime.now())
            return result
        return wrapper
    return decorator

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Drive service
@st.cache_resource
@cache_with_timeout(timeout_minutes=60)
def get_google_drive_service():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# Authenticate and build the Google Sheets service
@st.cache_resource
@cache_with_timeout(timeout_minutes=60)
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to upload a file to Google Drive
@cache_with_timeout(timeout_minutes=5)
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
    file_id = file.get('id')
    if file_id:
        st.session_state.upload_success = True
        return file_id
    return None

# Function to load data from Google Sheets
def load_data(spreadsheet_id):
    sheet_headers = {
        'ALL': [
            'DATE', 'First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 
            'Emergency contact N°', 'Chosen School', 'Specialite', 'Duration', 
            'Payment Amount', 'Sevis payment ?', 'Application payment ?', 'DS-160 maker', 
            'Password DS-160', 'Secret Q.', 'School Entry Date', 'Entry Date in the US', 
            'ADDRESS in the U.S', 'E-MAIL RDV', 'PASSWORD RDV', 'EMBASSY ITW. DATE', 
            'Attempts', 'Visa Result', 'Agent', 'Note', 'Stage'
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
                combined_data = pd.concat([combined_data, df], ignore_index=True)
        
        combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
        combined_data.reset_index(drop=True, inplace=True)

        return combined_data
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

# Function to save data to Google Sheets (batch update)
def save_data(df, spreadsheet_id, sheet_name):
    def replace_invalid_floats(val):
        if isinstance(val, float):
            if pd.isna(val) or np.isinf(val):
                return None
        return val

    # Replace NaN and inf values with None
    df = df.applymap(replace_invalid_floats)

    # Replace [pd.NA, pd.NaT, float('inf'), float('-inf')] with None
    df = df.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], None)

    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    
    # Get the number of columns in the sheet
    sheet_columns = len(sheet.row_values(1))
    
    # Limit the DataFrame to the number of columns in the sheet
    df = df.iloc[:, :sheet_columns]
    
    # Prepare the data for batch update
    values = [df.columns.tolist()] + df.values.tolist()
    
    # Calculate the last column letter
    if sheet_columns <= 26:
        last_column = string.ascii_uppercase[sheet_columns - 1]
    else:
        last_column = string.ascii_uppercase[(sheet_columns - 1) // 26 - 1] + string.ascii_uppercase[(sheet_columns - 1) % 26]

    # Perform batch update
    sheet.batch_update([{
        'range': f'A1:{last_column}{len(values)}',
        'values': values
    }])

    # Log the number of columns in the DataFrame and the sheet
    print(f"DataFrame columns: {len(df.columns)}, Sheet columns: {sheet_columns}")

def clear_cache_and_rerun():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

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

@cache_with_timeout(timeout_minutes=5)
def check_folder_exists(folder_name, parent_id=None):
    try:
        service = get_google_drive_service()
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        folders = results.get('files', [])
        if folders:
            return folders[0].get('id')
        else:
            return None
    except Exception as e:
        logger.error(f"An error occurred while checking if folder exists: {str(e)}")
        return None

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
@cache_with_timeout(timeout_minutes=5)
def check_file_exists(file_name, folder_id):
    service = get_google_drive_service()
    query = f"name='{file_name}' and '{folder_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files &#8203;:citation[oaicite:0]{index=0}&#8203;(id, name)').execute()
    files = results.get('files', [])
    return bool(files)

# Function to handle file upload and folder creation
def handle_file_upload(student_name, document_type, uploaded_file):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'  # Use the provided parent folder ID
    
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    if not student_folder_id:
        student_folder_id = create_folder_in_drive(student_name, parent_folder_id)
    
    document_folder_id = check_folder_exists(document_type, student_folder_id)
    if not document_folder_id:
        document_folder_id = create_folder_in_drive(document_type, student_folder_id)
    
    file_name = uploaded_file.name
    
    # Ensure no double extensions
    if file_name.lower().endswith('.pdf.pdf'):
        file_name = file_name[:-4]
    
    if not check_file_exists(file_name, document_folder_id):
        with st.spinner(f"Uploading {file_name}..."):
            temp_file_path = f"/tmp/{file_name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            mime_type = uploaded_file.type
            file_id = upload_file_to_drive(temp_file_path, mime_type, document_folder_id)
            os.remove(temp_file_path)
        if file_id:
            st.success(f"{file_name} uploaded successfully!")
            if 'document_status_cache' in st.session_state:
                st.session_state['document_status_cache'].pop(student_name, None)
            st.rerun()
            return file_id
    else:
        st.warning(f"{file_name} already exists for this student.")
    
    return None

async def fetch_document_status(session, document_type, student_folder_id, service):
    document_folder_id = await check_folder_exists_async(document_type, student_folder_id, service)
    if document_folder_id:
        files = await list_files_in_folder_async(document_folder_id, service)
        return document_type, bool(files), files
    return document_type, False, []

async def check_document_status_async(student_name, service):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'
    student_folder_id = await check_folder_exists_async(student_name, parent_folder_id, service)
    
    document_types = ["Passport", "Bank Statement", "Financial Letter", 
                      "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                      "SEVIS Receipt", "SEVIS"]
    document_status = {doc_type: {'status': False, 'files': []} for doc_type in document_types}

    if not student_folder_id:
        logger.info(f"Student folder not found for {student_name}")
        return document_status

    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_document_status(session, document_type, student_folder_id, service)
            for document_type in document_types
        ]
        results = await asyncio.gather(*tasks)
        for doc_type, status, files in results:
            document_status[doc_type] = {'status': status, 'files': files}
            logger.info(f"Document status for {doc_type}: {status}, Files: {files}")
    
    return document_status

async def check_folder_exists_async(folder_name, parent_id, service):
    try:
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        folders = results.get('files', [])
        return folders[0].get('id') if folders else None
    except Exception as e:
        logger.error(f"An error occurred while checking if folder exists: {str(e)}")
        return None

async def list_files_in_folder_async(folder_id, service):
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"An error occurred while listing files in folder: {str(e)}")
        return []

def trash_file_in_drive(file_id, student_name):
    service = get_google_drive_service()
    try:
        # Move the file to the trash
        file = service.files().update(
            fileId=file_id,
            body={"trashed": True}
        ).execute()
        
        # Clear the document status cache for this student
        if 'document_status_cache' in st.session_state:
            st.session_state['document_status_cache'].pop(student_name, None)
        
        return True
    
    except Exception as e:
        st.error(f"An error occurred while moving the file to trash: {str(e)}")
        return False

def get_document_status(student_name):
    if 'document_status_cache' not in st.session_state:
        st.session_state['document_status_cache'] = {}
    if student_name in st.session_state['document_status_cache']:
        return st.session_state['document_status_cache'][student_name]
    else:
        service = get_google_drive_service()
        document_status = asyncio.run(check_document_status_async(student_name, service))
        st.session_state['document_status_cache'][student_name] = document_status
        return document_status

# Debouncing inputs for edit mode
debounce_lock = threading.Lock()

def debounce(func, wait=0.5):
    def debounced(*args, **kwargs):
        def call_it():
            with debounce_lock:
                func(*args, **kwargs)
        if hasattr(debounced, '_timer'):
            debounced._timer.cancel()
        debounced._timer = threading.Timer(wait, call_it)
        debounced._timer.start()
    return debounced

@debounce
def update_student_data(*args, **kwargs):
    pass

# Main function
def main():
    st.set_page_config(page_title="Student Application Tracker", layout="wide")
    
    if 'student_changed' not in st.session_state:
        st.session_state.student_changed = False

    if 'upload_success' not in st.session_state:
        st.session_state.upload_success = False

    if 'selected_student' not in st.session_state:
        st.session_state.selected_student = ""

    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Personal"

    # Check if we need to refresh the page
    if st.session_state.upload_success:
        st.session_state.upload_success = False
        st.rerun()

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
            padding: 10px;
        }
        .stExpander {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 10px;
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
        .stTextInput input {
            font-size: 1rem;
            padding: 10px;
            margin-bottom: 10px;
        }
        .progress-container {
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .progress-bar {
            height: 20px;
            background-color: #4caf50;
            border-radius: 10px;
            transition: width 0.5s ease-in-out;
            text-align: center;
            line-height: 20px;
            color: white;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stCard" style="text-align: center;">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" width="150" height="150">
        <h1>The Us House</h1>
    </div>
    """, unsafe_allow_html=True)

    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    
    if 'data' not in st.session_state or st.session_state.get('reload_data', False):
        data = load_data(spreadsheet_id)
        st.session_state['data'] = data
        st.session_state['reload_data'] = False
    else:
        data = st.session_state['data']

    if not data.empty:
        current_steps = ["All"] + list(data['Stage'].unique())
        status_filter = st.selectbox("Filter by Stage", current_steps, key="status_filter")
        filtered_data = data if status_filter == "All" else data[data['Stage'] == status_filter]
        student_names = filtered_data['Student Name'].tolist()

        st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
        col2, col1, col3 = st.columns([3, 2, 3])

        with col2:
            search_query = st.selectbox(
                "🔍 Search for a student (First or Last Name)",
                options=student_names,
                key="search_query",
                index=student_names.index(st.session_state.selected_student) if st.session_state.selected_student in student_names else 0,
                on_change=on_student_select
            )
            # After the selectbox:
            if st.session_state.student_changed or st.session_state.selected_student != search_query:
                st.session_state.selected_student = search_query
                st.session_state.student_changed = False
                st.rerun()

        with col1:
            st.subheader("Application Status")
            if not filtered_data.empty:
                selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                steps = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.', 'SEVIS', 'CLIENTS ']
                current_step = selected_student['Stage'] if not filtered_data.empty else "Unknown"
                step_index = steps.index(current_step) if current_step in steps else 0
                progress = ((step_index + 1) / len(steps)) * 100
        
                progress_bar = f"""
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress}%;">
                        {int(progress)}%
                    </div>
                </div>
                """
                st.markdown(progress_bar, unsafe_allow_html=True)
                
                # Date of Payment
                date_of_payment = selected_student['DATE'] if not filtered_data.empty else None
                if date_of_payment:
                    try:
                        date_of_payment = pd.to_datetime(date_of_payment).strftime('%d %B %Y')
                    except ValueError:
                        date_of_payment = "Invalid Date"
                st.write(f"**📆 Date of Payment:** {date_of_payment}")
        
                st.write(f"**🚩 Current Stage:** {current_step}")
        
                # Agent
                agent = selected_student['Agent'] if not filtered_data.empty else "Unknown"
                st.write(f"**🧑‍💼 Agent:** {agent}")
                
                # SEVIS Payment
                sevis_payment = selected_student['Sevis payment ?'] if not filtered_data.empty else "No"
                sevis_icon = "✅" if sevis_payment == "YES" else "❌"
                st.write(f"**💲 SEVIS Payment:** {sevis_icon} ({sevis_payment})")
        
                # Application Payment
                application_payment = selected_student['Application payment ?'] if not filtered_data.empty else "No"
                application_icon = "✅" if application_payment == "YES" else "❌"
                st.write(f"**💸 Application Payment:** {application_icon} ({application_payment})")
        
                # Visa Status
                visa_status = selected_student['Visa Result'] if not filtered_data.empty else "Unknown"
                st.write(f"**🛂 Visa Status:** {visa_status}")

                entry_date = selected_student['School Entry Date'] if not filtered_data.empty else "Unknown"
                st.write(f"**🏫 School Entry Date:** {entry_date}")

                # Days until Interview
                interview_date = selected_student['EMBASSY ITW. DATE'] if not filtered_data.empty else None
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("📅 Days until interview", days_remaining)
                else:
                    st.metric("📅 Days until interview", "N/A")
                
            else:
                st.write("No data available for the current filters.")

        with col3:
            selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
            student_name = selected_student['Student Name']
        
            document_status = get_document_status(student_name)
            st.subheader("Document Status")
        
            for doc_type, status_info in document_status.items():
                icon = "✅" if status_info['status'] else "❌"
                col1, col2 = st.columns([9, 1])
                with col1:
                    st.markdown(f"**{icon} {doc_type}**")
                    for file in status_info['files']:
                        st.markdown(f"- [{file['name']}]({file['webViewLink']})")
                if status_info['status']:
                    if status_info['status']:
                        with col2:
                            if st.button("🗑️", key=f"delete_{status_info['files'][0]['id']}", help="Delete file"):
                                file_id = status_info['files'][0]['id']
                                if trash_file_in_drive(file_id, student_name):
                                    st.session_state['reload_data'] = True
                                    clear_cache_and_rerun()
                else:
                    with col2:
                        st.markdown("")
                                    
        if not filtered_data.empty:
            selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
            student_name = selected_student['Student Name']

            edit_mode = st.checkbox("Edit Mode", value=False)

            # Tabs for student information
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Personal", "School", "Embassy", "Payment", "Documents"])
            
            with tab1:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📋 Personal Information")
                if edit_mode:
                    first_name = st.text_input("First Name", selected_student['First Name'], key="first_name", on_change=update_student_data)
                    last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name", on_change=update_student_data)
                    phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number", on_change=update_student_data)
                    email = st.text_input("Email", selected_student['E-mail'], key="email", on_change=update_student_data)
                    emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact", on_change=update_student_data)
                    address = st.text_input("Address", selected_student['Address'], key="address", on_change=update_student_data)
                    attempts = st.text_input("Attempts", selected_student['Attempts'], key="attempts", on_change=update_student_data)
                else:
                    st.write(f"**First Name:** {selected_student['First Name']}")
                    st.write(f"**Last Name:** {selected_student['Last Name']}")
                    st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                    st.write(f"**Email:** {selected_student['E-mail']}")
                    st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                    st.write(f"**Address:** {selected_student['Address']}")
                    st.write(f"**Attempts:** {selected_student['Attempts']}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab2:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🏫 School Information")
                if edit_mode:
                    chosen_school = st.text_input("Chosen School", selected_student['Chosen School'], key="chosen_school", on_change=update_student_data)
                    specialite = st.text_input("Specialite", selected_student['Specialite'], key="specialite", on_change=update_student_data)
                    duration = st.text_input("Duration", selected_student['Duration'], key="duration", on_change=update_student_data)
                    school_entry_date = st.text_input("School Entry Date", selected_student['School Entry Date'], key="school_entry_date", on_change=update_student_data)
                    entry_date_in_us = st.text_input("Entry Date in the US", selected_student['Entry Date in the US'], key="entry_date_in_us", on_change=update_student_data)
                else:
                    st.write(f"**Chosen School:** {selected_student['Chosen School']}")
                    st.write(f"**Specialite:** {selected_student['Specialite']}")
                    st.write(f"**Duration:** {selected_student['Duration']}")
                    st.write(f"**School Entry Date:** {selected_student['School Entry Date']}")
                    st.write(f"**Entry Date in the US:** {selected_student['Entry Date in the US']}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab3:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🏛️ Embassy Information")
                if edit_mode:
                    address_us = st.text_input("Address in the U.S", selected_student['ADDRESS in the U.S'], key="address_us", on_change=update_student_data)


                    email_rdv = st.text_input("E-mail RDV", selected_student['E-MAIL RDV'], key="email_rdv", on_change=update_student_data)
                    password_rdv = st.text_input("Password RDV", selected_student['PASSWORD RDV'], key="password_rdv", on_change=update_student_data)
                    embassy_itw_date = st.text_input("Embassy Interview Date", selected_student['EMBASSY ITW. DATE'], key="embassy_itw_date", on_change=update_student_data)
                    ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker", on_change=update_student_data)
                    password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160", on_change=update_student_data)
                    secret_q = st.text_input("Secret Question", selected_student['Secret Q.'], key="secret_q", on_change=update_student_data)
                else:
                    st.write(f"**Address in the U.S:** {selected_student['ADDRESS in the U.S']}")
                    st.write(f"**E-mail RDV:** {selected_student['E-MAIL RDV']}")
                    st.write(f"**Password RDV:** {selected_student['PASSWORD RDV']}")
                    st.write(f"**Embassy Interview Date:** {selected_student['EMBASSY ITW. DATE']}")
                    st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                    st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                    st.write(f"**Secret Question:** {selected_student['Secret Q.']}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab4:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("💰 Payment Information")
                if edit_mode:
                    payment_date = st.text_input("Payment Date", selected_student['DATE'], key="payment_date", on_change=update_student_data)
                    payment_method = st.text_input("Payment Method", selected_student['Payment Amount'], key="payment_method", on_change=update_student_data)
                    sevis_payment = st.text_input("Sevis Payment", selected_student['Sevis payment ?'], key="sevis_payment", on_change=update_student_data)
                    application_payment = st.text_input("Application Payment", selected_student['Application payment ?'], key="application_payment", on_change=update_student_data)
                else:
                    st.write(f"**Payment Date:** {selected_student['DATE']}")
                    st.write(f"**Payment Method:** {selected_student['Payment Amount']}")
                    st.write(f"**Sevis Payment:** {selected_student['Sevis payment ?']}")
                    st.write(f"**Application Payment:** {selected_student['Application payment ?']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with tab5:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📂 Document Upload and Status")
                document_type = st.selectbox("Select Document Type", 
                                             ["Passport", "Bank Statement", "Financial Letter", 
                                              "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                                              "SEVIS Receipt", "SEVIS"], 
                                             key="document_type")
                uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png", "pdf"], key="uploaded_file")
                
                if uploaded_file and st.button("Upload Document"):
                    file_id = handle_file_upload(student_name, document_type, uploaded_file)
                    if file_id:
                        st.success(f"{document_type} uploaded successfully!")
                        if 'document_status_cache' in st.session_state:
                            st.session_state['document_status_cache'].pop(student_name, None)
                        clear_cache_and_rerun()  # Clear cache and rerun the app
                    else:
                        st.error("An error occurred while uploading the document.")

            if edit_mode and st.button("Save Changes"):
                updated_student = {
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Phone N°': phone_number,
                    'E-mail': email,
                    'Emergency contact N°': emergency_contact,
                    'Address': address,
                    'Attempts': attempts,
                    'Chosen School': chosen_school,
                    'Specialite': specialite,
                    'Duration': duration,
                    'School Entry Date': school_entry_date,
                    'Entry Date in the US': entry_date_in_us,
                    'ADDRESS in the U.S': address_us,
                    'E-MAIL RDV': email_rdv,
                    'PASSWORD RDV': password_rdv,
                    'EMBASSY ITW. DATE': embassy_itw_date,
                    'DS-160 maker': ds160_maker,
                    'Password DS-160': password_ds160,
                    'Secret Q.': secret_q,
                    'Visa Result': visa_status,
                    'Stage': current_step,
                    'DATE': payment_date,
                    'Payment Amount': payment_method,
                    'Sevis payment ?': sevis_payment,
                    'Application payment ?': application_payment,
                }
                
                # Update the data in the DataFrame
                for key, value in updated_student.items():
                    filtered_data.loc[filtered_data['Student Name'] == student_name, key] = value

                # Save the updated data back to Google Sheets
                save_data(filtered_data, spreadsheet_id, 'ALL')
                st.success("Changes saved successfully!")
                clear_cache_and_rerun()  # Clear cache and rerun the app

        else:
            st.info("No students found matching the search criteria.")

    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()
                    email_rdv = st.text_input("E-mail RDV", selected_student['E-MAIL RDV'], key="email_rdv", on_change=update_student_data)
                    password_rdv = st.text_input("Password RDV", selected_student['PASSWORD RDV'], key="password_rdv", on_change=update_student_data)
                    embassy_itw_date = st.text_input("Embassy Interview Date", selected_student['EMBASSY ITW. DATE'], key="embassy_itw_date", on_change=update_student_data)
                    ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker", on_change=update_student_data)
                    password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160", on_change=update_student_data)
                    secret_q = st.text_input("Secret Question", selected_student['Secret Q.'], key="secret_q", on_change=update_student_data)
                else:
                    st.write(f"**Address in the U.S:** {selected_student['ADDRESS in the U.S']}")
                    st.write(f"**E-mail RDV:** {selected_student['E-MAIL RDV']}")
                    st.write(f"**Password RDV:** {selected_student['PASSWORD RDV']}")
                    st.write(f"**Embassy Interview Date:** {selected_student['EMBASSY ITW. DATE']}")
                    st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                    st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                    st.write(f"**Secret Question:** {selected_student['Secret Q.']}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with tab4:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("💰 Payment Information")
                if edit_mode:
                    payment_date = st.text_input("Payment Date", selected_student['DATE'], key="payment_date", on_change=update_student_data)
                    payment_method = st.text_input("Payment Method", selected_student['Payment Amount'], key="payment_method", on_change=update_student_data)
                    sevis_payment = st.text_input("Sevis Payment", selected_student['Sevis payment ?'], key="sevis_payment", on_change=update_student_data)
                    application_payment = st.text_input("Application Payment", selected_student['Application payment ?'], key="application_payment", on_change=update_student_data)
                else:
                    st.write(f"**Payment Date:** {selected_student['DATE']}")
                    st.write(f"**Payment Method:** {selected_student['Payment Amount']}")
                    st.write(f"**Sevis Payment:** {selected_student['Sevis payment ?']}")
                    st.write(f"**Application Payment:** {selected_student['Application payment ?']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with tab5:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📂 Document Upload and Status")
                document_type = st.selectbox("Select Document Type", 
                                             ["Passport", "Bank Statement", "Financial Letter", 
                                              "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                                              "SEVIS Receipt", "SEVIS"], 
                                             key="document_type")
                uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png", "pdf"], key="uploaded_file")
                
                if uploaded_file and st.button("Upload Document"):
                    file_id = handle_file_upload(student_name, document_type, uploaded_file)
                    if file_id:
                        st.success(f"{document_type} uploaded successfully!")
                        if 'document_status_cache' in st.session_state:
                            st.session_state['document_status_cache'].pop(student_name, None)
                        clear_cache_and_rerun()  # Clear cache and rerun the app
                    else:
                        st.error("An error occurred while uploading the document.")

            if edit_mode and st.button("Save Changes"):
                updated_student = {
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Phone N°': phone_number,
                    'E-mail': email,
                    'Emergency contact N°': emergency_contact,
                    'Address': address,
                    'Attempts': attempts,
                    'Chosen School': chosen_school,
                    'Specialite': specialite,
                    'Duration': duration,
                    'School Entry Date': school_entry_date,
                    'Entry Date in the US': entry_date_in_us,
                    'ADDRESS in the U.S': address_us,
                    'E-MAIL RDV': email_rdv,
                    'PASSWORD RDV': password_rdv,
                    'EMBASSY ITW. DATE': embassy_itw_date,
                    'DS-160 maker': ds160_maker,
                    'Password DS-160': password_ds160,
                    'Secret Q.': secret_q,
                    'Visa Result': visa_status,
                    'Stage': current_step,
                    'DATE': payment_date,
                    'Payment Amount': payment_method,
                    'Sevis payment ?': sevis_payment,
                    'Application payment ?': application_payment,
                }
                
                # Update the data in the DataFrame
                for key, value in updated_student.items():
                    filtered_data.loc[filtered_data['Student Name'] == student_name, key] = value

                # Save the updated data back to Google Sheets
                save_data(filtered_data, spreadsheet_id, 'ALL')
                st.success("Changes saved successfully!")
                clear_cache_and_rerun()  # Clear cache and rerun the app

        else:
            st.info("No students found matching the search criteria.")

    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()


