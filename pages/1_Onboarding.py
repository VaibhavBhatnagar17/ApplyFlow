import streamlit as st
from engine.profile import Profile, JobPreferences, ALL_SKILLS, TARGET_ROLES, TARGET_LOCATIONS
from engine.resume_parser import (
    parse_resume_pdf, extract_skills_from_text,
    extract_experience_years, extract_name_from_text,
    extract_email_from_text, extract_phone_from_text,
)
from engine.state import save_profile, load_profile

st.set_page_config(page_title="Onboarding | ApplyFlow", page_icon="📝", layout="wide")
st.title("Onboarding")
st.caption("Upload your resume and set your preferences to get personalized job matches.")

existing_profile, existing_prefs = load_profile()

# --- Resume Upload ---
st.subheader("Step 1: Upload Resume")
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

extracted_skills = []
extracted_name = ""
extracted_email = ""
extracted_phone = ""
extracted_years = 0

if uploaded:
    with st.spinner("Parsing resume..."):
        try:
            text = parse_resume_pdf(uploaded)
            extracted_skills = extract_skills_from_text(text)
            extracted_years = extract_experience_years(text)
            extracted_name = extract_name_from_text(text)
            extracted_email = extract_email_from_text(text)
            extracted_phone = extract_phone_from_text(text)

            st.success(f"Extracted {len(extracted_skills)} skills from resume")
            if extracted_skills:
                st.write("**Detected skills:**", ", ".join(extracted_skills))
            with st.expander("View extracted text"):
                st.text(text[:3000])
        except Exception as e:
            st.error(f"Could not parse PDF: {e}")

# --- Profile Form ---
st.subheader("Step 2: Your Details")

with st.form("profile_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name", value=extracted_name or (existing_profile.name if existing_profile else ""))
        email = st.text_input("Email", value=extracted_email or (existing_profile.email if existing_profile else ""))
        phone = st.text_input("Phone", value=extracted_phone or (existing_profile.phone if existing_profile else ""))
        location = st.text_input("Current Location", value=existing_profile.location if existing_profile else "Bangalore, India")

    with col2:
        current_title = st.text_input("Current Title", value=existing_profile.current_title if existing_profile else "")
        current_company = st.text_input("Current Company", value=existing_profile.current_company if existing_profile else "")
        years_exp = st.number_input("Years of Experience", min_value=0, max_value=40,
                                     value=extracted_years or (existing_profile.years_experience if existing_profile else 0))
        notice_period = st.text_input("Notice Period", value=existing_profile.notice_period if existing_profile else "30 days")

    summary = st.text_area("Professional Summary", height=120,
                            value=existing_profile.summary if existing_profile else "")

    default_skills = extracted_skills or (existing_profile.core_skills if existing_profile else [])
    valid_defaults = [s for s in default_skills if s in ALL_SKILLS]
    skills = st.multiselect("Core Skills", options=ALL_SKILLS, default=valid_defaults)

    extra_skills = st.text_input("Additional skills (comma-separated)", value="")

    achievements_text = st.text_area(
        "Key Achievements (one per line)", height=100,
        value="\n".join(existing_profile.key_achievements) if existing_profile else "",
    )

    education = st.text_input("Education", value=existing_profile.education if existing_profile else "")
    linkedin = st.text_input("LinkedIn URL", value=existing_profile.linkedin_url if existing_profile else "")
    github = st.text_input("GitHub URL", value=existing_profile.github_url if existing_profile else "")
    relocate = st.checkbox("Willing to relocate", value=existing_profile.willing_to_relocate if existing_profile else True)

    # --- Preferences ---
    st.markdown("---")
    st.subheader("Step 3: Job Preferences")

    pref_col1, pref_col2 = st.columns(2)
    with pref_col1:
        target_titles = st.multiselect(
            "Target Roles",
            options=TARGET_ROLES,
            default=(existing_prefs.target_titles if existing_prefs else TARGET_ROLES[:6]),
        )
        target_locations = st.multiselect(
            "Target Locations",
            options=TARGET_LOCATIONS,
            default=(existing_prefs.target_locations if existing_prefs else TARGET_LOCATIONS[:10]),
        )
    with pref_col2:
        remote_pref = st.selectbox(
            "Remote Preference",
            ["remote_only", "remote_preferred", "hybrid_ok", "onsite_ok"],
            index=["remote_only", "remote_preferred", "hybrid_ok", "onsite_ok"].index(
                existing_prefs.remote_preference if existing_prefs else "remote_preferred"
            ),
        )
        min_salary = st.number_input(
            "Min Salary (INR LPA)", min_value=0, step=5,
            value=existing_prefs.min_salary_inr // 100000 if existing_prefs else 0,
        )

    preferred_cos = st.text_input(
        "Preferred Companies (comma-separated)",
        value=", ".join(existing_prefs.preferred_companies) if existing_prefs else "",
    )
    excluded_cos = st.text_input(
        "Excluded Companies (comma-separated)",
        value=", ".join(existing_prefs.excluded_companies) if existing_prefs else "",
    )

    submitted = st.form_submit_button("Save Profile & Preferences", type="primary", use_container_width=True)

    if submitted:
        all_skills = skills + [s.strip() for s in extra_skills.split(",") if s.strip()]
        achievements = [a.strip() for a in achievements_text.strip().split("\n") if a.strip()]

        profile = Profile(
            name=name, email=email, phone=phone, location=location,
            linkedin_url=linkedin, github_url=github,
            years_experience=int(years_exp), current_title=current_title,
            current_company=current_company, summary=summary,
            core_skills=all_skills, key_achievements=achievements,
            education=education, willing_to_relocate=relocate,
            notice_period=notice_period,
        )
        prefs = JobPreferences(
            target_titles=target_titles, target_locations=target_locations,
            remote_preference=remote_pref, min_salary_inr=min_salary * 100000,
            excluded_companies=[c.strip() for c in excluded_cos.split(",") if c.strip()],
            preferred_companies=[c.strip() for c in preferred_cos.split(",") if c.strip()],
        )
        save_profile(profile, prefs)
        st.success("Profile saved! Head to the Dashboard to see your matched jobs.")
        st.balloons()
