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
st.caption("Search across multiple websites with broader role/location combinations.")

profile, prefs = state.load_profile(username)

# --- Google Jobs / SerpAPI config (Option A + B + C) ---
with st.expander("Google Jobs Settings (optional)", expanded=False):
    st.markdown(
        "**Google Jobs** requires a [SerpAPI](https://serpapi.com) key. "
        "Free tier gives 100 searches/month. Without a key, Google Jobs uses "
        "an unreliable HTML fallback. Other platforms work without any key."
    )
    saved_key = state.load_user_serpapi_key(username)
    user_key = st.text_input(
        "Your SerpAPI Key (stored per account, never shared)",
        value=saved_key,
        type="password",
        help="Paste your personal SerpAPI key. It's stored only in your account data.",
    )
    if user_key != saved_key:
        state.save_user_serpapi_key(user_key, username)
        st.success("SerpAPI key saved.")

    remaining = state.google_jobs_remaining(username)
    daily_limit = state.GOOGLE_JOBS_DAILY_LIMIT
    st.info(f"Google Jobs daily limit: **{remaining}** of **{daily_limit}** searches remaining today.")

with st.form("search_form"):
    st.subheader("Search Strategy")
    col1, col2 = st.columns(2)
    with col1:
        default_roles = prefs.target_titles[:4] if prefs and prefs.target_titles else TARGET_ROLES[:4]
        roles = st.multiselect("Roles (select multiple)", TARGET_ROLES, default=default_roles)
    with col2:
        default_locations = prefs.target_locations[:3] if prefs and prefs.target_locations else TARGET_LOCATIONS[:3]
        locations = st.multiselect("Locations (select multiple)", TARGET_LOCATIONS, default=default_locations)

    st.subheader("Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        max_jobs_per_combination = st.slider("Max jobs per role/location", 20, 200, 60, step=20)
    with f2:
        posted_within_days = st.selectbox("Freshness", [1, 3, 7, 14, 30], index=2, format_func=lambda d: f"Last {d} days")
    with f3:
        default_min_exp = max((profile.years_experience - 1), 0) if profile else 0
        min_experience = st.number_input("Min experience (years)", min_value=0, max_value=30, value=default_min_exp)
    with f4:
        default_max_exp = (profile.years_experience + 5) if profile else 10
        max_experience = st.number_input("Max experience (years)", min_value=1, max_value=40, value=default_max_exp)

    default_platforms = ["linkedin", "indeed", "naukri"]
    platforms = st.multiselect(
        "Platforms",
        SUPPORTED_PLATFORMS,
        default=[p for p in default_platforms if p in SUPPORTED_PLATFORMS],
        help="google_jobs requires a SerpAPI key (see settings above).",
    )

    search_btn = st.form_submit_button("Search Live Jobs", type="primary", use_container_width=True)

if search_btn:
    if not roles:
        st.error("Please select at least one role.")
        st.stop()
    if not locations:
        st.error("Please select at least one location.")
        st.stop()
    if not platforms:
        st.error("Please select at least one platform.")
        st.stop()

    use_google = "google_jobs" in platforms
    serpapi_key = state.load_user_serpapi_key(username)
    google_remaining = state.google_jobs_remaining(username)
    google_calls_used = 0

    if use_google and not serpapi_key:
        st.warning("Google Jobs selected but no SerpAPI key configured. It will use unreliable HTML fallback.")

    if use_google and google_remaining <= 0:
        st.warning(f"Google Jobs daily limit reached ({state.GOOGLE_JOBS_DAILY_LIMIT}/day). "
                   "Skipping Google Jobs for this search.")
        platforms = [p for p in platforms if p != "google_jobs"]

    scraper = JobScraper()
    all_jobs = []
    platform_counts = {}
    diagnostics = []

    with st.spinner(f"Searching {len(roles)} role(s) across {len(locations)} location(s)..."):
        for role in roles:
            for location in locations:
                run_platforms = list(platforms)
                if "google_jobs" in run_platforms and google_remaining - google_calls_used <= 0:
                    run_platforms = [p for p in run_platforms if p != "google_jobs"]

                batch = scraper.search(
                    title=role,
                    location=location,
                    platforms=run_platforms,
                    max_jobs=max_jobs_per_combination,
                    posted_within_days=posted_within_days,
                    min_experience=min_experience,
                    max_experience=max_experience,
                    serpapi_key=serpapi_key,
                )
                all_jobs.extend(batch)
                diagnostics.extend(scraper.get_last_run_diagnostics())
                for j in batch:
                    platform_counts[j.platform] = platform_counts.get(j.platform, 0) + 1

                if "google_jobs" in run_platforms:
                    google_calls_used += 1

    if google_calls_used > 0:
        state.increment_google_jobs_usage(username, google_calls_used)

    dedup = {}
    for j in all_jobs:
        dedup[j.job_id] = j
    jobs = list(dedup.values())

    if not jobs:
        st.warning("No results found. Job sites may be blocking automated requests. "
                    "Try different role/location or check back later.")
    else:
        st.success(f"Found {len(jobs)} unique jobs!")
        if platform_counts:
            count_parts = [f"{p}: {platform_counts.get(p, 0)}" for p in platforms]
            st.caption("Platform results -> " + " | ".join(count_parts))
        if google_calls_used > 0:
            new_remaining = state.google_jobs_remaining(username)
            st.caption(f"Google Jobs searches used this run: {google_calls_used} | Remaining today: {new_remaining}")
        st.session_state["search_results"] = jobs
        st.session_state["search_diagnostics"] = diagnostics

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
            st.caption(job.platform)
            st.caption(f"Exp: {job.experience or 'n/a'}")
            st.caption(f"Posted: {job.posted_date or 'n/a'}")
        with col3:
            if job.url:
                st.link_button("View", job.url, use_container_width=True)
        with col4:
            st.caption(job.freshness or "active")
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
                entries.append({
                    "company": j.company, "title": j.title, "location": j.location,
                    "experience": j.experience, "posted": j.posted_date, "url": j.url,
                    "platform": j.platform, "match_quality": "good",
                    "skills_matched": [], "status": "new", "freshness": "active",
                })
            if hasattr(state, "add_jobs_to_active"):
                added = state.add_jobs_to_active(entries)
            elif hasattr(state, "add_jobs_for_user"):
                added = state.add_jobs_for_user(entries, username)
            else:
                added = 0
            st.success(f"Saved {added} new jobs to your database!")
            del st.session_state["search_results"]
            if "search_diagnostics" in st.session_state:
                del st.session_state["search_diagnostics"]
            st.rerun()

if "search_diagnostics" in st.session_state:
    st.subheader("Search Diagnostics")
    diagnostics = st.session_state["search_diagnostics"]
    if diagnostics:
        summary = {}
        for row in diagnostics:
            p = row["platform"]
            if p not in summary:
                summary[p] = {
                    "platform": p,
                    "attempts": 0,
                    "jobs_found_total": 0,
                    "errors": 0,
                    "zero_result_attempts": 0,
                    "latest_note": "",
                }
            summary[p]["attempts"] += 1
            summary[p]["jobs_found_total"] += int(row.get("jobs_found", 0))
            if row.get("status") == "error":
                summary[p]["errors"] += 1
            if int(row.get("jobs_found", 0)) == 0:
                summary[p]["zero_result_attempts"] += 1
            if row.get("note"):
                summary[p]["latest_note"] = row["note"]
        st.dataframe(list(summary.values()), use_container_width=True, hide_index=True)
        with st.expander("Detailed diagnostics"):
            st.dataframe(diagnostics, use_container_width=True, hide_index=True)
