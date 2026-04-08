import streamlit as st
import plotly.express as px
import pandas as pd

from engine.state import load_profile, load_user_saved_jobs, save_application, load_applications
from engine.job_model import JobListing
from engine.matcher import JobMatcher
from engine.guard import require_login, sidebar_user_info, get_username

st.set_page_config(page_title="Dashboard | ApplyFlow", page_icon="📊", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Job Dashboard")

profile, prefs = load_profile(username)
if not profile or not profile.is_complete():
    st.warning("Complete onboarding first to see personalized matches.")
    st.page_link("pages/1_Onboarding.py", label="Go to Onboarding", icon="📝")
    st.stop()

raw_listings = load_user_saved_jobs(username)
if not raw_listings:
    st.info("No saved jobs yet. Use Job Search to fetch live openings and save them.")
    st.page_link("pages/4_Job_Search.py", label="Go to Job Search", icon="🔍")
    st.stop()

applied_ids = {a["job_id"] for a in load_applications(username)}

jobs = [JobListing.from_active_job(e) for e in raw_listings]
matcher = JobMatcher(profile, prefs)
results = matcher.score_jobs(jobs)

filtered_by_threshold = [r for r in results if r.score >= prefs.min_match_score]

total = len(results)
excellent = sum(1 for r in results if r.score >= 0.75)
good = sum(1 for r in results if 0.5 <= r.score < 0.75)
stretch = sum(1 for r in results if r.score < 0.5)
applied_count = len(applied_ids)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Saved Jobs", total)
c2.metric("Excellent Match", excellent)
c3.metric("Good Match", good)
c4.metric("Applied", applied_count)
c5.metric("Above Threshold", len(filtered_by_threshold))

with st.expander("How onboarding data impacts this dashboard", expanded=True):
    i1, i2 = st.columns(2)
    with i1:
        st.write(f"**Name / Persona:** {profile.name}")
        st.write(f"**Current Role:** {profile.current_title or 'n/a'}")
        st.write(f"**Experience:** {profile.years_experience} years")
        st.write(f"**Core Skills used in scoring:** {', '.join(profile.core_skills[:10])}")
        st.write(f"**Career Goal:** {profile.career_goal or 'n/a'}")
    with i2:
        st.write(f"**Target Roles:** {', '.join(prefs.target_titles[:8])}")
        st.write(f"**Target Locations:** {', '.join(prefs.target_locations[:8])}")
        st.write(f"**Remote Preference:** {prefs.remote_preference}")
        st.write(f"**Preferred Companies:** {', '.join(prefs.preferred_companies[:5]) or 'None'}")
        st.write(f"**Minimum Match Score:** {int(prefs.min_match_score * 100)}%")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    company_counts = {}
    for r in results:
        company_counts[r.job.company] = company_counts.get(r.job.company, 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])[:15]
    if top_companies:
        df_co = pd.DataFrame(top_companies, columns=["Company", "Openings"])
        fig = px.bar(df_co, x="Openings", y="Company", orientation="h", title="Saved Openings by Company")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=380)
        st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    quality_data = {"Excellent": excellent, "Good": good, "Stretch": stretch}
    df_q = pd.DataFrame(list(quality_data.items()), columns=["Quality", "Count"])
    fig2 = px.pie(df_q, values="Count", names="Quality", title="Match Quality")
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Saved Jobs")
f1, f2, f3, f4 = st.columns(4)
with f1:
    quality_filter = st.selectbox("Match Quality", ["All", "Excellent", "Good", "Stretch"])
with f2:
    all_companies = sorted({r.job.company for r in results})
    company_filter = st.selectbox("Company", ["All"] + all_companies)
with f3:
    threshold_only = st.checkbox("Only above min match score", value=False)
with f4:
    search_text = st.text_input("Search")

filtered = results
if quality_filter == "Excellent":
    filtered = [r for r in filtered if r.score >= 0.75]
elif quality_filter == "Good":
    filtered = [r for r in filtered if 0.5 <= r.score < 0.75]
elif quality_filter == "Stretch":
    filtered = [r for r in filtered if r.score < 0.5]

if company_filter != "All":
    filtered = [r for r in filtered if r.job.company == company_filter]

if threshold_only:
    filtered = [r for r in filtered if r.score >= prefs.min_match_score]

if search_text:
    s = search_text.lower()
    filtered = [r for r in filtered if s in r.job.title.lower() or s in r.job.company.lower() or s in r.job.description.lower()]

st.caption(f"Showing {len(filtered)} of {len(results)} saved jobs")

for i, r in enumerate(filtered):
    job = r.job
    is_applied = job.job_id in applied_ids
    with st.container():
        cols = st.columns([3, 2, 1, 2, 1, 1])
        with cols[0]:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
            if r.reasons:
                st.caption(r.reasons[0])
        with cols[1]:
            st.caption(f"📍 {job.location}")
            st.caption(f"🎓 {job.experience or 'n/a'}")
        with cols[2]:
            st.markdown(f"**{r.score:.0%}**")
        with cols[3]:
            st.caption(f"Platform: {job.platform}")
            st.caption(f"Posted: {job.posted_date or 'n/a'}")
        with cols[4]:
            if job.url:
                st.link_button("Apply", job.url, use_container_width=True)
        with cols[5]:
            if not is_applied:
                if st.button("Mark Applied", key=f"apply_{i}_{job.job_id}", use_container_width=True):
                    save_application(job.job_id, job.company, job.title, job.url, username=username)
                    st.rerun()
            else:
                st.success("Applied")
        st.divider()
