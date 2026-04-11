"""Profile — Tell us about yourself so we can find the perfect jobs."""

import streamlit as st

st.set_page_config(page_title="Profile | ApplyFlow", page_icon="👤", layout="wide")

from engine.guard import require_login, get_username, sidebar_user_info
from engine.profile import Profile, JobPreferences, ALL_SKILLS, TARGET_ROLES, TARGET_LOCATIONS
from engine.resume_parser import (
    parse_resume_pdf,
    extract_skills_from_text,
    extract_experience_years,
    extract_name_from_text,
    extract_email_from_text,
    extract_phone_from_text,
)
from engine.state import (
    save_profile,
    load_profile,
    save_resume_text,
    load_resume_text,
)

sidebar_user_info()
require_login()
username = get_username()

profile, prefs = load_profile(username)
saved_resume = load_resume_text(username)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
.section-header {
    font-size: 16px; font-weight: 700; color: #22c984;
    text-transform: uppercase; letter-spacing: 1.2px;
    margin: 28px 0 8px; padding-bottom: 6px;
    border-bottom: 1px solid #2a2f3d;
}
.profile-hero {
    background: linear-gradient(135deg, #13161d 0%, #1a1f2e 100%);
    border: 1px solid #2a2f3d; border-radius: 16px;
    padding: 28px 32px; margin-bottom: 24px;
}
.profile-hero h1 { font-size: 26px; margin-bottom: 4px; }
.profile-hero p { color: #8c93a8; font-size: 14px; }
.strength-bar {
    height: 6px; border-radius: 3px; background: #252a35;
    margin-top: 12px; overflow: hidden;
}
.strength-fill {
    height: 100%; border-radius: 3px;
    transition: width .3s;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────
def _strength(p):
    s = 0
    if p and p.name: s += 12
    if p and p.email: s += 8
    if p and p.current_title: s += 15
    if p and p.years_experience > 0: s += 15
    if p and len(p.core_skills) >= 3: s += 20
    if p and p.summary: s += 10
    if p and p.key_achievements: s += 10
    if p and p.education: s += 10
    return min(s, 100)

strength = _strength(profile)
bar_color = "#22c984" if strength >= 70 else ("#5b8def" if strength >= 40 else "#f0b429")

st.markdown(f"""
<div class="profile-hero">
    <h1>👤 Your Profile</h1>
    <p>The better we understand you, the better we match jobs to your skills and goals.</p>
    <div style="display:flex;align-items:center;gap:12px;margin-top:14px">
        <span style="font-size:13px;font-weight:700;color:{bar_color}">Profile Strength: {strength}%</span>
    </div>
    <div class="strength-bar">
        <div class="strength-fill" style="width:{strength}%;background:{bar_color}"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Resume Upload ──────────────────────────────────────────────────
st.markdown('<div class="section-header">📄 Resume</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="resume_upload")

if uploaded:
    raw_bytes = uploaded.read()
    text = parse_resume_pdf(raw_bytes)
    if text:
        auto_skills = extract_skills_from_text(text)
        auto_exp = extract_experience_years(text)
        auto_name = extract_name_from_text(text)
        auto_email = extract_email_from_text(text)
        auto_phone = extract_phone_from_text(text)
        save_resume_text(text, username)
        st.success("Resume parsed! We extracted your details below — review and adjust.")
        with st.expander("Extracted text", expanded=False):
            st.text(text[:3000])
    else:
        st.error("Could not extract text. Try a different PDF.")
        auto_skills, auto_exp, auto_name, auto_email, auto_phone = [], 0, "", "", ""
elif saved_resume:
    auto_skills = extract_skills_from_text(saved_resume)
    auto_exp = extract_experience_years(saved_resume)
    auto_name = extract_name_from_text(saved_resume)
    auto_email = extract_email_from_text(saved_resume)
    auto_phone = extract_phone_from_text(saved_resume)
    st.info("Using your previously uploaded resume.")
else:
    auto_skills, auto_exp, auto_name, auto_email, auto_phone = [], 0, "", "", ""

# ── Profile Form ───────────────────────────────────────────────────
with st.form("profile_form"):
    st.markdown('<div class="section-header">🧑‍💼 About You</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full Name", value=(profile.name if profile else auto_name) or "")
        email = st.text_input("Email", value=(profile.email if profile else auto_email) or "")
        phone = st.text_input("Phone", value=(profile.phone if profile else auto_phone) or "")
        location = st.text_input("Current City", value=(profile.location if profile else "") or "")
    with c2:
        current_title = st.text_input("Current Job Title", value=(profile.current_title if profile else "") or "")
        current_company = st.text_input("Current Company", value=(profile.current_company if profile else "") or "")
        years_exp = st.number_input("Years of Experience", 0, 50,
            value=(profile.years_experience if profile else auto_exp) or 0)
        notice_opts = ["Immediate", "15 days", "30 days", "60 days", "90 days"]
        notice_period = st.selectbox("Notice Period", notice_opts,
            index=notice_opts.index(profile.notice_period if profile and profile.notice_period in notice_opts else "30 days"))

    summary = st.text_area("Professional Summary (2–3 sentences about what you do best)",
        value=(profile.summary if profile else "") or "", height=100)

    career_goal = st.text_area("Career Goal — what kind of role/impact are you looking for?",
        value=(profile.career_goal if profile else "") or "", height=80,
        placeholder="e.g. I want to lead an ML team building production LLM systems at a product company")

    st.markdown('<div class="section-header">🛠️ Skills & Strengths</div>', unsafe_allow_html=True)

    pre_skills = profile.core_skills if profile and profile.core_skills else auto_skills
    core_skills = st.multiselect("Core Skills", ALL_SKILLS,
        default=[s for s in pre_skills if s in ALL_SKILLS])
    extra_skills = st.text_input("Additional Skills (comma-separated)",
        value=", ".join(profile.secondary_skills) if profile and profile.secondary_skills else "")

    achievements_text = st.text_area("Key Achievements (one per line — quantified results work best)",
        value="\n".join(profile.key_achievements) if profile and profile.key_achievements else "",
        height=120,
        placeholder="e.g. Increased model accuracy from 72% to 94% for fraud detection\n"
                    "e.g. Built real-time pipeline processing 50k events/sec on Kafka")

    education = st.text_input("Education",
        value=(profile.education if profile else "") or "",
        placeholder="e.g. M.Tech CS, IIT Delhi (2018)")

    c3, c4 = st.columns(2)
    with c3:
        linkedin = st.text_input("LinkedIn URL", value=(profile.linkedin_url if profile else "") or "")
    with c4:
        github = st.text_input("GitHub URL", value=(profile.github_url if profile else "") or "")

    st.markdown('<div class="section-header">🎯 What You\'re Looking For</div>', unsafe_allow_html=True)

    c5, c6 = st.columns(2)
    with c5:
        dr = prefs.target_titles if prefs else TARGET_ROLES[:6]
        target_roles = st.multiselect("Target Roles", TARGET_ROLES,
            default=[r for r in dr if r in TARGET_ROLES])
    with c6:
        dl = prefs.target_locations if prefs else TARGET_LOCATIONS[:6]
        target_locations = st.multiselect("Target Locations", TARGET_LOCATIONS,
            default=[l for l in dl if l in TARGET_LOCATIONS])

    remote_opts = ["Remote Only", "Remote Preferred", "Hybrid", "On-site OK", "No Preference"]
    remote_map_to_idx = {"remote_only": 0, "remote_preferred": 1, "hybrid": 2, "onsite": 3, "no_preference": 4}
    remote_pref = st.selectbox("Remote Preference", remote_opts,
        index=remote_map_to_idx.get(prefs.remote_preference if prefs else "remote_preferred", 1))

    c7, c8 = st.columns(2)
    with c7:
        min_salary = st.number_input("Minimum Salary (LPA ₹)", 0, 200,
            value=(prefs.min_salary_inr // 100_000 if prefs and prefs.min_salary_inr else 0))
    with c8:
        relocate = st.checkbox("Willing to Relocate",
            value=(profile.willing_to_relocate if profile else True))

    preferred_cos = st.text_input("Preferred Companies (comma-separated, optional)",
        value=", ".join(prefs.preferred_companies) if prefs and prefs.preferred_companies else "")
    excluded_cos = st.text_input("Excluded Companies (comma-separated, optional)",
        value=", ".join(prefs.excluded_companies) if prefs and prefs.excluded_companies else "")

    submitted = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)

if submitted:
    all_skills = list(dict.fromkeys(core_skills + [s.strip() for s in extra_skills.split(",") if s.strip()]))
    achievements = [a.strip() for a in achievements_text.strip().split("\n") if a.strip()]
    remote_map = {"Remote Only": "remote_only", "Remote Preferred": "remote_preferred",
                  "Hybrid": "hybrid", "On-site OK": "onsite", "No Preference": "no_preference"}

    new_profile = Profile(
        name=name, email=email, phone=phone, location=location,
        current_title=current_title, current_company=current_company,
        years_experience=years_exp, summary=summary,
        core_skills=all_skills,
        secondary_skills=[s.strip() for s in extra_skills.split(",") if s.strip()],
        key_achievements=achievements, education=education,
        linkedin_url=linkedin, github_url=github,
        career_goal=career_goal, notice_period=notice_period,
        willing_to_relocate=relocate,
    )
    new_prefs = JobPreferences(
        target_titles=target_roles, target_locations=target_locations,
        remote_preference=remote_map.get(remote_pref, "remote_preferred"),
        min_salary_inr=min_salary * 100_000,
        preferred_companies=[c.strip() for c in preferred_cos.split(",") if c.strip()],
        excluded_companies=[c.strip() for c in excluded_cos.split(",") if c.strip()],
    )

    save_profile(new_profile, new_prefs, username)
    st.success("Profile saved! Head to **Find Jobs** to discover your best matches.")
    st.balloons()
