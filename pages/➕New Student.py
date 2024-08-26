import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
import time

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to add a new student to the Google Sheet
def add_student_to_sheet(student_data):
    client = get_google_sheet_client()
    sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
    sheet.append_row(list(student_data.values()))

    # Add the month in '%B %Y' format to the 'Months' column
    date_str = student_data['DATE']
    date_obj = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    month_year = date_obj.strftime("%B %Y")

    # Check if the 'Months' column exists and append the new month-year
    months_col_index = sheet.row_values(1).index('Months') + 1
    existing_months = sheet.col_values(months_col_index)
    
    if month_year not in existing_months:
        sheet.update_cell(len(existing_months) + 1, months_col_index, month_year)

# Function to load data from Google Sheets
@st.cache_data(ttl=5)
def load_data():
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
        expected_headers = ["DATE", "First Name", "Last Name", "Age", "Gender", "Phone N°", "Address", "E-mail", 
                            "Emergency contact N°", "Chosen School", "Specialite", "Duration", "Payment Amount", 
                            "Payment Type", "Compte", "Sevis payment ?", "Application payment ?", "DS-160 maker", 
                            "Password DS-160", "Secret Q.", "School Entry Date", "Entry Date in the US", 
                            "ADDRESS in the U.S", "E-MAIL RDV", "PASSWORD RDV", "EMBASSY ITW. DATE", "Attempts", 
                            "Visa Result", "Agent", "Note", "Stage", "BANK", "Student Name"]
        data = sheet.get_all_records(expected_headers=expected_headers)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}")
        raise e

# Custom CSS to make the app beautiful and modern
def load_css():
    st.markdown("""
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stTextInput, .stSelectbox, .stDateInput, .stTextArea {
        background-color: white;
        color: #2c3e50;
        border-radius: 5px;
        padding: 10px;
        border: 1px solid #bdc3c7;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
    .success-message {
        background-color: #2ecc71;
        color: white;
        padding: 10px;
        border-radius: 5px;
        animation: fadeIn 0.5s;
    }
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    </style>
    """, unsafe_allow_html=True)

# Streamlit app
def main():
    st.set_page_config(page_title="Add New Student", layout="wide")
    load_css()

    st.title("🎓 Add New Student")
    st.markdown("Fill in the form below to add a new student to the database.")

    # Initialize session state
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

    # Create form
    with st.form("student_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("📅 Date", datetime.now())
            first_name = st.text_input("👤 First Name")
            last_name = st.text_input("👤 Last Name")
            gender = st.selectbox("⚧ Gender", ["Male", "Female"])
            phone = st.text_input("📞 Phone Number")
            address = st.text_input("🏠 Address")
            email = st.text_input("📧 Email")
            emergency_contact = st.text_input("🆘 Emergency Contact Number")

        with col2:
            age = st.text_input("👤 Age")
            school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                              "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                              "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
            chosen_school = st.selectbox("🏫 Chosen School", school_options)
            specialite = st.text_input("📚 Specialite")
            duration = st.text_input("⏳ Duration")
            payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
            payment_amount = st.selectbox("💰 Payment Amount", payment_amount_options)
            payment_type = st.selectbox("💳 Payment Type", ["Cash", "CCP", "Baridimob", "Bank"])
            compte = st.selectbox("🏦 Compte", ["Mohamed", "Sid Ali"])
            agent_options = ["Nesrine", "Hamza", "Djazila","Nada"]
            agent = st.selectbox("👨‍💼 Agent", agent_options)

        submit_button = st.form_submit_button("Add Student")

    if submit_button:
        # Show a spinner while processing
        with st.spinner('Adding student to database...'):
            # Prepare student data
            student_data = {
                "DATE": date.strftime("%d/%m/%Y %H:%M:%S"),
                "First Name": first_name,
                "Last Name": last_name,
                "Age": age,
                "Gender": gender,
                "Phone N°": phone,
                "Address": address,
                "E-mail": email,
                "Emergency contact N°": emergency_contact,
                "Chosen School": chosen_school,
                "Specialite": specialite,
                "Duration": duration,
                "BANK": "",
                "Payment Amount": payment_amount,
                "Payment Type": payment_type,
                "Compte": compte,
                "Sevis payment ?": "NO",
                "Application payment ?": "NO",
                "DS-160 maker": "",
                "Password DS-160": "",
                "Secret Q.": "",
                "School Entry Date": "",
                "Entry Date in the US": "",
                "ADDRESS in the U.S": "",
                "E-MAIL RDV": "",
                "PASSWORD RDV": "",
                "EMBASSY ITW. DATE": "",
                "Attempts": "1st Try",
                "Visa Result": "",
                "Agent": agent,
                "Prep ITW": "NO",
                "School Paid": "NO",
                "Visa Result": "",
                "Note": "",
                "Stage": "PAYMENT & MAIL",
                "BANK": "",
                "Student Name": f"{first_name} {last_name}"
            }

            # Add student to sheet
            add_student_to_sheet(student_data)
            time.sleep(1)  # Simulate processing time

        # Set success message
        st.session_state.success_message = f"✅ Student {first_name} {last_name} added successfully!"
        st.session_state.form_submitted = True

        # Clear the form by resetting the session state
        for key in st.session_state.keys():
            if key not in ['form_submitted', 'success_message']:
                del st.session_state[key]

        # Rerun the app to show the success message and clear the form
        st.rerun()

    # Display success message if it exists
    if st.session_state.success_message:
        st.markdown(f'<p class="success-message">{st.session_state.success_message}</p>', unsafe_allow_html=True)
        st.session_state.success_message = None  # Clear the message after displaying

    # Display the latest data
    st.subheader("Latest Students")
    data = load_data()
    st.dataframe(data.tail(5))  # Show the last 5 entries

if __name__ == "__main__":
    main()
