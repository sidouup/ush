import streamlit as st
import pandas as pd
from main import load_and_combine_data, get_visa_status, calculate_days_until_interview

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

