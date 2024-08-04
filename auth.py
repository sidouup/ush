import streamlit as st
import time

def check_password():
    """Returns `True` if the user is logged in or successfully logs in."""
    
    # Check if the user is already logged in
    if "logged_in" in st.session_state and st.session_state.logged_in:
        # Check if the session has expired (e.g., after 12 hours)
        if time.time() - st.session_state.login_time < 12 * 3600:
            return True
        else:
            # Session expired, clear the session state
            st.session_state.clear()
    
    # If not logged in, show the login form
    placeholder = st.empty()
    with placeholder.form("login"):
        st.markdown("#### Enter your credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if (username in st.secrets["passwords"] and
                password == st.secrets["passwords"][username]):
            st.session_state.logged_in = True
            st.session_state.login_time = time.time()
            placeholder.empty()
            st.success("Login successful!")
            return True
        else:
            st.error("Invalid username or password")
    
    return False
