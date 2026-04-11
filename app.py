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


def _profile_strength(profile) -> int:
    score = 0
    if profile.name:
        score += 10
    if profile.email:
        score += 10
    if profile.current_title:
        score += 15
    if profile.years_experience > 0:
        score += 15
    if len(profile.core_skills) >= 3:
        score += 20
    if profile.summary:
        score += 10
    if len(profile.key_achievements) >= 1:
        score += 10
    if profile.education:
        score += 10
    return min(score, 100)


sidebar_user_info()
username = get_username()

if username:
    profile, prefs = load_profile(username)
    saved = load_user_saved_jobs(username)
    apps = load_applications(username)

    st.markdown("# ApplyFlow")
    st.markdown("**Understand you. Find the best jobs. Apply.**")

    if not profile or not profile.is_complete():
        st.warning("Complete your profile so we can find the best jobs for you.")
        st.page_link("pages/1_Profile.py", label="Set Up Profile", icon="👤")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Matched Jobs", len(saved))
        c2.metric("Applications", len(apps))
        c3.metric("Profile Strength", f"{_profile_strength(profile)}%")

        st.markdown("---")
        st.markdown("### Your Flow")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 1. Profile")
            st.caption("We understand your skills, experience, and goals.")
            st.page_link("pages/1_Profile.py", label="Edit Profile", icon="👤")
        with col2:
            st.markdown("#### 2. Find Jobs")
            st.caption("Search across platforms. We score every job against your profile.")
            st.page_link("pages/2_Find_Jobs.py", label="Find Jobs", icon="🔍")
        with col3:
            st.markdown("#### 3. Dashboard")
            st.caption("Your best matches with cover letters, apply links, and tracking.")
            st.page_link("pages/3_Dashboard.py", label="Open Dashboard", icon="📊")

else:
    st.markdown("# ApplyFlow")
    st.markdown(
        "**From resume to offer, in one smooth flow.**\n\n"
        "Upload your resume, tell us what you're looking for, "
        "and we'll score every opening against your profile — "
        "with cover letters and one-click apply links."
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            lu = st.text_input("Username", key="login_user")
            lp = st.text_input("Password", type="password", key="login_pass")
            if st.form_submit_button("Login", type="primary", use_container_width=True):
                if not lu or not lp:
                    st.error("Please enter both username and password.")
                else:
                    ok, msg = login(lu, lp)
                    if ok:
                        st.session_state["username"] = lu.strip().lower()
                        st.session_state["display_name"] = msg
                        st.rerun()
                    else:
                        st.error(msg)

    with tab2:
        with st.form("register_form"):
            st.subheader("Create Account")
            rn = st.text_input("Display Name", key="reg_name")
            ru = st.text_input("Username", key="reg_user")
            rp = st.text_input("Password", type="password", key="reg_pass")
            rp2 = st.text_input("Confirm Password", type="password", key="reg_pass2")
            if st.form_submit_button("Register", type="primary", use_container_width=True):
                if rp != rp2:
                    st.error("Passwords don't match.")
                elif not ru or not rp:
                    st.error("Please fill in all fields.")
                else:
                    ok, msg = register(ru, rp, rn)
                    if ok:
                        st.session_state["username"] = ru.strip().lower()
                        st.session_state["display_name"] = rn or ru
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
