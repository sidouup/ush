import streamlit as st
import pandas as pd
import plotly.express as px
from main import load_and_combine_data

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("📊 Dashboard - All Clients")

if 'uploaded_file' not in st.session_state:
    st.error("Please upload an Excel file on the Home page first.")
    st.stop()

data = load_and_combine_data(st.session_state['uploaded_file'])

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

# Summary Statistics
st.subheader("Summary Statistics")
total_students = len(data)
unique_schools = data['Chosen School'].nunique()

# Handle potential errors in Duration calculation
try:
    # Try to convert Duration to numeric, coercing errors to NaN
    data['Duration'] = pd.to_numeric(data['Duration'], errors='coerce')
    average_duration = data['Duration'].mean()
    average_duration_str = f"{average_duration:.2f}" if pd.notnull(average_duration) else "N/A"
except Exception as e:
    st.warning(f"Error calculating average duration: {str(e)}")
    average_duration_str = "Error"

col1, col2, col3 = st.columns(3)
col1.metric("Total Students", total_students)
col2.metric("Unique Schools", unique_schools)
col3.metric("Average Duration (days)", average_duration_str)

# Recent Applications
st.subheader("Recent Applications")
st.dataframe(data[['Student Name', 'Chosen School', 'Current Step']].head(10))

# Visa Status Distribution
st.subheader("Visa Status Distribution")
visa_status_counts = data['Visa Result'].value_counts()
fig_visa = px.pie(values=visa_status_counts.values, names=visa_status_counts.index, title='Visa Status Distribution')
st.plotly_chart(fig_visa, use_container_width=True)

# School Distribution
st.subheader("Top Schools")
school_counts = data['Chosen School'].value_counts().head(10)
fig_schools = px.bar(x=school_counts.index, y=school_counts.values, labels={'x': 'School', 'y': 'Number of Students'}, title='Top 10 Schools')
st.plotly_chart(fig_schools, use_container_width=True)

# Data Quality Check
st.subheader("Data Quality Check")
missing_data = data.isnull().sum()
st.write("Number of missing values in each column:")
st.write(missing_data[missing_data > 0])

# Display a sample of the data
st.subheader("Sample Data")
st.write(data.head())

# Footer
st.markdown("---")
st.markdown("© 2024 The Us House. All rights reserved.")

