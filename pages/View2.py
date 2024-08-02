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
def save_data(df, spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = df.where(pd.notnull(df), None)  # Replace NaNs with None for gspread
    rows = df.values.tolist()
    headers = df.columns.tolist()
    sheet.clear()
    sheet.update([headers] + rows)

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

    # Filter buttons for stages
    st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
    stage_filter = st.selectbox("Filter by Stage", current_steps, key="stage_filter")

    # Filter widgets
    col1, col2, col3 = st.columns(3)
    with col1:
        agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
    with col2:
        school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
    with col3:
        attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")

    # Apply filters
    filtered_data = df_all
    if stage_filter != "All":
        filtered_data = filtered_data[filtered_data['Stage'] == stage_filter]
    if agent_filter != "All":
        filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
    if school_filter != "All":
        filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
    if attempts_filter != "All":
        filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]

    student_names = filtered_data['Student Name'].tolist()

    # Editable table
    edit_mode = st.checkbox("Edit Mode")
    if edit_mode:
        # Convert empty strings to None to allow editing
        filtered_data = filtered_data.replace('', None)
        edited_data = st.data_editor(
            filtered_data,
            num_rows="dynamic",
            key="data_editor",
            use_container_width=True,
            column_config={
                col: st.column_config.TextColumn(col, required=False)
                for col in filtered_data.columns
            }
        )
        if st.button("Save Changes"):
            save_data(edited_data, spreadsheet_id, sheet_name)
            st.success("Changes saved successfully!")
    else:
        st.dataframe(filtered_data)

if __name__ == "__main__":
    main()
