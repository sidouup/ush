def refresh():
    Server.get_current()._reloader.reload()import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import time
from streamlit.server.server import Server

def refresh():
    Server.get_current()._reloader.reload()
# Set up Google Sheets authentication
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# Function to add a new student to the Google Sheet
def add_student_to_sheet(student_data):
    client = get_google_sheet_client()
    sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
    sheet.append_row(list(student_data.values()))

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

    # Initialize session state for form inputs
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

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
            agent_options = ["Nesrine", "Hamza", "Djazila"]
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
                "Gender": gender,
                "Phone N°": phone,
                "Address": address,
                "E-mail": email,
                "Emergency contact N°": emergency_contact,
                "Chosen School": chosen_school,
                "Specialite": specialite,
                "Duration": duration,
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
                "Note": "",
                "Stage": "PAYMENT & MAIL",
                "BANK": "",
                "Student Name": f"{first_name} {last_name}"
            }

            # Add student to sheet
            add_student_to_sheet(student_data)
            time.sleep(1)  # Simulate processing time

        # Show success message
        st.markdown(f'<p class="success-message">✅ Student {first_name} {last_name} added successfully!</p>', unsafe_allow_html=True)

        # Set form_submitted to True to trigger a rerun
        st.session_state.form_submitted = True

    # Check if form was just submitted and rerun if so
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
        st.rerun()
        refresh()

if __name__ == "__main__":
    main()
