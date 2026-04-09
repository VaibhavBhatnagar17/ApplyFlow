import streamlit as st

from engine.scraper import JobScraper, SUPPORTED_PLATFORMS
import engine.state as state
from engine.profile import TARGET_ROLES, TARGET_LOCATIONS
from engine.guard import require_login, sidebar_user_info, get_username

st.set_page_config(page_title="Job Search | ApplyFlow", page_icon="🔍", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Live Job Search")
st.caption("Search across multiple websites with role, freshness, and experience filters.")

profile, prefs = state.load_profile(username)

with st.form("search_form"):
    st.subheader("Search Setup")
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Role mode", ["Select multiple roles", "Custom role text"], horizontal=True)
        if mode == "Select multiple roles":
            default_roles = prefs.target_titles[:4] if prefs and prefs.target_titles else TARGET_ROLES[:4]
            roles = st.multiselect("Roles (select multiple)", TARGET_ROLES, default=default_roles)
        else:
            custom = st.text_input("Custom role query", value=(prefs.target_titles[0] if prefs and prefs.target_titles else "Data Engineer"))
            roles = [r.strip() for r in custom.split(",") if r.strip()]

    with col2:
        location = st.selectbox(
            "Location",
            TARGET_LOCATIONS,
            index=0 if not prefs else min(
                next((i for i, l in enumerate(TARGET_LOCATIONS) if l in prefs.target_locations), 0),
                len(TARGET_LOCATIONS) - 1,
            ),
        )

    st.subheader("Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        max_jobs = st.slider("Max jobs", 20, 300, 120, step=20)
    with f2:
        posted_within_days = st.selectbox("Freshness", [1, 3, 7, 14, 30], index=2, format_func=lambda d: f"Last {d} days")
    with f3:
        min_experience = st.number_input("Min experience (years)", min_value=0, max_value=30, value=max((profile.years_experience - 1) if profile else 0, 0))
    with f4:
        max_experience = st.number_input("Max experience (years)", min_value=1, max_value=40, value=((profile.years_experience + 5) if profile else 10))

    platforms = st.multiselect("Websites", SUPPORTED_PLATFORMS, default=["linkedin", "indeed", "naukri", "foundit"])

    search_btn = st.form_submit_button("Search Live Jobs", type="primary", use_container_width=True)

if search_btn:
    if not roles:
        st.error("Please select at least one role.")
        st.stop()

    scraper = JobScraper()
    all_jobs = []

    with st.spinner(f"Searching {len(roles)} role(s) across {len(platforms)} website(s)..."):
        for role in roles:
            batch = scraper.search(
                title=role,
                location=location,
                platforms=platforms,
                max_jobs=max_jobs,
                posted_within_days=posted_within_days,
                min_experience=min_experience,
                max_experience=max_experience,
            )
            all_jobs.extend(batch)

    dedup = {}
    for j in all_jobs:
        dedup[j.job_id] = j
    jobs = list(dedup.values())

    if not jobs:
        st.warning(
            "No results found with current filters. Try broader freshness/experience or fewer websites. "
            "Some websites can rate-limit scraping."
        )
    else:
        st.success(f"Found {len(jobs)} unique jobs for {len(roles)} role(s).")
        st.session_state["search_results"] = jobs

if "search_results" in st.session_state:
    jobs = st.session_state["search_results"]
    st.subheader(f"Results ({len(jobs)})")

    select_all = st.checkbox("Select all for saving")
    selected_indices = []

    for i, job in enumerate(jobs):
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
        with col1:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
        with col2:
            st.caption(f"📍 {job.location}")
            st.caption(f"Exp: {job.experience or 'n/a'}")
            st.caption(f"Posted: {job.posted_date or 'n/a'}")
        with col3:
            st.caption(job.platform)
        with col4:
            if job.url:
                st.link_button("View", job.url, use_container_width=True)
        with col5:
            checked = st.checkbox("Save", key=f"save_{i}", value=select_all)
            if checked:
                selected_indices.append(i)
        st.divider()

    if selected_indices:
        if st.button(f"Save {len(selected_indices)} jobs to database", type="primary", use_container_width=True):
            entries = []
            for idx in selected_indices:
                j = jobs[idx]
                entries.append(
                    {
                        "company": j.company,
                        "title": j.title,
                        "location": j.location,
                        "experience": j.experience,
                        "posted": j.posted_date,
                        "url": j.url,
                        "platform": j.platform,
                        "match_quality": "good",
                        "skills_matched": [],
                        "status": "new",
                        "freshness": "active",
                    }
                )

            if hasattr(state, "add_jobs_to_active"):
                added = state.add_jobs_to_active(entries)
            elif hasattr(state, "add_jobs_for_user"):
                added = state.add_jobs_for_user(entries, username)
            else:
                added = 0

            st.success(f"Saved {added} new jobs to your database!")
            del st.session_state["search_results"]
            st.rerun()
