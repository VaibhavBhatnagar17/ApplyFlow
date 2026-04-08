import streamlit as st

st.set_page_config(
    page_title="ApplyFlow",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from engine.auth import login, register
from engine.guard import get_username, sidebar_user_info
from engine.state import load_profile, load_applications, load_user_saved_jobs

sidebar_user_info()
username = get_username()

if username:
    profile, _ = load_profile(username)

    st.markdown("""
# Welcome to ApplyFlow

**From resume to offer, in one smooth flow.**

Your onboarding profile drives job discovery, ranking, and application tracking.

### Quick Links

1. **Onboarding** — Add deep profile details + resume preview
2. **Dashboard** — Personalized insights from your onboarding data
3. **Saved & Applied** — Unified pipeline of saved jobs and applied jobs
4. **Job Search** — Real-time search across platforms with advanced filters
5. **Cover Letters** — Tailored drafts based on your profile and target role
""")

    saved_jobs = load_user_saved_jobs(username)
    apps = load_applications(username)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Saved Jobs", len(saved_jobs))
    with c2:
        st.metric("Applications", len(apps))
    with c3:
        pct = int((len(apps) / len(saved_jobs)) * 100) if saved_jobs else 0
        st.metric("Apply Rate", f"{pct}%")

    if not profile or not profile.is_complete():
        st.info("Complete onboarding to unlock personalized matching and insights.")
        st.page_link("pages/1_Onboarding.py", label="Start Onboarding", icon="📝")

else:
    st.markdown("""
# Welcome to ApplyFlow

**From resume to offer, in one smooth flow.**

Create an account, complete onboarding, and get a personalized real-time job search workflow.
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
