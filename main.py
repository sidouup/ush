import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build

def adjust_data_to_headers(headers, data):
    """Adjust the data to match the number of headers."""
    if len(headers) > len(data[0]):
        # Add empty values to data rows
        return [row + [''] * (len(headers) - len(row)) for row in data]
    elif len(headers) < len(data[0]):
        # Truncate data rows
        return [row[:len(headers)] for row in data]
    return data

def load_data_from_sheets():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials)
    sheet_id = st.secrets["private_gsheets_url"].split("/")[5]
    
    sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    
    all_data = []
    
    for sheet in sheets:
        sheet_name = sheet['properties']['title']
        range_name = f"{sheet_name}!A1:ZZ"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            continue
        
        headers = values[0]
        data = values[1:]
        
        # Adjust data to match headers
        adjusted_data = adjust_data_to_headers(headers, data)
        
        df = pd.DataFrame(adjusted_data, columns=headers)
        df['Current Step'] = sheet_name
        all_data.append(df)
    
    if not all_data:
        return None
    
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Create 'Student Name' column if possible
    if 'First Name' in combined_data.columns and 'Last Name' in combined_data.columns:
        combined_data['Student Name'] = combined_data['First Name'].astype(str) + " " + combined_data['Last Name'].astype(str)
    
    combined_data.dropna(subset=['Student Name'], inplace=True, errors='ignore')
    combined_data.dropna(how='all', inplace=True)
    combined_data.drop_duplicates(subset='Student Name', keep='last', inplace=True)
    combined_data.reset_index(drop=True, inplace=True)
    
    return combined_data

# Utility functions (unchanged)
def get_visa_status(result):
    result_mapping = {
        'Denied': 'Denied',
        'Approved': 'Approved',
        'Not our school partner': 'Not our school partner',
    }
    return result_mapping.get(result, 'Unknown')

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

# Set page config
st.set_page_config(page_title="Student Application Tracker", layout="wide")

# Custom CSS (unchanged)
st.markdown("""
    <div style="display: flex; align-items: center;">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
        <h1 style="color: #1E3A8A;">Student Application Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

# Load data from Google Sheets
try:
    data = load_data_from_sheets()
    if data is not None and not data.empty:
        st.success("Data loaded successfully from Google Sheets!")

        # Combined search and selection functionality
        st.header("👤 Student Search and Details")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search for a student (First or Last Name)")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some vertical space
            search_button = st.button("Search", key="search_button", help="Click to search")
        
        # Filter data based on search query
        if search_query and search_button:
            filtered_data = data[data['Student Name'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_data = data

        # Display filtered data with selection capability
        if not filtered_data.empty:
            selected_index = st.selectbox(
                "Select a student to view details",
                range(len(filtered_data)),
                format_func=lambda i: f"{filtered_data.iloc[i]['Student Name']} - {filtered_data.iloc[i]['Current Step']}"
            )
            
            selected_student = filtered_data.iloc[selected_index]
            
            # Display student details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                with st.expander("📋 Personal Information", expanded=True):
                    personal_info = ['First Name', 'Last Name', 'Phone N°', 'E-mail', 'Emergency contact N°', 'Attempts', 'Address']
                    st.write(selected_student[personal_info].dropna())
                
                with st.expander("🏫 School Information", expanded=True):
                    school_info = ['Chosen School', 'Duration', 'School Entry Date', 'Entry Date in the US']
                    st.write(selected_student[school_info].dropna())
                
                with st.expander("🏛️ Embassy Information", expanded=True):
                    embassy_info = ['ADDRESS in the U.S', ' E-MAIL RDV', 'PASSWORD RDV', 'EMBASSY ITW. DATE', 'DS-160 maker', 'Password DS-160', 'Secret Q.']
                    st.write(selected_student[embassy_info].dropna())
            
            with col2:
                st.subheader("Application Status")
                
                # Visa Status
                visa_status = get_visa_status(selected_student.get('Visa Result', 'Unknown'))
                st.metric("Visa Status", visa_status)
                
                # Current Step
                current_step = selected_student['Current Step']
                st.metric("Current Step", current_step)
                
                # Days until interview
                interview_date = selected_student.get('EMBASSY ITW. DATE')
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("Days until interview", days_remaining)
                else:
                    st.metric("Days until interview", "N/A")
                
                # Payment Information
                with st.expander("💰 Payment Information", expanded=True):
                    payment_info = ['DATE', 'Payment Method ', 'Sevis payment ? ', 'Application payment ?']
                    st.write(selected_student[payment_info].dropna())
        else:
            st.info("No students found matching the search criteria.")

        # Dashboard with all clients
        st.header("📊 Dashboard - All Clients")
        
        # Create a bar chart of students per step
        step_counts = data['Current Step'].value_counts()
        fig = px.bar(step_counts, x=step_counts.index, y=step_counts.values, 
                     labels={'x': 'Application Step', 'y': 'Number of Students'},
                     title='Students per Application Step')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0.05)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Failed to load data from Google Sheets or the sheet is empty.")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    st.stop()

# Footer
st.markdown("---")
st.markdown("© 2024 The Us House. All rights reserved.")

