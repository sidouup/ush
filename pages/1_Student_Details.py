import streamlit as st
import pandas as pd
def load_data_from_sheets():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    
    service = build("sheets", "v4", credentials=credentials)
    sheet_id = st.secrets["private_gsheets_url"].split("/")[5]
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:ZZ1000").execute()
    data = result.get("values", [])
    
    if not data:
        st.error("No data found in the Google Sheet.")
        return None
    
    # Use the first row as column names and match with actual data length
    columns = data[0][:len(data[1])]
    
    # Create DataFrame with dynamic column names
    df = pd.DataFrame(data[1:], columns=columns)
    
    # Display information about the DataFrame
    st.write(f"Columns in the sheet: {', '.join(columns)}")
    st.write(f"Number of columns: {len(columns)}")
    st.write(f"Number of rows: {len(df)}")
    
    # Check if 'First Name' and 'Last Name' columns exist
    if 'First Name' in df.columns and 'Last Name' in df.columns:
        df['Student Name'] = df['First Name'] + " " + df['Last Name']
    else:
        st.warning("'First Name' or 'Last Name' column not found. 'Student Name' column not created.")
    
    df.dropna(how='all', inplace=True)
    
    return df

try:
    data = load_data_from_sheets()
    if data is not None:
        st.session_state['data'] = data
        st.success("Data loaded successfully from Google Sheets!")
        
        # Display the first few rows of the data
        st.write("First few rows of the data:")
        st.write(data.head())
    else:
        st.error("Failed to load data from Google Sheets.")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    import traceback
    st.error(traceback.format_exc())
    st.stop()

# Utility functions
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

st.set_page_config(page_title="Student Details", layout="wide")

st.title("👤 Student Search and Details")

if 'uploaded_file' not in st.session_state:
    st.error("Please upload an Excel file on the Home page first.")
    st.stop()

data = load_and_combine_data(st.session_state['uploaded_file'])

col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("🔍 Search for a student (First or Last Name)")
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
        format_func=lambda i: f"{filtered_data.iloc[i]['Student Name']} - {filtered_data.iloc[i]['Current Step']}"
    )
    
    selected_student = filtered_data.iloc[selected_index]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.expander("📋 Personal Information", expanded=True):
            st.write(selected_student[['First Name', 'Last Name', 'Phone N°', 'E-mail', 'Emergency contact N°', 'Attempts', 'Address']])
        
        with st.expander("🏫 School Information", expanded=True):
            st.write(selected_student[['Chosen School', 'Duration', 'School Entry Date', 'Entry Date in the US']])
        
        with st.expander("🏛️ Embassy Information", expanded=True):
            st.write(selected_student[['ADDRESS in the U.S', 'E-MAIL RDV', 'PASSWORD RDV', 'EMBASSY ITW. DATE', 'DS-160 maker', 'Password DS-160', 'Secret Q.']])
    
    with col2:
        st.subheader("Application Status")
        
        visa_status = get_visa_status(selected_student['Visa Result'])
        st.metric("Visa Status", visa_status)
        
        current_step = selected_student['Current Step']
        st.metric("Current Step", current_step)
        
        interview_date = selected_student['EMBASSY ITW. DATE']
        days_remaining = calculate_days_until_interview(interview_date)
        if days_remaining is not None:
            st.metric("Days until interview", days_remaining)
        else:
            st.metric("Days until interview", "N/A")
        
        with st.expander("💰 Payment Information", expanded=True):
            st.write(selected_student[['DATE','Payment Method ', 'Sevis payment ? ', 'Application payment ?']])
else:
    st.info("No students found matching the search criteria.")

