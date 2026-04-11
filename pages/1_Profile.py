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
    save_resume_preview_b64,
    load_resume_preview_b64,
)

sidebar_user_info()
require_login()
username = get_username()

profile, prefs = load_profile(username)
saved_resume = load_resume_text(username)

st.markdown("# 👤 Your Profile")
st.caption("The better we understand you, the better we match jobs to your skills and goals.")

# ── Step 1: Resume Upload ──────────────────────────────────────────
st.markdown("### 📄 Resume")
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
        st.success("Resume parsed successfully!")
        with st.expander("Extracted text", expanded=False):
            st.text(text[:3000])
    else:
        st.error("Could not extract text. Please try a different PDF.")
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

st.markdown("---")

# ── Step 2: About You + Preferences (single form) ─────────────────
with st.form("profile_form"):
    st.markdown("### 🧑‍💼 About You")
    col_a, col_b = st.columns(2)
    with col_a:
        name = st.text_input("Full Name", value=(profile.name if profile else auto_name) or "")
        email = st.text_input("Email", value=(profile.email if profile else auto_email) or "")
        phone = st.text_input("Phone", value=(profile.phone if profile else auto_phone) or "")
        location = st.text_input("Current City", value=(profile.location if profile else "") or "")
    with col_b:
        current_title = st.text_input("Current Job Title", value=(profile.current_title if profile else "") or "")
        current_company = st.text_input("Current Company", value=(profile.current_company if profile else "") or "")
        years_exp = st.number_input(
            "Years of Experience",
            min_value=0, max_value=50,
            value=(profile.years_experience if profile else auto_exp) or 0,
        )
        notice_period = st.selectbox(
            "Notice Period",
            ["Immediate", "15 days", "30 days", "60 days", "90 days"],
            index=["Immediate", "15 days", "30 days", "60 days", "90 days"].index(
                profile.notice_period if profile and profile.notice_period in
                ["Immediate", "15 days", "30 days", "60 days", "90 days"] else "30 days"
            ),
        )

    summary = st.text_area(
        "Professional Summary (2-3 sentences about what you do best)",
        value=(profile.summary if profile else "") or "",
        height=100,
    )

    st.markdown("### 🛠️ Skills & Strengths")
    pre_skills = profile.core_skills if profile and profile.core_skills else auto_skills
    valid_pre = [s for s in pre_skills if s in ALL_SKILLS]
    core_skills = st.multiselect("Core Skills", ALL_SKILLS, default=valid_pre)
    extra_skills = st.text_input(
        "Additional Skills (comma-separated)",
        value=", ".join(profile.secondary_skills) if profile and profile.secondary_skills else "",
    )

    achievements_text = st.text_area(
        "Key Achievements (one per line — quantified results work best)",
        value="\n".join(profile.key_achievements) if profile and profile.key_achievements else "",
        height=120,
        placeholder="e.g. Increased model accuracy from 72% to 94% for fraud detection\n"
                    "e.g. Built real-time pipeline processing 50k events/sec on Kafka",
    )

    education = st.text_input(
        "Education",
        value=(profile.education if profile else "") or "",
        placeholder="e.g. M.Tech CS, IIT Delhi (2018)",
    )

    col_l, col_g = st.columns(2)
    with col_l:
        linkedin = st.text_input("LinkedIn URL", value=(profile.linkedin_url if profile else "") or "")
    with col_g:
        github = st.text_input("GitHub URL", value=(profile.github_url if profile else "") or "")

    career_goal = st.text_area(
        "Career Goal (what kind of role/impact are you looking for?)",
        value=(profile.career_goal if profile else "") or "",
        height=80,
        placeholder="e.g. I want to lead an ML team building production LLM systems at a product company",
    )

    st.markdown("---")
    st.markdown("### 🎯 What You're Looking For")

    col_r, col_lo = st.columns(2)
    with col_r:
        default_roles = prefs.target_titles if prefs else TARGET_ROLES[:6]
        valid_roles = [r for r in default_roles if r in TARGET_ROLES]
        target_roles = st.multiselect("Target Roles", TARGET_ROLES, default=valid_roles)
    with col_lo:
        default_locs = prefs.target_locations if prefs else TARGET_LOCATIONS[:6]
        valid_locs = [l for l in default_locs if l in TARGET_LOCATIONS]
        target_locations = st.multiselect("Target Locations", TARGET_LOCATIONS, default=valid_locs)

    remote_pref = st.selectbox(
        "Remote Preference",
        ["Remote Only", "Remote Preferred", "Hybrid", "On-site OK", "No Preference"],
        index={"remote_only": 0, "remote_preferred": 1, "hybrid": 2, "onsite": 3, "no_preference": 4}.get(
            prefs.remote_preference if prefs else "remote_preferred", 1
        ),
    )

    col_sal, col_rel = st.columns(2)
    with col_sal:
        min_salary = st.number_input(
            "Minimum Salary (LPA ₹)",
            min_value=0, max_value=200,
            value=(prefs.min_salary_inr // 100_000 if prefs and prefs.min_salary_inr else 0),
        )
    with col_rel:
        relocate = st.checkbox(
            "Willing to Relocate",
            value=(profile.willing_to_relocate if profile else True),
        )

    preferred_cos = st.text_input(
        "Preferred Companies (comma-separated, optional)",
        value=", ".join(prefs.preferred_companies) if prefs and prefs.preferred_companies else "",
    )
    excluded_cos = st.text_input(
        "Excluded Companies (comma-separated, optional)",
        value=", ".join(prefs.excluded_companies) if prefs and prefs.excluded_companies else "",
    )

    submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

if submitted:
    all_skills = list(dict.fromkeys(core_skills + [s.strip() for s in extra_skills.split(",") if s.strip()]))
    achievements = [a.strip() for a in achievements_text.strip().split("\n") if a.strip()]
    remote_map = {
        "Remote Only": "remote_only",
        "Remote Preferred": "remote_preferred",
        "Hybrid": "hybrid",
        "On-site OK": "onsite",
        "No Preference": "no_preference",
    }

    new_profile = Profile(
        name=name,
        email=email,
        phone=phone,
        location=location,
        current_title=current_title,
        current_company=current_company,
        years_experience=years_exp,
        summary=summary,
        core_skills=all_skills,
        secondary_skills=[s.strip() for s in extra_skills.split(",") if s.strip()],
        key_achievements=achievements,
        education=education,
        linkedin_url=linkedin,
        github_url=github,
        career_goal=career_goal,
        notice_period=notice_period,
        willing_to_relocate=relocate,
    )

    new_prefs = JobPreferences(
        target_titles=target_roles,
        target_locations=target_locations,
        remote_preference=remote_map.get(remote_pref, "remote_preferred"),
        min_salary_inr=min_salary * 100_000,
        preferred_companies=[c.strip() for c in preferred_cos.split(",") if c.strip()],
        excluded_companies=[c.strip() for c in excluded_cos.split(",") if c.strip()],
    )

    save_profile(new_profile, new_prefs, username)
    st.success("Profile saved! Head to **Find Jobs** to discover your best matches.")
    st.balloons()
