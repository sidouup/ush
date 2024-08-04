import streamlit as st
import time

def check_password():
    password = st.text_input("Enter the password:", type="password")
    if password == st.secrets["general"]["password"]:
        return True
    else:
        st.warning("Incorrect password")
        return False
