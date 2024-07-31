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
            return file_id
    else:
        st.warning(f"{file_name} already exists for this student.")
    
    return None
def check_document_status(student_name):
    parent_folder_id = '1It91HqQDsYeSo1MuYgACtmkmcO82vzXp'
    student_folder_id = check_folder_exists(student_name, parent_folder_id)
    
    document_types = ["Passport", "Bank Statement", "Financial Letter", "Transcripts", "Diplomas", "English Test", "Payment Receipts"]
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
def list_files_in_folder(folder_id):
    service = get_google_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, webViewLink)').execute()
    return results.get('files', [])
    
def delete_file_from_drive(file_id):
    service = get_google_drive_service()
    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        st.error(f"An error occurred while deleting the file: {str(e)}")
        return False
def check_file_exists_in_folder(folder_id):
    service = get_google_drive_service()
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    return bool(results.get('files', []))

# Main function
def main():
    st.set_page_config(page_title="Student Application Tracker", layout="wide")

    # Custom CSS (keep your existing styles and add styles for the 3D progress bar)
    st.markdown("""
    <style>
        /* Your existing CSS styles */
        .progress-container {
          width: 100%;
          background-color: #f3f3f3;
          border-radius: 25px;
          overflow: hidden;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .progress-bar {
          height: 30px;
          background: linear-gradient(90deg, #4CAF50, #45a049);
          text-align: center;
          line-height: 30px;
          color: white;
          border-radius: 25px;
          transition: width 0.5s ease-in-out;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1) inset;
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
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            search_query = st.text_input("🔍 Search for a student (First or Last Name)", key="search_query")
        with col2:
            status_filter = st.selectbox("Filter by status", ["All"] + list(data['Current Step'].unique()), key="status_filter")
        with col3:
            search_button = st.button("Search", key="search_button", help="Click to search")
        
        filtered_data = data
        if search_query and search_button:
            filtered_data = filtered_data[filtered_data['Student Name'].str.contains(search_query, case=False, na=False)]
        if status_filter != "All":
            filtered_data = filtered_data[filtered_data['Current Step'] == status_filter]

        if not filtered_data.empty:
            selected_index = st.selectbox(
                "Select a student to view details",
                range(len(filtered_data)),
                format_func=lambda i: f"{filtered_data.iloc[i]['Student Name']} - {filtered_data.iloc[i]['Current Step']}",
                key="selected_index"
            )
        
            selected_student = filtered_data.iloc[selected_index]
            student_name = selected_student['Student Name']

            edit_mode = st.toggle("Edit Mode", value=False)
        
            # Application Status (with 3D progress bar)
            st.subheader("Application Status")
            steps = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.', 'SEVIS', 'CLIENTS ']
            current_step = selected_student['Current Step']
            step_index = steps.index(current_step) if current_step in steps else 0
            progress = ((step_index + 1) / len(steps)) * 100
            
            progress_html = f"""
            <div class="progress-container">
              <div class="progress-bar" style="width: {progress}%;">{int(progress)}%</div>
            </div>
            """
            st.components.v1.html(progress_html, height=50)
            st.write(f"Current Step: {current_step}")

            if edit_mode:
                visa_status = st.selectbox(
                    "Visa Status",
                    ['Denied', 'Approved', 'Not our school partner', 'Unknown'],
                    index=['Denied', 'Approved', 'Not our school partner', 'Unknown'].index(get_visa_status(selected_student.get('Visa Result', 'Unknown'))),
                    key="visa_status"
                )
                current_step = st.selectbox("Current Step", steps, index=step_index, key="current_step")
            else:
                st.write(f"**Visa Status:** {get_visa_status(selected_student.get('Visa Result', 'Unknown'))}")

            interview_date = selected_student['EMBASSY ITW. DATE']
            days_remaining = calculate_days_until_interview(interview_date)
            if days_remaining is not None:
                st.metric("Days until interview", days_remaining)
            else:
                st.metric("Days until interview", "N/A")

            # Create tabs for different information categories
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Personal", "School", "Embassy", "Payment", "Documents"])
            
            with tab1:
                st.subheader("📋 Personal Information")
                if edit_mode:
                    first_name = st.text_input("First Name", selected_student['First Name'], key="first_name")
                    last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name")
                    phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number")
                    email = st.text_input("Email", selected_student['E-mail'], key="email")
                    emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact")
                    address = st.text_input("Address", selected_student['Address'], key="address")
                    attempts = st.text_input("Attempts", selected_student['Attempts'], key="attempts")
                else:
                    st.write(f"**First Name:** {selected_student['First Name']}")
                    st.write(f"**Last Name:** {selected_student['Last Name']}")
                    st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                    st.write(f"**Email:** {selected_student['E-mail']}")
                    st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                    st.write(f"**Address:** {selected_student['Address']}")
                    st.write(f"**Attempts:** {selected_student['Attempts']}")
            
            # ... [Keep the content for tab2, tab3, and tab4 as in the previous version] ...

            with tab5:
                st.subheader("📂 Document Upload and Status")
                col1, col2 = st.columns(2)
                with col1:
                    document_type = st.selectbox("Select Document Type", 
                                                 ["Passport", "Bank Statement", "Financial Letter", 
                                                  "Transcripts", "Diplomas", "English Test", "Payment Receipt"], 
                                                 key="document_type")
                    uploaded_file = st.file_uploader("Upload Document", type=["jpg", "jpeg", "png", "pdf"], key="uploaded_file")
                    
                    if uploaded_file and st.button("Upload Document"):
                        file_id = handle_file_upload(student_name, document_type, uploaded_file)
                        if file_id:
                            st.success(f"{document_type} uploaded successfully!")
                        else:
                            st.error("An error occurred while uploading the document.")

                with col2:
                    document_status = check_document_status(student_name)
                    st.subheader("Document Status")
                    for doc_type, status_info in document_status.items():
                        icon = "✅" if status_info['status'] else "❌"
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <span style="font-size: 20px; margin-right: 10px;">{icon}</span>
                            <span style="flex-grow: 1;">{doc_type}</span>
                            {"".join([f'<a href="{file["webViewLink"]}" target="_blank" style="margin-left: 10px;">View</a><button onclick="deleteFile(\'{file["id"]}\')">🗑️</button>' for file in status_info['files']])}
                        </div>
                        """, unsafe_allow_html=True)

                # Add JavaScript for file deletion
                st.markdown("""
                <script>
                function deleteFile(fileId) {
                    if (confirm('Are you sure you want to delete this file?')) {
                        fetch('/delete_file', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({file_id: fileId}),
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('File deleted successfully');
                                location.reload();
                            } else {
                                alert('Failed to delete file: ' + data.error);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('An error occurred while deleting the file');
                        });
                    }
                }
                </script>
                """, unsafe_allow_html=True)

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

    else:
        st.error("No data available. Please check your Google Sheets connection and data.")

    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()





