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
            'DATE','First Name', 'Last Name', 'Phone N°', 'Address', 'E-mail', 
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

# Function to save data to Google Sheets (batch up)
def save_data(df, spreadsheet_id, sheet_name, student_name):
    def replace_invalid_floats(val):
        if isinstance(val, float):
            if pd.isna(val) or np.isinf(val):
                return None
        return val

    # Get the row of the specific student
    student_row = df[df['Student Name'] == student_name].iloc[0]

    # Replace NaN and inf values with None for this student's data
    student_row = student_row.apply(replace_invalid_floats)

    # Replace [pd.NA, pd.NaT, float('inf'), float('-inf')] with None
    student_row = student_row.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], None)

    # Format the date columns to ensure consistency
    date_columns = ['DATE', 'School Entry Date', 'Entry Date in the US', 'EMBASSY ITW. DATE']
    for col in date_columns:
        if col in student_row.index:
            value = student_row[col]
            if pd.notna(value):
                try:
                    formatted_date = pd.to_datetime(value).strftime('%d/%m/%Y %H:%M:%S')
                    student_row[col] = formatted_date
                except:
                    student_row[col] = ""

    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    
    # Find the row of the student in the sheet
    cell = sheet.find(student_name)
    if cell is None:
        logger.error(f"Student {student_name} not found in the sheet.")
        return

    row_number = cell.row

    # Prepare the data for update
    values = [student_row.tolist()]
    
    # Calculate the last column letter
    num_columns = len(student_row)
    if num_columns <= 26:
        last_column = string.ascii_uppercase[num_columns - 1]
    else:
        last_column = string.ascii_uppercase[(num_columns - 1) // 26 - 1] + string.ascii_uppercase[(num_columns - 1) % 26]

    # Update only the specific student's row
    sheet.update(f'A{row_number}:{last_column}{row_number}', values)

    logger.info(f"Updated data for student: {student_name}")

def format_date(date_string):
    if pd.isna(date_string) or date_string == 'NaT':
        return "Not set"
    try:
        # Parse the date string, assuming day first format
        date = pd.to_datetime(date_string, format='%d/%m/%Y %H:%M:%S', dayfirst=True)
        return date.strftime('%d %B %Y')
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
    st.set_page_config(page_title="Student List", layout="wide")

    st.title("Student List")

    # Load data from Google Sheets
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    sheet_name = "ALL"
    df_all = load_data(spreadsheet_id, sheet_name)

    # Define filter options
    columns_to_filter = ["First Name", "Last Name", "Chosen School", "Specialite", "Duration", "Agent", "Stage"]
    filter_options = {col: ["All"] + df_all[col].dropna().unique().tolist() for col in columns_to_filter}

    # Create filter widgets
    filters = {}
    for col, options in filter_options.items():
        filters[col] = st.sidebar.selectbox(f"Filter by {col}", options)

    # Apply filters
    filtered_data = apply_filters(df_all, filters)

    # Display the data in a table
    st.dataframe(filtered_data)

if __name__ == "__main__":
    main()
