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
import time
import re

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

def load_data(spreadsheet_id):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(spreadsheet_id)
        
        combined_data = pd.DataFrame()
        
        for worksheet in sheet.worksheets():
            # Load all records without specifying headers
            data = worksheet.get_all_values()
            
            # Convert the data to a DataFrame
            df = pd.DataFrame(data)
            
            # Set the first row as the header
            df.columns = df.iloc[0]
            df = df[1:]  # Remove the first row since it's now the header
            
            # Treat everything as a string
            df = df.astype(str)
            
            # Combine data from all worksheets
            combined_data = pd.concat([combined_data, df], ignore_index=True)
        
        # Handle duplicates by appending a number to duplicate names
        combined_data['Student Name'] = combined_data['Student Name'].astype(str)
        name_counts = combined_data['Student Name'].value_counts()
        for name, count in name_counts.items():
            if count > 1:
                indices = combined_data[combined_data['Student Name'] == name].index
                for i, idx in enumerate(indices):
                    combined_data.at[idx, 'Student Name'] = f"{name} {i+1}"
        
        combined_data.reset_index(drop=True, inplace=True)

        return combined_data
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return pd.DataFrame()

def save_data(df, spreadsheet_id, sheet_name):
    logger.info("Attempting to save changes")

    # Handle duplicates by appending a number to duplicate names
    df['Student Name'] = df['Student Name'].astype(str)
    name_counts = df['Student Name'].value_counts()
    for name, count in name_counts.items():
        if count > 1:
            indices = df[df['Student Name'] == name].index
            for i, idx in enumerate(indices):
                df.at[idx, 'Student Name'] = f"{name} {i+1}"
    
    try:
        client = get_google_sheet_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.worksheet(sheet_name)

        # Convert DATE column back to string for saving
        date_columns = ['DATE', 'School Entry Date', 'Entry Date in the US', 'EMBASSY ITW. DATE']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')  # Ensure DATE is datetime
                df[col] = df[col].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Replace problematic values with a placeholder
        df.replace([np.inf, -np.inf, np.nan], 'NaN', inplace=True)

        # Clear the existing sheet
        sheet.clear()

        # Update the sheet with new data, including the "Student Name" column
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False

def format_date(date_string):
    if pd.isna(date_string) or date_string == 'NaT':
        return "Not set"
    try:
        # Parse the date string, assuming day first format
        date = pd.to_datetime(date_string, errors='coerce', dayfirst=True)
        return date.strftime('%d %B %Y') if not pd.isna(date) else "Invalid Date"
    except:
        return "Invalid Date"

def clear_cache_and_rerun():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# Function to calculate days until interview
def calculate_days_until_interview(interview_date):
    try:
        # Parse the interview date, assuming day first format
        interview_date = pd.to_datetime(interview_date, format='%d/%m/%Y %H:%M:%S', dayfirst=True)
        if pd.isnull(interview_date):
            return None
        today = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
        days_remaining = (interview_date - today).days
        return days_remaining
    except Exception as e:
        logger.error(f"Error calculating days until interview: {str(e)}")
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
from googleapiclient.errors import HttpError

@cache_with_timeout(timeout_minutes=5)
def check_file_exists(file_name, student_folder_id, document_type):
    service = get_google_drive_service()
    
    # First, find the document type folder within the student folder
    document_folder_query = f"name = '{document_type}' and '{student_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    document_folder_results = service.files().list(q=document_folder_query, spaces='drive', fields='files(id)').execute()
    document_folders = document_folder_results.get('files', [])
    
    if not document_folders:
        logger.info(f"Document folder '{document_type}' not found in student folder.")
        return False
    
    document_folder_id = document_folders[0]['id']
    
    # Now check for the file within the document type folder
    file_query = f"name = '{file_name}' and '{document_folder_id}' in parents and trashed = false"
    try:
        results = service.files().list(
            q=file_query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        files = results.get('files', [])
        file_exists = len(files) > 0
        logger.info(f"File '{file_name}' exists: {file_exists}")
        return file_exists
    except HttpError as error:
        logger.error(f"An error occurred while checking if file exists: {error}")
        return False

# Function to handle file upload and folder creation
def handle_file_upload(student_name, document_type, uploaded_file):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'  # Use the provided parent folder ID
    
    # Check if student folder exists, if not create it
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    if not student_folder_id:
        student_folder_id = create_folder_in_drive(student_name, parent_folder_id)
        logger.info(f"Created new folder for student: {student_name}")
    
    # Check if document type folder exists within student folder, if not create it
    document_folder_id = check_folder_exists(document_type, student_folder_id)
    if not document_folder_id:
        document_folder_id = create_folder_in_drive(document_type, student_folder_id)
        logger.info(f"Created new folder for document type: {document_type}")
    
    file_name = uploaded_file.name
    
    # Ensure no double extensions
    if file_name.lower().endswith('.pdf.pdf'):
        file_name = file_name[:-4]
    
    file_exists = check_file_exists(file_name, student_folder_id, document_type)
    if not file_exists:
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
        st.warning(f"{file_name} already exists for this student in the {document_type} folder.")
    
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
                      "SEVIS Receipt", "I20"]
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
    # Initialize other session state variables
    for key in ['visa_status', 'current_step', 'payment_date', 'payment_method', 'payment_type', 'compte', 'sevis_payment', 'application_payment']:
        if key not in st.session_state:
            st.session_state[key] = None

    # Check if we need to refresh the page
    if st.session_state.upload_success:
        st.session_state.upload_success = False
        st.rerun()

    st.markdown("""
    <style>
        /* Your existing CSS styling */
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

    # Combine First Name and Last Name for all rows
    data['Student Name'] = data['First Name'] + " " + data['Last Name']

    if not data.empty:
        current_steps = ["All"] + list(data['Stage'].unique())
        agents = ["All", "Nesrine", "Hamza", "Djazila","Nada"]
        school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English ",
                          "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                          "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
        attempts_options = ["All", "1 st Try", "2 nd Try", "3 rd Try"]
        Gender_options = ["Male", "Female"]

        st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filter = st.selectbox("Filter by Stage", current_steps, key="status_filter")
        with col2:
            agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
        with col3:
            school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
        with col4:
            attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")

        # Apply filters
        filtered_data = st.session_state['data'].copy()
        if status_filter != "All":
            filtered_data = filtered_data[filtered_data['Stage'] == status_filter]
        if agent_filter != "All":
            filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
        if school_filter != "All":
            filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
        if attempts_filter != "All":
            filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]

        # Combine First Name and Last Name for filtered data
        filtered_data['Student Name'] = filtered_data['First Name'] + " " + filtered_data['Last Name']

        student_names = filtered_data['Student Name'].tolist()
        
        if not filtered_data.empty:
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
                st.subheader("📝 Student Notes")
                
                # Get the current note for the selected student
                selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                selected_student_dict = selected_student.to_dict()
                current_note = selected_student['Note'] if 'Note' in selected_student else ""
            
                # Create a text area for note input
                new_note = st.text_area("Enter/Edit Note:", value=current_note, height=150, key="note_input")
            
                # Save button for the note
                if st.button("Save Note"):
                    # Update the note in the original DataFrame (not the filtered one)
                    st.session_state['data'].loc[st.session_state['data']['Student Name'] == search_query, 'Note'] = new_note
                    
                    # Save the updated data back to Google Sheets
                    save_data(st.session_state['data'], spreadsheet_id, 'ALL')
                    
                    st.success("Note saved successfully!")
                    
                    # Set a flag to reload data on next run
                    st.session_state['reload_data'] = True
                    
                    # Rerun the app to show updated data
                    st.rerun()
              

            
            with col1:
                st.subheader("Application Status")
                selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                steps = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.',  'CLIENTS ']
                current_step = selected_student['Stage']
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
                
                payment_date_str = selected_student['DATE']
                try:
                    payment_date = pd.to_datetime(payment_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                    payment_date_value = payment_date.strftime('%d %B %Y') if not pd.isna(payment_date) else "Not set"
                except AttributeError:
                    payment_date_value = "Not set"
                
                st.write(f"**📆 Date of Payment:** {payment_date_value}")
        
                st.write(f"**🚩 Current Stage:** {current_step}")
        
                # Agent
                agent = selected_student['Agent']
                st.write(f"**🧑‍💼 Agent:** {agent}")
                
                # SEVIS Payment
                sevis_payment = selected_student['Sevis payment ?']
                sevis_icon = "✅" if selected_student['Sevis payment ?'] == "YES" else "❌"
                st.write(f"**💲 SEVIS Payment:** {sevis_icon} ({sevis_payment})")
        
                # Application Payment
                application_payment = selected_student['Application payment ?']
                application_icon = "✅" if selected_student['Application payment ?'] == "YES" else "❌"
                st.write(f"**💸 Application Payment:** {application_icon} ({application_payment})")
        
                # Visa Status
                visa_status = selected_student['Visa Result']
                st.write(f"**🛂 Visa Status:** {visa_status}")
        
                # Find the section where we display the school entry date
                entry_date = format_date(selected_student['School Entry Date'])
                st.write(f"**🏫 School Entry Date:** {entry_date}")
        
                # Days until Interview
                interview_date = selected_student['EMBASSY ITW. DATE']
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("📅 Days until interview", days_remaining)
                else:
                    st.metric("📅 Days until interview", "N/A")
        
            with col3:
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
                        with col2:
                            if st.button("🗑️", key=f"delete_{status_info['files'][0]['id']}", help="Delete file"):
                                file_id = status_info['files'][0]['id']
                                if trash_file_in_drive(file_id, student_name):
                                    st.session_state['reload_data'] = True
                                    clear_cache_and_rerun()
        
        else:
            st.info("No students found matching the search criteria.")

                                    
        if not filtered_data.empty:
            selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
            student_name = selected_student['Student Name']

            edit_mode = st.toggle("Edit Mode", value=False)

            # Tabs for student information
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Personal", "School", "Embassy", "Payment","Stage", "Documents"])
            
            # Options for dropdowns
            school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                              "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago","BEA Huston","BIA Huston","OHLA Miami", "UCDEA","HAWAII","Not Partner", "Not yet"]
            
            payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
            School_paid_opt = ["YES", "NO"]
            Prep_ITW_opt = ["YES", "NO"]


            payment_type_options = ["Cash", "CCP", "Baridimob", "Bank"]
            compte_options = ["Mohamed", "Sid Ali"]
            yes_no_options = ["YES", "NO"]
            attempts_options = ["1st Try", "2nd Try", "3rd Try"]
            Gender_options = ["","Male", "Female"]

            
            with tab1:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📋 Personal Information")
                if edit_mode:
                    first_name = st.text_input("First Name", selected_student['First Name'], key="first_name", on_change=update_student_data)
                    last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name", on_change=update_student_data)
                    Age = st.text_input("Age", selected_student['Age'], key="Age", on_change=update_student_data)
                    Gender = st.selectbox(
                        "Gender", 
                        Gender_options, 
                        index=Gender_options.index(selected_student['Gender']) if selected_student['Gender'] in Gender_options else 0,
                        key="Gender", 
                        on_change=update_student_data
                    )
            
                    # Updated phone number input
                    phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number", on_change=update_student_data)
                    if phone_number and not re.match(r'^\+?[0-9]+$', phone_number):
                        st.warning("Phone number should only contain digits, and optionally start with a '+'")
                    
                    email = st.text_input("Email", selected_student['E-mail'], key="email", on_change=update_student_data)
                    
                    # Updated emergency contact input
                    emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact", on_change=update_student_data)
                    if emergency_contact and not re.match(r'^\+?[0-9]+$', emergency_contact):
                        st.warning("Emergency contact number should only contain digits, and optionally start with a '+'")
                    
                    address = st.text_input("Address", selected_student['Address'], key="address", on_change=update_student_data)
                    attempts = st.selectbox(
                        "Attempts", 
                        attempts_options, 
                        index=attempts_options.index(selected_student['Attempts']) if selected_student['Attempts'] in attempts_options else 0,
                        key="attempts", 
                        on_change=update_student_data
                    )
                    agentss = st.selectbox(
                    "Agent", 
                    agents, 
                    index=agents.index(selected_student['Agent']) if selected_student['Agent'] in attempts_options else 0,
                    key="Agent", 
                    on_change=update_student_data
                )
                else:
                    st.write(f"**First Name:** {selected_student['First Name']}")
                    st.write(f"**Last Name:** {selected_student['Last Name']}")
                    st.write(f"**Age:** {selected_student['Age']}")
                    st.write(f"**Gender:** {selected_student['Gender']}")
                    st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                    st.write(f"**Email:** {selected_student['E-mail']}")
                    st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                    st.write(f"**Address:** {selected_student['Address']}")
                    st.write(f"**Attempts:** {selected_student['Attempts']}")
                    st.write(f"**Agent:** {selected_student['Agent']}")
                st.markdown('</div>', unsafe_allow_html=True)
                    
                with tab2:
                    st.markdown('<div class="stCard">', unsafe_allow_html=True)
                    st.subheader("🏫 School Information")
                    if edit_mode:
                        chosen_school = st.selectbox("Chosen School", school_options, index=school_options.index(selected_student['Chosen School']) if selected_student['Chosen School'] in school_options else 0, key="chosen_school", on_change=update_student_data)
                        specialite = st.text_input("Specialite", selected_student['Specialite'], key="specialite", on_change=update_student_data)
                        duration = st.text_input("Duration", selected_student['Duration'], key="duration", on_change=update_student_data)
                        Bankstatment = st.text_input("BANK", selected_student['BANK'], key="Bankstatment", on_change=update_student_data)

                        school_entry_date = pd.to_datetime(selected_student['School Entry Date'], errors='coerce', dayfirst=True)
                        school_entry_date = st.date_input(
                            "School Entry Date",
                            value=school_entry_date if not pd.isna(school_entry_date) else None,
                            key="school_entry_date",
                            on_change=update_student_data
                        )

                        entry_date_in_us = pd.to_datetime(selected_student['Entry Date in the US'], errors='coerce', dayfirst=True)
                        entry_date_in_us = st.date_input(
                            "Entry Date in the US",
                            value=entry_date_in_us if not pd.isna(entry_date_in_us) else None,
                            key="entry_date_in_us",
                            on_change=update_student_data
                        )
                        School_Paid = st.selectbox(
                            "School Paid",
                            School_paid_opt,
                            index=School_paid_opt.index(selected_student['School Paid']) if selected_student['School Paid'] in School_paid_opt else 0,
                            key="School_Paid",
                            on_change=update_student_data
                        )
                    else:
                        st.write(f"**Chosen School:** {selected_student['Chosen School']}")
                        st.write(f"**Specialite:** {selected_student['Specialite']}")
                        st.write(f"**Duration:** {selected_student['Duration']}")
                        st.write(f"**Bank:** {selected_student['BANK']}")
                        st.write(f"**School Entry Date:** {format_date(selected_student['School Entry Date'])}")
                        st.write(f"**Entry Date in the US:** {format_date(selected_student['Entry Date in the US'])}")
                        st.write(f"**School Paid:** {selected_student['School Paid']}")
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab3:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🏛️ Embassy Information")
                if edit_mode:
                    address_us = st.text_input("Address in the U.S", selected_student['ADDRESS in the U.S'], key="address_us", on_change=update_student_data)
                    email_rdv = st.text_input("E-mail RDV", selected_student['E-MAIL RDV'], key="email_rdv", on_change=update_student_data)
                    password_rdv = st.text_input("Password RDV", selected_student['PASSWORD RDV'], key="password_rdv", on_change=update_student_data)

                    # Handle embassy interview date
                    embassy_itw_date_str = selected_student['EMBASSY ITW. DATE']
                    try:
                        embassy_itw_date = pd.to_datetime(embassy_itw_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                        embassy_itw_date_value = embassy_itw_date.date() if not pd.isna(embassy_itw_date) else None
                    except AttributeError:
                        embassy_itw_date_value = None

                    embassy_itw_date = st.date_input(
                        "Embassy Interview Date",
                        value=embassy_itw_date_value,
                        key="embassy_itw_date",
                        on_change=update_student_data
                    )

                    ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker", on_change=update_student_data)
                    password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160", on_change=update_student_data)
                    secret_q = st.text_input("Secret Question", selected_student['Secret Q.'], key="secret_q", on_change=update_student_data)
                    Prep_ITW = st.selectbox(
                        "Prep ITW",
                        Prep_ITW_opt,
                        index=Prep_ITW_opt.index(selected_student['Prep ITW']) if selected_student['Prep ITW'] in Prep_ITW_opt else 0,
                        key="Prep_ITW",
                        on_change=update_student_data
                    )

                else:
                    st.write(f"**Address in the U.S:** {selected_student['ADDRESS in the U.S']}")
                    st.write(f"**E-mail RDV:** {selected_student['E-MAIL RDV']}")
                    st.write(f"**Password RDV:** {selected_student['PASSWORD RDV']}")
                    st.write(f"**Embassy Interview Date:** {format_date(selected_student['EMBASSY ITW. DATE'])}")
                    st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                    st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                    st.write(f"**Secret Question:** {selected_student['Secret Q.']}")
                    st.write(f"**ITW Prep:** {selected_student['Prep ITW']}")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab4:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("💰 Payment Information")
                
                if edit_mode:
                    # Handling Payment Date
                    payment_date = selected_student_dict['DATE']
                    payment_date = st.date_input(
                        "Payment Date",
                        value=payment_date if pd.notna(payment_date) else None,
                        key="payment_date",
                        on_change=update_student_data
                    )
    
                    # Handling Payment Method Radio
                    st.write("Payment Method")
                    current_payment_method = selected_student_dict['Payment Amount'] if pd.notna(selected_student_dict['Payment Amount']) else payment_amount_options[0]
                    payment_method = st.radio(
                        "Payment Method",
                        payment_amount_options,
                        index=payment_amount_options.index(current_payment_method) if current_payment_method in payment_amount_options else 0,
                        key="payment_method",
                        on_change=update_student_data,
                        horizontal=True
                    )
    
                    # Handling Payment Type Radio
                    st.write("Payment Type")
                    current_payment_type = selected_student_dict['Payment Type'] if pd.notna(selected_student_dict['Payment Type']) else payment_type_options[0]
                    payment_type = st.radio(
                        "Payment Type",
                        payment_type_options,
                        index=payment_type_options.index(current_payment_type) if current_payment_type in payment_type_options else 0,
                        key="payment_type",
                        on_change=update_student_data,
                        horizontal=True
                    )
    
                    # Handling Compte Radio
                    st.write("Compte")
                    current_compte = selected_student_dict['Compte'] if pd.notna(selected_student_dict['Compte']) else compte_options[0]
                    compte = st.radio(
                        "Compte",
                        compte_options,
                        index=compte_options.index(current_compte) if current_compte in compte_options else 0,
                        key="compte",
                        on_change=update_student_data,
                        horizontal=True
                    )
    
                    # Handling Sevis Payment Radio
                    st.write("Sevis Payment")
                    current_sevis_payment = selected_student_dict['Sevis payment ?'] if pd.notna(selected_student_dict['Sevis payment ?']) else yes_no_options[0]
                    sevis_payment = st.radio(
                        "Sevis Payment",
                        yes_no_options,
                        index=yes_no_options.index(current_sevis_payment) if current_sevis_payment in yes_no_options else 0,
                        key="sevis_payment",
                        on_change=update_student_data,
                        horizontal=True
                    )
    
                    # Handling Application Payment Radio
                    st.write("Application Payment")
                    current_application_payment = selected_student_dict['Application payment ?'] if pd.notna(selected_student_dict['Application payment ?']) else yes_no_options[0]
                    application_payment = st.radio(
                        "Application Payment",
                        yes_no_options,
                        index=yes_no_options.index(current_application_payment) if current_application_payment in yes_no_options else 0,
                        key="application_payment",
                        on_change=update_student_data,
                        horizontal=True
                    )
    
                else:
                    st.write(f"**Payment Date:** {format_date(selected_student_dict['DATE'])}")
                    st.write(f"**Payment Method:** {selected_student_dict['Payment Amount']}")
                    st.write(f"**Payment Type:** {selected_student_dict['Payment Type']}")
                    st.write(f"**Compte:** {selected_student_dict['Compte']}")
                    st.write(f"**Sevis Payment:** {selected_student_dict['Sevis payment ?']}")
                    st.write(f"**Application Payment:** {selected_student_dict['Application payment ?']}")
                st.markdown('</div>', unsafe_allow_html=True)

    
            with tab5:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🚩 Current Stage")

                # Define the stages
                stages = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.',  'CLIENTS']

                if edit_mode:
                    current_stage = st.selectbox(
                        "Current Stage",
                        stages,
                        index=stages.index(selected_student['Stage']) if selected_student['Stage'] in stages else 0,
                        key="current_stage",
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**Current Stage:** {selected_student['Stage']}")

                # Display progress bar
                step_index = stages.index(selected_student['Stage']) if selected_student['Stage'] in stages else 0
                progress = ((step_index + 1) / len(stages)) * 100

                progress_bar = f"""
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress}%;">
                        {int(progress)}%
                    </div>
                </div>
                """
                st.markdown(progress_bar, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            with tab6:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📂 Document Upload and Status")
                document_type = st.selectbox("Select Document Type",
                                             ["Passport", "Bank Statement", "Financial Letter",
                                              "Transcripts", "Diplomas", "English Test", "Payment Receipt",
                                              "SEVIS Receipt", "I20"],
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

            if st.button("Save Changes", key="save_changes_button"):
                try:
                    # Prepare the updated student data
                    updated_student = {
                        'First Name': st.session_state.get('first_name', selected_student['First Name']),
                        'Last Name': st.session_state.get('last_name', selected_student['Last Name']),
                        'Phone N°': st.session_state.get('phone_number', selected_student['Phone N°']),
                        'E-mail': st.session_state.get('email', selected_student['E-mail']),
                        'Emergency contact N°': st.session_state.get('emergency_contact', selected_student['Emergency contact N°']),
                        'Address': st.session_state.get('address', selected_student['Address']),
                        'Attempts': st.session_state.get('attempts', selected_student['Attempts']),
                        'Chosen School': st.session_state.get('chosen_school', selected_student['Chosen School']),
                        'Specialite': st.session_state.get('specialite', selected_student['Specialite']),
                        'Duration': st.session_state.get('duration', selected_student['Duration']),
                        'School Entry Date': st.session_state.get('school_entry_date', selected_student['School Entry Date']),
                        'Entry Date in the US': st.session_state.get('entry_date_in_us', selected_student['Entry Date in the US']),
                        'ADDRESS in the U.S': st.session_state.get('address_us', selected_student['ADDRESS in the U.S']),
                        'E-MAIL RDV': st.session_state.get('email_rdv', selected_student['E-MAIL RDV']),
                        'PASSWORD RDV': st.session_state.get('password_rdv', selected_student['PASSWORD RDV']),
                        'EMBASSY ITW. DATE': st.session_state.get('embassy_itw_date', selected_student['EMBASSY ITW. DATE']),
                        'DS-160 maker': st.session_state.get('ds160_maker', selected_student['DS-160 maker']),
                        'Password DS-160': st.session_state.get('password_ds160', selected_student['Password DS-160']),
                        'Secret Q.': st.session_state.get('secret_q', selected_student['Secret Q.']),
                        'Visa Result': st.session_state.get('visa_status', selected_student['Visa Result']),
                        'Stage': st.session_state.get('current_stage', selected_student['Stage']),
                        'DATE': st.session_state.get('payment_date', selected_student['DATE']),
                        'BANK': st.session_state.get('Bankstatment', selected_student['BANK']),
                        'Gender': st.session_state.get('Gender', selected_student['Gender']),
                        'Payment Amount': st.session_state.get('payment_method', selected_student['Payment Amount']),
                        'Payment Type': st.session_state.get('payment_type', selected_student['Payment Type']),
                        'Compte': st.session_state.get('compte', selected_student['Compte']),
                        'School Paid': st.session_state.get('School_Paid', selected_student['School Paid']),
                        'Prep ITW': st.session_state.get('Prep_ITW', selected_student['Prep ITW']),
                        'Age': st.session_state.get('Age', selected_student['Age']),
                        'Sevis payment ?': st.session_state.get('sevis_payment', selected_student['Sevis payment ?']),
                        'Agent': st.session_state.get('Agent', selected_student['Agent']),
                        'Application payment ?': st.session_state.get('application_payment', selected_student['Application payment ?']),
                    }
            
                    original_data = st.session_state['data']
            
                    # Apply the changes to the original data
                    for key, value in updated_student.items():
                        original_data.loc[original_data['Student Name'] == student_name, key] = value
            
                    # Ensure the "Student Name" column is updated
                    original_data['Student Name'] = original_data['First Name'] + " " + original_data['Last Name']
            
                    # Save the original data back to Google Sheets
                    if save_data(original_data, spreadsheet_id, 'ALL'):
                        st.success("Changes saved successfully!")
                        st.session_state['reload_data'] = True
                        st.cache_data.clear()
                        with st.spinner("Refreshing data..."):
                            time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Failed to save changes. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred while saving: {str(e)}")
                    
    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()
