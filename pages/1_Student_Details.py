import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# The ID of your spreadsheet
SPREADSHEET_ID = "1NPc-dQ7uts1c1JjNoABBou-uq2ixzUTiSBTB8qlTuOQ"

@st.cache_resource
def get_google_sheet_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scope)
    return gspread.authorize(creds)

def add_student_to_sheet(student_data):
    client = get_google_sheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet("PAYMENT & MAIL")
    worksheet.append_row(student_data)

def main():
    # Set page config
    st.set_page_config(page_title="Add New Student", layout="wide")

    # Custom CSS
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
    </style>
    """, unsafe_allow_html=True)

    # Main title with logo
    st.markdown("""
        <div style="display: flex; align-items: center;">
            <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" style="margin-right: 10px; width: 50px; height: auto;">
            <h1 style="color: #1E3A8A;">Add New Student</h1>
        </div>
        """, unsafe_allow_html=True)

    st.header("📝 Enter Student Information")

    # Personal Information
    with st.expander("📋 Personal Information", expanded=True):
        first_name = st.text_input("First Name ✏️")
        last_name = st.text_input("Last Name ✏️")
        phone_number = st.text_input("Phone Number 📞")
        email = st.text_input("Email 📧")
        emergency_contact = st.text_input("Emergency Contact Number 🚨")
        address = st.text_input("Address 🏠")
    
    # School Information
    with st.expander("🏫 School Information", expanded=True):
        chosen_school = st.text_input("Chosen School 🎓")
        duration = st.text_input("Duration ⏳")
        school_entry_date = st.text_input("School Entry Date 📅")
        entry_date_in_us = st.text_input("Entry Date in the US ✈️")

    # Embassy Information
    with st.expander("🏛️ Embassy Information", expanded=True):
        address_us = st.text_input("Address in the U.S 📍")
        email_rdv = st.text_input("E-mail RDV 📧")
        password_rdv = st.text_input("Password RDV 🔒")
        embassy_itw_date = st.text_input("Embassy Interview Date 📅")
        ds160_maker = st.text_input("DS-160 Maker 📝")
        password_ds160 = st.text_input("Password DS-160 🔒")
        secret_q = st.text_input("Secret Question ❓")
    
    # Payment Information
    with st.expander("💰 Payment Information", expanded=True):
        payment_method = st.text_input("Payment Method 💳")
        sevis_payment = st.text_input("Sevis Payment 💵")
        application_payment = st.text_input("Application Payment 💵")

    # Additional Information
    attempts = st.text_input("Attempts 🔄")
    visa_result = st.text_input("Visa Result 🛂")
    agent = st.text_input("Agent 🧑‍💼")
    note = st.text_input("Note 📝")

    if st.button("Add Student", key="add_student_button"):
        student_data = [
            first_name, last_name, phone_number, address, email, emergency_contact, chosen_school,
            duration, payment_method, sevis_payment, application_payment, ds160_maker, password_ds160,
            secret_q, school_entry_date, entry_date_in_us, address_us, email_rdv, password_rdv, embassy_itw_date,
            attempts, visa_result, agent, note
        ]
        add_student_to_sheet(student_data)
        st.success("Student added successfully! 🎉")

    # Footer
    st.markdown("---")
    st.markdown("© 2024 The Us House. All rights reserved.")

if __name__ == "__main__":
    main()
