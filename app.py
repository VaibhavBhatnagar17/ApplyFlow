import streamlit as st

st.set_page_config(
    page_title="ApplyFlow",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from engine.auth import login, register
from engine.guard import get_username, sidebar_user_info
from engine.state import load_profile, load_active_jobs, load_applications
from engine.company_db import load_companies

sidebar_user_info()

username = get_username()

if username:
    profile, prefs = load_profile(username)

    st.markdown("""
# Welcome to ApplyFlow

**From resume to offer, in one smooth flow.**

Your personalized dashboard scores every opening against your profile, writes tailored cover letters, and tracks applications from "applied" to "offer."

### Quick Links

1. **Onboarding** — Upload resume & set preferences
2. **Dashboard** — View matched jobs with scores
3. **Companies** — Browse 250+ company database
4. **Job Search** — Live search across platforms
5. **Cover Letters** — Generate tailored letters
6. **Tracker** — Track your applications
""")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Jobs in Database", len(load_active_jobs()))
    with col2:
        st.metric("Companies Tracked", len(load_companies()))
    with col3:
        st.metric("Applications Sent", len(load_applications(username)))

    if not profile or not profile.is_complete():
        st.info("Complete onboarding to unlock personalized job matching.")
        st.page_link("pages/1_Onboarding.py", label="Start Onboarding", icon="📝")

else:
    st.markdown("""
# Welcome to ApplyFlow

**From resume to offer, in one smooth flow.**

Upload your resume, set your preferences, and get a personalized dashboard that scores every opening against your profile, writes tailored cover letters, and tracks applications from "applied" to "offer."
""")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            login_btn = st.form_submit_button("Login", type="primary", use_container_width=True)

            if login_btn:
                if not login_user or not login_pass:
                    st.error("Please enter both username and password.")
                else:
                    ok, msg = login(login_user, login_pass)
                    if ok:
                        st.session_state["username"] = login_user.strip().lower()
                        st.session_state["display_name"] = msg
                        st.rerun()
                    else:
                        st.error(msg)

    with tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            reg_name = st.text_input("Display Name", key="reg_name")
            reg_user = st.text_input("Username", key="reg_user")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            reg_pass2 = st.text_input("Confirm Password", type="password", key="reg_pass2")
            reg_btn = st.form_submit_button("Register", type="primary", use_container_width=True)

            if reg_btn:
                if reg_pass != reg_pass2:
                    st.error("Passwords don't match.")
                elif not reg_user or not reg_pass:
                    st.error("Please fill in all fields.")
                else:
                    ok, msg = register(reg_user, reg_pass, reg_name)
                    if ok:
                        st.session_state["username"] = reg_user.strip().lower()
                        st.session_state["display_name"] = reg_name or reg_user
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
