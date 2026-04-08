import streamlit as st
from engine.state import load_profile, load_user_saved_jobs
from engine.job_model import JobListing
from engine.cover_letter import CoverLetterGenerator
from engine.guard import require_login, sidebar_user_info, get_username

st.set_page_config(page_title="Cover Letters | ApplyFlow", page_icon="✉️", layout="wide")
sidebar_user_info()
require_login()

username = get_username()

st.title("Cover Letter Generator")
st.caption("Generate a tailored cover letter for any job in your database.")

profile, _ = load_profile(username)
if not profile or not profile.is_complete():
    st.warning("Complete onboarding first.")
    st.page_link("pages/1_Onboarding.py", label="Go to Onboarding", icon="📝")
    st.stop()

raw_listings = load_user_saved_jobs(username)
if not raw_listings:
    st.info("No saved jobs found. Save jobs from Job Search first.")
    st.stop()

jobs = [JobListing.from_active_job(e) for e in raw_listings]
jobs.sort(key=lambda j: j.match_score, reverse=True)

job_labels = [f"{j.company} — {j.title} ({j.match_quality or 'unknown'})" for j in jobs]
selected_idx = st.selectbox("Select a job", range(len(job_labels)), format_func=lambda i: job_labels[i])
selected_job = jobs[selected_idx]

with st.expander("Job Details", expanded=True):
    dc1, dc2 = st.columns(2)
    with dc1:
        st.write(f"**Company:** {selected_job.company}")
        st.write(f"**Title:** {selected_job.title}")
        st.write(f"**Location:** {selected_job.location}")
    with dc2:
        st.write(f"**Experience:** {selected_job.experience}")
        st.write(f"**Platform:** {selected_job.platform}")
        if selected_job.skills_matched:
            st.write(f"**Skills:** {', '.join(selected_job.skills_matched)}")
    if selected_job.url:
        st.link_button("View Job Posting", selected_job.url)

if st.button("Generate Cover Letter", type="primary", use_container_width=True):
    with st.spinner("Generating..."):
        gen = CoverLetterGenerator(profile)
        letter = gen.generate(selected_job)
    st.session_state["generated_letter"] = letter
    st.session_state["generated_for"] = selected_job.job_id

if "generated_letter" in st.session_state:
    st.subheader("Your Cover Letter")

    edited = st.text_area(
        "Edit below (changes are preserved until you generate again)",
        value=st.session_state["generated_letter"], height=400,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download as .txt", data=edited,
            file_name=f"cover_letter_{selected_job.company}_{selected_job.title}.txt".replace(" ", "_"),
            mime="text/plain", use_container_width=True,
        )
    with col2:
        if st.button("Copy to Clipboard", use_container_width=True):
            st.code(edited, language=None)
            st.info("Select all text above and copy (Ctrl+C / Cmd+C)")
