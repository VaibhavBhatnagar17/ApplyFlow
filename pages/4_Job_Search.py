import streamlit as st

from engine.scraper import JobScraper
from engine.state import add_jobs_to_active, load_profile
from engine.profile import TARGET_ROLES, TARGET_LOCATIONS
from engine.guard import require_login, sidebar_user_info, get_username
from engine.matcher import JobMatcher

st.set_page_config(page_title="Job Search | ApplyFlow", page_icon="🔍", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Live Job Search")
st.caption("Real-time extraction across LinkedIn, Indeed, and Naukri with advanced filters.")

profile, prefs = load_profile(username)
if not profile or not prefs:
    st.warning("Please complete onboarding first.")
    st.page_link("pages/1_Onboarding.py", label="Go to Onboarding", icon="📝")
    st.stop()

with st.form("search_form"):
    st.subheader("Search Query")
    q1, q2 = st.columns(2)
    with q1:
        role = st.selectbox(
            "Role",
            TARGET_ROLES,
            index=min(next((i for i, t in enumerate(TARGET_ROLES) if t in prefs.target_titles), 0), len(TARGET_ROLES) - 1),
        )
    with q2:
        location = st.selectbox(
            "Location",
            TARGET_LOCATIONS,
            index=min(next((i for i, l in enumerate(TARGET_LOCATIONS) if l in prefs.target_locations), 0), len(TARGET_LOCATIONS) - 1),
        )

    st.subheader("Live Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        max_jobs = st.slider("How many jobs", min_value=10, max_value=150, value=60, step=10)
    with f2:
        posted_within_days = st.selectbox("Date filter", [1, 3, 7, 14, 30], index=2, format_func=lambda x: f"Last {x} days")
    with f3:
        min_exp = st.number_input("Min experience (years)", min_value=0, max_value=20, value=max(profile.years_experience - 1, 0))
    with f4:
        max_exp = st.number_input("Max experience (years)", min_value=1, max_value=30, value=profile.years_experience + 4)

    platforms = st.multiselect("Platforms", ["linkedin", "indeed", "naukri"], default=["linkedin", "indeed", "naukri"])

    search_btn = st.form_submit_button("Search Live Jobs", type="primary", use_container_width=True)

if search_btn:
    with st.spinner(f"Running live search for '{role}' in '{location}'..."):
        scraper = JobScraper()
        jobs = scraper.search(
            title=role,
            location=location,
            platforms=platforms,
            max_jobs=max_jobs,
            posted_within_days=posted_within_days,
            min_experience=min_exp,
            max_experience=max_exp,
        )

    if not jobs:
        st.warning(
            "No jobs found in this run. Some platforms may throttle scraping. "
            "Try broader filters or run again after a few minutes."
        )
    else:
        matcher = JobMatcher(profile, prefs)
        ranked = matcher.score_jobs(jobs)
        st.session_state["search_results"] = ranked
        with_exp = sum(1 for r in ranked if r.job.experience)
        with_posted = sum(1 for r in ranked if r.job.posted_date)
        st.success(f"Found {len(ranked)} live jobs. Parsed experience for {with_exp}, posted date for {with_posted}.")

if "search_results" in st.session_state:
    ranked = st.session_state["search_results"]
    st.subheader(f"Live Results ({len(ranked)})")

    select_all = st.checkbox("Select all for saving")
    selected_indices = []

    for i, result in enumerate(ranked):
        job = result.job
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
        with col1:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
        with col2:
            st.caption(f"📍 {job.location}")
            st.caption(f"🧠 Match: {result.score:.0%}")
            if result.reasons:
                st.caption(result.reasons[0])
        with col3:
            st.caption(f"Exp: {job.experience or 'n/a'}")
            st.caption(f"Date: {job.posted_date or 'n/a'}")
        with col4:
            st.caption(job.platform)
            if job.url:
                st.link_button("View", job.url, use_container_width=True)
        with col5:
            checked = st.checkbox("Save", key=f"save_{i}", value=select_all)
            if checked:
                selected_indices.append(i)
        st.divider()

    if selected_indices:
        if st.button(f"Save {len(selected_indices)} jobs to dashboard", type="primary", use_container_width=True):
            entries = []
            for idx in selected_indices:
                result = ranked[idx]
                j = result.job
                quality = "excellent" if result.score >= 0.75 else ("good" if result.score >= 0.5 else "stretch")
                entries.append(
                    {
                        "company": j.company,
                        "title": j.title,
                        "location": j.location,
                        "experience": j.experience,
                        "posted": j.posted_date,
                        "url": j.url,
                        "platform": j.platform,
                        "match_quality": quality,
                        "skills_matched": profile.core_skills[:4],
                        "status": "new",
                        "freshness": "active",
                    }
                )
            added = add_jobs_to_active(entries)
            st.success(f"Saved {added} new jobs to your dashboard database.")
            del st.session_state["search_results"]
            st.rerun()
