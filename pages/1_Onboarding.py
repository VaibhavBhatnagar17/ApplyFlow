import streamlit as st

from engine.profile import Profile, JobPreferences, ALL_SKILLS, TARGET_ROLES, TARGET_LOCATIONS
from engine.resume_parser import (
    parse_resume_pdf,
    extract_skills_from_text,
    extract_experience_years,
    extract_name_from_text,
    extract_email_from_text,
    extract_phone_from_text,
    render_resume_preview_png,
    png_bytes_to_base64,
    base64_to_png_bytes,
)
from engine.state import (
    save_profile,
    load_profile,
    save_resume_text,
    load_resume_text,
    save_resume_preview_b64,
    load_resume_preview_b64,
)
from engine.guard import require_login, sidebar_user_info, get_username

st.set_page_config(page_title="Onboarding | ApplyFlow", page_icon="📝", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Onboarding")
st.caption("Tell us who you are. These details directly drive search, ranking, and dashboard insights.")

existing_profile, existing_prefs = load_profile(username)
saved_resume = load_resume_text(username)
saved_preview_b64 = load_resume_preview_b64(username)

st.subheader("Step 1: Resume Upload")
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

extracted_skills = []
extracted_name = ""
extracted_email = ""
extracted_phone = ""
extracted_years = 0

if uploaded:
    with st.spinner("Parsing and indexing resume..."):
        try:
            text = parse_resume_pdf(uploaded)
            extracted_skills = extract_skills_from_text(text)
            extracted_years = extract_experience_years(text)
            extracted_name = extract_name_from_text(text)
            extracted_email = extract_email_from_text(text)
            extracted_phone = extract_phone_from_text(text)

            save_resume_text(text, username)

            preview_png = render_resume_preview_png(uploaded)
            if preview_png:
                save_resume_preview_b64(png_bytes_to_base64(preview_png), username)

            st.success(f"Resume indexed. Detected {len(extracted_skills)} skills.")
        except Exception as e:
            st.error(f"Could not parse PDF: {e}")

preview_b64 = load_resume_preview_b64(username)
if preview_b64:
    st.markdown("**Resume Preview (first page)**")
    st.image(base64_to_png_bytes(preview_b64), use_container_width=True)
elif saved_resume:
    st.info("Resume text saved. (Install preview dependency to render first page image.)")

st.subheader("Step 2: Professional Profile")
with st.form("profile_form"):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full Name", value=extracted_name or (existing_profile.name if existing_profile else ""))
        email = st.text_input("Email", value=extracted_email or (existing_profile.email if existing_profile else ""))
        phone = st.text_input("Phone", value=extracted_phone or (existing_profile.phone if existing_profile else ""))
        location = st.text_input("Current Location", value=existing_profile.location if existing_profile else "")
        years_exp = st.number_input("Years of Experience", min_value=0, max_value=40,
                                    value=extracted_years or (existing_profile.years_experience if existing_profile else 0))
        current_title = st.text_input("Current Title", value=existing_profile.current_title if existing_profile else "")
        current_company = st.text_input("Current Company", value=existing_profile.current_company if existing_profile else "")
    with c2:
        notice_period = st.text_input("Notice Period", value=existing_profile.notice_period if existing_profile else "30 days")
        work_auth = st.text_input("Work Authorization", value=existing_profile.work_authorization if existing_profile else "")
        work_mode = st.selectbox("Preferred Work Mode", ["remote", "hybrid", "onsite"],
                                 index=["remote", "hybrid", "onsite"].index(existing_profile.preferred_work_mode)
                                 if existing_profile and existing_profile.preferred_work_mode in ["remote", "hybrid", "onsite"] else 1)
        relocate = st.checkbox("Willing to relocate", value=existing_profile.willing_to_relocate if existing_profile else True)
        linkedin = st.text_input("LinkedIn URL", value=existing_profile.linkedin_url if existing_profile else "")
        github = st.text_input("GitHub URL", value=existing_profile.github_url if existing_profile else "")
        education = st.text_input("Education", value=existing_profile.education if existing_profile else "")

    summary = st.text_area("Professional Summary", height=120, value=existing_profile.summary if existing_profile else "")
    career_goal = st.text_area("Career Goal (next 12-24 months)", height=90, value=existing_profile.career_goal if existing_profile else "")
    certifications = st.text_input("Certifications", value=existing_profile.certifications if existing_profile else "")

    default_skills = extracted_skills or (existing_profile.core_skills if existing_profile else [])
    valid_defaults = [s for s in default_skills if s in ALL_SKILLS]
    core_skills = st.multiselect("Core Skills", options=ALL_SKILLS, default=valid_defaults)
    secondary_skills = st.multiselect("Secondary Skills", options=ALL_SKILLS,
                                      default=existing_profile.secondary_skills if existing_profile else [])

    extra_skills = st.text_input("Additional skills (comma-separated)")
    domains = st.multiselect("Domain Experience", ["Healthcare", "Fintech", "E-commerce", "Semiconductor", "SaaS", "Manufacturing", "Consulting"],
                             default=existing_profile.domains if existing_profile else [])
    achievements_text = st.text_area("Key Achievements (one per line)", height=110,
                                     value="\n".join(existing_profile.key_achievements) if existing_profile else "")

    st.markdown("---")
    st.subheader("Step 3: Job Preferences")
    p1, p2 = st.columns(2)
    with p1:
        target_titles = st.multiselect("Target Roles", options=TARGET_ROLES,
                                       default=(existing_prefs.target_titles if existing_prefs else TARGET_ROLES[:10]))
        target_locations = st.multiselect("Target Locations", options=TARGET_LOCATIONS,
                                          default=(existing_prefs.target_locations if existing_prefs else TARGET_LOCATIONS[:10]))
        job_types = st.multiselect("Job Types", ["Full-time", "Contract", "Internship", "Part-time"],
                                   default=existing_prefs.job_types if existing_prefs else ["Full-time"])
    with p2:
        remote_pref = st.selectbox("Remote Preference", ["remote_only", "remote_preferred", "hybrid_ok", "onsite_ok"],
                                   index=["remote_only", "remote_preferred", "hybrid_ok", "onsite_ok"].index(existing_prefs.remote_preference)
                                   if existing_prefs and existing_prefs.remote_preference in ["remote_only", "remote_preferred", "hybrid_ok", "onsite_ok"] else 1)
        min_salary = st.number_input("Minimum Salary (INR LPA)", min_value=0, step=1,
                                     value=existing_prefs.min_salary_inr // 100000 if existing_prefs else 0)
        min_match_score = st.slider("Minimum Match Score", min_value=0.0, max_value=1.0, step=0.05,
                                    value=existing_prefs.min_match_score if existing_prefs else 0.3)

    industries = st.multiselect("Preferred Industries", ["AI/ML", "Data", "Healthcare", "Fintech", "Semiconductor", "SaaS", "Consulting", "Manufacturing"],
                                default=existing_prefs.industries if existing_prefs else [])

    preferred_cos = st.text_input("Preferred Companies (comma-separated)",
                                  value=", ".join(existing_prefs.preferred_companies) if existing_prefs else "")
    excluded_cos = st.text_input("Excluded Companies (comma-separated)",
                                 value=", ".join(existing_prefs.excluded_companies) if existing_prefs else "")

    submitted = st.form_submit_button("Save Onboarding", type="primary", use_container_width=True)

    if submitted:
        all_core = list(dict.fromkeys(core_skills + [s.strip() for s in extra_skills.split(",") if s.strip()]))
        achievements = [a.strip() for a in achievements_text.strip().split("\n") if a.strip()]

        profile = Profile(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin_url=linkedin,
            github_url=github,
            years_experience=int(years_exp),
            current_title=current_title,
            current_company=current_company,
            summary=summary,
            core_skills=all_core,
            secondary_skills=secondary_skills,
            key_achievements=achievements,
            domains=domains,
            education=education,
            certifications=certifications,
            career_goal=career_goal,
            work_authorization=work_auth,
            notice_period=notice_period,
            preferred_work_mode=work_mode,
            willing_to_relocate=relocate,
        )

        prefs = JobPreferences(
            target_titles=target_titles,
            target_locations=target_locations,
            remote_preference=remote_pref,
            min_salary_inr=min_salary * 100000,
            job_types=job_types,
            industries=industries,
            excluded_companies=[c.strip() for c in excluded_cos.split(",") if c.strip()],
            preferred_companies=[c.strip() for c in preferred_cos.split(",") if c.strip()],
            min_match_score=min_match_score,
        )

        save_profile(profile, prefs, username)
        st.success("Onboarding saved. Dashboard and search are now personalized to this profile.")
        st.rerun()
