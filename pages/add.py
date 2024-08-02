import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread

# Set up Google Sheets authentication
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

# Function to add a new student to the Google Sheet
def add_student_to_sheet(student_data):
    client = get_google_sheet_client()
    sheet = client.open_by_key("1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI").worksheet('ALL')
    sheet.append_row(list(student_data.values()))

# Streamlit app
def main():
    st.set_page_config(page_title="Add New Student", layout="wide")
    st.title("Add New Student")

    # Create form
    with st.form("student_form"):
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("Date", datetime.now())
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            gender = st.selectbox("Gender", ["Male", "Female"])
            phone = st.text_input("Phone Number")
            address = st.text_area("Address")
            email = st.text_input("Email")
            emergency_contact = st.text_input("Emergency Contact Number")

        with col2:
            school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                              "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                              "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
            chosen_school = st.selectbox("Chosen School", school_options)
            specialite = st.text_input("Specialite")
            duration = st.text_input("Duration")
            payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
            payment_amount = st.selectbox("Payment Amount", payment_amount_options)
            payment_type = st.selectbox("Payment Type", ["Cash", "CCP", "Baridimob", "Bank"])
            compte = st.selectbox("Compte", ["Mohamed", "Sid Ali"])
            sevis_payment = st.selectbox("Sevis Payment", ["YES", "NO"])
            application_payment = st.selectbox("Application Payment", ["YES", "NO"])

        submit_button = st.form_submit_button("Add Student")

    if submit_button:
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
            "Sevis payment ?": sevis_payment,
            "Application payment ?": application_payment,
            # Add default values for other fields
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
            "Agent": "",
            "Note": "",
            "Stage": "PAYMENT & MAIL",
            "BANK": "",
            "Student Name": f"{first_name} {last_name}"
        }

        # Add student to sheet
        add_student_to_sheet(student_data)
        st.success("Student added successfully!")

if __name__ == "__main__":
    main()
