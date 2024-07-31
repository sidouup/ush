import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread

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
    st.title("Add New Student")

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email")
    emergency_contact = st.text_input("Emergency Contact Number")
    address = st.text_input("Address")
    chosen_school = st.text_input("Chosen School")
    duration = st.text_input("Duration")
    payment_method = st.text_input("Payment Method")
    sevis_payment = st.text_input("Sevis Payment")
    application_payment = st.text_input("Application Payment")
    ds160_maker = st.text_input("DS-160 Maker")
    password_ds160 = st.text_input("Password DS-160")
    secret_q = st.text_input("Secret Question")
    school_entry_date = st.text_input("School Entry Date")
    entry_date_in_us = st.text_input("Entry Date in the US")
    address_us = st.text_input("Address in the U.S")
    email_rdv = st.text_input("E-mail RDV")
    password_rdv = st.text_input("Password RDV")
    embassy_itw_date = st.text_input("Embassy Interview Date")
    attempts = st.text_input("Attempts")
    visa_result = st.text_input("Visa Result")
    agent = st.text_input("Agent")
    note = st.text_input("Note")

    if st.button("Add Student"):
        student_data = [
            first_name, last_name, phone_number, address, email, emergency_contact, chosen_school,
            duration, payment_method, sevis_payment, application_payment, ds160_maker, password_ds160,
            secret_q, school_entry_date, entry_date_in_us, address_us, email_rdv, password_rdv, embassy_itw_date,
            attempts, visa_result, agent, note
        ]
        add_student_to_sheet(student_data)
        st.success("Student added successfully!")

if __name__ == "__main__":
    main()
