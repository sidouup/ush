import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load data from Google Sheets
def load_data(spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# Function to apply filters
def apply_filters(df, filters):
    for column, value in filters.items():
        if value != "All":
            df = df[df[column] == value]
    return df

# Function to save data to Google Sheets
def save_data(df, spreadsheet_id, sheet_name, student_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = df.where(pd.notnull(df), None)  # Replace NaNs with None for gspread
    rows = df.values.tolist()
    headers = df.columns.tolist()
    sheet.clear()
    sheet.update([headers] + rows)

# Function to handle student selection
def on_student_select():
    st.session_state.student_changed = True

# Main function for the new page
def main():
    st.set_page_config(page_title="Student List", layout="wide")

    st.title("Student List")

    # Load data from Google Sheets
    spreadsheet_id = "1os1G3ri4xMmJdQSNsVSNx6VJttyM8JsPNbmH0DCFUiI"
    sheet_name = "ALL"
    df_all = load_data(spreadsheet_id, sheet_name)

    # Define filter options
    current_steps = ["All"] + list(df_all['Stage'].unique())
    agents = ["All", "Nesrine", "Hamza", "Djazila"]
    school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                      "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                      "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
    attempts_options = ["All", "1st Try", "2nd Try", "3rd Try"]

    st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox("Filter by Stage", current_steps, key="status_filter")
    with col2:
        agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
    with col3:
        school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
    with col4:
        attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")

    # Apply filters
    filtered_data = df_all
    if status_filter != "All":
        filtered_data = filtered_data[filtered_data['Stage'] == status_filter]
    if agent_filter != "All":
        filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
    if school_filter != "All":
        filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
    if attempts_filter != "All":
        filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]

    student_names = filtered_data['Student Name'].tolist()

    if not filtered_data.empty:
        st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
        col2, col1, col3 = st.columns([3, 2, 3])

        with col2:
            search_query = st.selectbox(
                "🔍 Search for a student (First or Last Name)",
                options=student_names,
                key="search_query",
                index=student_names.index(st.session_state.selected_student) if st.session_state.selected_student in student_names else 0,
                on_change=on_student_select
            )
            # After the selectbox:
            if st.session_state.student_changed or st.session_state.selected_student != search_query:
                st.session_state.selected_student = search_query
                st.session_state.student_changed = False
                st.rerun()

            st.subheader("📝 Student Notes")

            # Get the current note for the selected student
            selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
            current_note = selected_student['Note'] if 'Note' in selected_student else ""

            # Create a text area for note input
            new_note = st.text_area("Enter/Edit Note:", value=current_note, height=150, key="note_input")

            # Save button for the note
            if st.button("Save Note"):
                # Update the note in the DataFrame
                filtered_data.loc[filtered_data['Student Name'] == search_query, 'Note'] = new_note

                # Save the updated data back to Google Sheets
                save_data(df_all, spreadsheet_id, sheet_name, search_query)

                st.success("Note saved successfully!")

                # Set a flag to reload data on next run
                st.session_state['reload_data'] = True

                # Rerun the app to show updated data
                st.rerun()

        # Display the data in a table
        st.dataframe(filtered_data)

if __name__ == "__main__":
    main()
