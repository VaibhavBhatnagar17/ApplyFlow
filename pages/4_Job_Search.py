import streamlit as st
from engine.scraper import JobScraper
from engine.state import add_jobs_to_active, load_profile
from engine.profile import TARGET_ROLES, TARGET_LOCATIONS

st.set_page_config(page_title="Job Search | JobPilot", page_icon="🔍", layout="wide")
st.title("Live Job Search")
st.caption("Search across LinkedIn, Indeed, and Naukri for new openings.")

profile, prefs = load_profile()

# --- Search Form ---
with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        role = st.selectbox("Role", TARGET_ROLES,
                            index=0 if not prefs else min(
                                next((i for i, t in enumerate(TARGET_ROLES) if t in prefs.target_titles), 0),
                                len(TARGET_ROLES) - 1
                            ))
    with col2:
        location = st.selectbox("Location", TARGET_LOCATIONS,
                                index=0 if not prefs else min(
                                    next((i for i, l in enumerate(TARGET_LOCATIONS) if l in prefs.target_locations), 0),
                                    len(TARGET_LOCATIONS) - 1
                                ))

    platforms = st.multiselect(
        "Platforms",
        ["linkedin", "indeed", "naukri"],
        default=["linkedin", "indeed", "naukri"],
    )

    search_btn = st.form_submit_button("Search", type="primary", use_container_width=True)

if search_btn:
    with st.spinner(f"Searching for {role} in {location}..."):
        scraper = JobScraper()
        jobs = scraper.search(role, location, platforms)

    if not jobs:
        st.warning("No results found. Job sites may be blocking automated requests. "
                    "Try different role/location or check back later.")
    else:
        st.success(f"Found {len(jobs)} jobs!")

        st.session_state["search_results"] = jobs

if "search_results" in st.session_state:
    jobs = st.session_state["search_results"]

    st.subheader(f"Results ({len(jobs)})")

    select_all = st.checkbox("Select all for saving")

    selected_indices = []
    for i, job in enumerate(jobs):
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
        with col2:
            st.caption(f"📍 {job.location}")
            st.caption(job.platform)
        with col3:
            if job.url:
                st.link_button("View", job.url, use_container_width=True)
        with col4:
            checked = st.checkbox("Save", key=f"save_{i}", value=select_all)
            if checked:
                selected_indices.append(i)

        st.divider()

    if selected_indices:
        if st.button(f"Save {len(selected_indices)} jobs to database", type="primary", use_container_width=True):
            entries = []
            for idx in selected_indices:
                j = jobs[idx]
                entries.append({
                    "company": j.company,
                    "title": j.title,
                    "location": j.location,
                    "experience": "",
                    "posted": j.posted_date,
                    "url": j.url,
                    "platform": j.platform,
                    "match_quality": "good",
                    "skills_matched": [],
                    "status": "new",
                    "freshness": "active",
                })
            added = add_jobs_to_active(entries)
            st.success(f"Saved {added} new jobs to your database!")
            del st.session_state["search_results"]
            st.rerun()
