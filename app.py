import streamlit as st

st.set_page_config(
    page_title="JobPilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

from engine.state import load_profile

profile, prefs = load_profile()

st.sidebar.markdown("## JobPilot")
if profile and profile.is_complete():
    st.sidebar.success(f"Logged in as **{profile.name}**")
    st.sidebar.caption(f"{profile.current_title} | {profile.years_experience}+ yrs")
else:
    st.sidebar.info("Complete onboarding to unlock all features.")

st.markdown("""
# Welcome to JobPilot

Your AI-powered job search companion. Upload your resume, set preferences, and get a personalized dashboard with matched jobs, cover letters, and application tracking.

### Get Started

1. **Onboarding** — Upload resume & set preferences
2. **Dashboard** — View matched jobs with scores
3. **Companies** — Browse 250+ company database
4. **Job Search** — Live search across platforms
5. **Cover Letters** — Generate tailored letters
6. **Tracker** — Track your applications

Use the sidebar to navigate between pages.
""")

col1, col2, col3 = st.columns(3)
with col1:
    jobs = len(__import__("engine.state", fromlist=["load_active_jobs"]).load_active_jobs())
    st.metric("Jobs in Database", jobs)
with col2:
    companies = len(__import__("engine.company_db", fromlist=["load_companies"]).load_companies())
    st.metric("Companies Tracked", companies)
with col3:
    apps = len(__import__("engine.state", fromlist=["load_applications"]).load_applications())
    st.metric("Applications Sent", apps)
