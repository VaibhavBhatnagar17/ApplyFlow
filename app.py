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
    s = 0
    if profile.name: s += 10
    if profile.email: s += 10
    if profile.current_title: s += 15
    if profile.years_experience > 0: s += 15
    if len(profile.core_skills) >= 3: s += 20
    if profile.summary: s += 10
    if len(profile.key_achievements) >= 1: s += 10
    if profile.education: s += 10
    return min(s, 100)


# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #13161d 0%, #1a1f2e 100%);
    border: 1px solid #2a2f3d; border-radius: 16px;
    padding: 36px 40px; margin-bottom: 28px; text-align: center;
}
.hero h1 { font-size: 36px; margin-bottom: 8px; }
.hero h1 span { color: #22c984; }
.hero p { color: #8c93a8; font-size: 16px; max-width: 600px; margin: 0 auto; line-height: 1.6; }
.flow-card {
    background: #13161d; border: 1px solid #2a2f3d; border-radius: 12px;
    padding: 24px; text-align: center; transition: border-color .15s;
}
.flow-card:hover { border-color: #5b8def; }
.flow-card h3 { font-size: 16px; margin: 10px 0 6px; }
.flow-card p { font-size: 13px; color: #8c93a8; }
.flow-num {
    width: 36px; height: 36px; border-radius: 50%;
    background: rgba(91,141,239,.12); color: #5b8def;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 16px;
}
.metric-row {
    display: flex; gap: 12px; margin-bottom: 24px;
}
.metric-box {
    flex: 1; background: #13161d; border: 1px solid #2a2f3d;
    border-radius: 12px; padding: 16px 20px; text-align: center;
}
.metric-n { font-size: 28px; font-weight: 800; }
.metric-l { font-size: 11px; color: #8c93a8; text-transform: uppercase; letter-spacing: .5px; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

sidebar_user_info()
username = get_username()

if username:
    profile, prefs = load_profile(username)
    saved = load_user_saved_jobs(username)
    apps = load_applications(username)

    if not profile or not profile.is_complete():
        st.markdown("""
        <div class="hero">
            <h1>Welcome to <span>ApplyFlow</span></h1>
            <p>Let's get started — complete your profile so we can find the best jobs for you.</p>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/1_Profile.py", label="Set Up Profile →", icon="👤")
    else:
        display = st.session_state.get("display_name", username)
        strength = _profile_strength(profile)
        bar_color = "#22c984" if strength >= 70 else ("#5b8def" if strength >= 40 else "#f0b429")

        st.markdown(f"""
        <div class="hero">
            <h1>Welcome back, <span>{display}</span></h1>
            <p>Your profile is {strength}% complete. Here's your job search at a glance.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box"><div class="metric-n" style="color:#5b8def">{len(saved)}</div><div class="metric-l">Matched Jobs</div></div>
            <div class="metric-box"><div class="metric-n" style="color:#a78bfa">{len(apps)}</div><div class="metric-l">Applications</div></div>
            <div class="metric-box"><div class="metric-n" style="color:{bar_color}">{strength}%</div><div class="metric-l">Profile Strength</div></div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
            <div class="flow-card">
                <div class="flow-num">1</div>
                <h3>Profile</h3>
                <p>We understand your skills, experience, and goals.</p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/1_Profile.py", label="Edit Profile", icon="👤")
        with c2:
            st.markdown("""
            <div class="flow-card">
                <div class="flow-num">2</div>
                <h3>Find Jobs</h3>
                <p>Search across platforms. We score every job against you.</p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/2_Find_Jobs.py", label="Find Jobs", icon="🔍")
        with c3:
            st.markdown("""
            <div class="flow-card">
                <div class="flow-num">3</div>
                <h3>Dashboard</h3>
                <p>Your best matches with cover letters and apply links.</p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/3_Dashboard.py", label="Open Dashboard", icon="📊")

else:
    st.markdown("""
    <div class="hero">
        <h1>🚀 <span>ApplyFlow</span></h1>
        <p>From resume to offer, in one smooth flow. Upload your resume, tell us what you're looking for,
        and we'll score every opening against your profile — with cover letters and one-click apply links.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
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
