import streamlit as st
import plotly.express as px
import pandas as pd
from dataclasses import asdict

from engine.state import load_profile, load_active_jobs, save_application, load_applications
from engine.job_model import JobListing
from engine.matcher import JobMatcher
from engine.guard import require_login, sidebar_user_info, get_username
from engine.llm import OpenSourceInsights

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

raw_listings = load_active_jobs()
if not raw_listings:
    st.info("No jobs in database yet. Use Job Search to find some.")
    st.stop()

applied_ids = {a["job_id"] for a in load_applications(username)}

jobs = [JobListing.from_active_job(e) for e in raw_listings]
matcher = JobMatcher(profile, prefs)
results = matcher.score_jobs(jobs)

# --- Summary Stats ---
total = len(results)
excellent = sum(1 for r in results if r.score >= 0.75)
good = sum(1 for r in results if 0.5 <= r.score < 0.75)
stretch = sum(1 for r in results if r.score < 0.5)
applied_count = len(applied_ids)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Jobs", total)
c2.metric("Excellent Match", excellent)
c3.metric("Good Match", good)
c4.metric("Applied", applied_count)

# --- AI Insights (managed API) ---
with st.expander("AI Insights (Managed API)", expanded=False):
    llm = OpenSourceInsights()
    st.caption(
        f"Provider: `{llm.provider}` | Model: `{llm.model}`. "
        "Set `OPENROUTER_API_KEY` or `OPENAI_API_KEY` to enable."
    )
    if llm.is_available():
        st.success("LLM configured and ready.")
    else:
        st.info("LLM key not configured. Showing deterministic fallback insights.")

    if st.button("Generate AI Insights", use_container_width=True):
        with st.spinner("Generating insights..."):
            st.session_state["dashboard_ai_insights"] = llm.dashboard_insights(profile, prefs, results)

    if st.session_state.get("dashboard_ai_insights"):
        st.markdown(st.session_state["dashboard_ai_insights"])

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    company_counts = {}
    for r in results:
        company_counts[r.job.company] = company_counts.get(r.job.company, 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])[:15]
    if top_companies:
        df_co = pd.DataFrame(top_companies, columns=["Company", "Openings"])
        fig = px.bar(df_co, x="Openings", y="Company", orientation="h",
                     title="Top Companies by Openings", color="Openings",
                     color_continuous_scale="Viridis")
        fig.update_layout(yaxis=dict(autorange="reversed"), height=400,
                         margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    quality_data = {"Excellent (75%+)": excellent, "Good (50-75%)": good, "Stretch (<50%)": stretch}
    df_q = pd.DataFrame(list(quality_data.items()), columns=["Quality", "Count"])
    fig2 = px.pie(df_q, values="Count", names="Quality", title="Match Quality Distribution",
                  color_discrete_sequence=["#22c55e", "#6C63FF", "#f59e0b"])
    fig2.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig2, use_container_width=True)

# --- Filters ---
st.subheader("Job Listings")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    quality_filter = st.selectbox("Match Quality", ["All", "Excellent (75%+)", "Good (50-75%)", "Stretch (<50%)"])
with filter_col2:
    all_companies = sorted({r.job.company for r in results})
    company_filter = st.selectbox("Company", ["All"] + all_companies)
with filter_col3:
    all_locations = sorted({r.job.location for r in results})
    location_filter = st.selectbox("Location", ["All"] + all_locations)
with filter_col4:
    search_text = st.text_input("Search", placeholder="Search title, company, skills...")

filtered = results
if quality_filter == "Excellent (75%+)":
    filtered = [r for r in filtered if r.score >= 0.75]
elif quality_filter == "Good (50-75%)":
    filtered = [r for r in filtered if 0.5 <= r.score < 0.75]
elif quality_filter == "Stretch (<50%)":
    filtered = [r for r in filtered if r.score < 0.5]

if company_filter != "All":
    filtered = [r for r in filtered if r.job.company == company_filter]
if location_filter != "All":
    filtered = [r for r in filtered if r.job.location == location_filter]
if search_text:
    sl = search_text.lower()
    filtered = [r for r in filtered if sl in r.job.title.lower()
                or sl in r.job.company.lower()
                or sl in r.job.description.lower()]

st.caption(f"Showing {len(filtered)} of {total} jobs")

# --- Job Table ---
for i, r in enumerate(filtered):
    job = r.job
    is_applied = job.job_id in applied_ids

    score_color = "green" if r.score >= 0.75 else ("blue" if r.score >= 0.5 else "orange")

    with st.container():
        cols = st.columns([3, 2, 1, 1, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
        with cols[1]:
            st.caption(f"📍 {job.location}")
            if job.experience:
                st.caption(f"🎓 {job.experience}")
        with cols[2]:
            st.markdown(f":{score_color}[**{r.score:.0%}**]")
        with cols[3]:
            if job.skills_matched:
                st.caption(", ".join(job.skills_matched[:3]))
        with cols[4]:
            st.caption(job.freshness or job.platform)
        with cols[5]:
            if job.url:
                st.link_button("Apply", job.url, use_container_width=True)
        with cols[6]:
            if not is_applied:
                if st.button("Mark Applied", key=f"apply_{i}_{job.job_id}", use_container_width=True):
                    save_application(job.job_id, job.company, job.title, job.url, username=username)
                    st.rerun()
            else:
                st.success("Applied", icon="✅")
        st.divider()
