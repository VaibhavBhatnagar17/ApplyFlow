import streamlit as st

from engine.scraper import JobScraper
from engine.state import add_jobs_to_active, load_profile
from engine.profile import TARGET_ROLES, TARGET_LOCATIONS
from engine.guard import require_login, sidebar_user_info, get_username
from engine.matcher import JobMatcher
from engine.llm import OpenSourceInsights

st.set_page_config(page_title="Job Search | ApplyFlow", page_icon="🔍", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Live Job Search")
st.caption("Search across platforms with optional open-source LLM query assistant.")

profile, prefs = load_profile(username)

llm_model = st.sidebar.text_input("LLM model", value="llama3.1:8b")
llm = OpenSourceInsights(model=llm_model)

st.subheader("AI Query Assistant")
ai_col1, ai_col2 = st.columns([1, 3])
with ai_col1:
    use_ai = st.checkbox("Use AI query expansion", value=False)
with ai_col2:
    if llm.is_available():
        st.caption("Open-source LLM detected (Ollama). AI query suggestions enabled.")
    else:
        st.caption("LLM not running locally. App will use standard search queries.")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        role_mode = st.radio("Role input", ["Preset", "Custom"], horizontal=True)
        if role_mode == "Preset":
            role = st.selectbox(
                "Role",
                TARGET_ROLES,
                index=0 if not prefs else min(
                    next((i for i, t in enumerate(TARGET_ROLES) if t in prefs.target_titles), 0),
                    len(TARGET_ROLES) - 1,
                ),
            )
        else:
            role = st.text_input("Custom role", value=(prefs.target_titles[0] if prefs and prefs.target_titles else "Data Engineer"))
    with col2:
        location = st.selectbox(
            "Location",
            TARGET_LOCATIONS,
            index=0 if not prefs else min(
                next((i for i, l in enumerate(TARGET_LOCATIONS) if l in prefs.target_locations), 0),
                len(TARGET_LOCATIONS) - 1,
            ),
        )

    platforms = st.multiselect("Platforms", ["linkedin", "indeed", "naukri"], default=["linkedin", "indeed", "naukri"])
    max_jobs = st.slider("How many jobs", min_value=20, max_value=150, value=60, step=10)
    posted_within_days = st.selectbox("Date window", [1, 3, 7, 14, 30], index=2, format_func=lambda d: f"Last {d} days")
    min_exp = st.number_input("Min experience", min_value=0, max_value=30, value=max((profile.years_experience - 1) if profile else 0, 0))
    max_exp = st.number_input("Max experience", min_value=1, max_value=40, value=((profile.years_experience + 4) if profile else 8))

    search_btn = st.form_submit_button("Search", type="primary", use_container_width=True)

if search_btn:
    queries = [role]
    if use_ai and llm.is_available() and profile and prefs:
        queries = llm.suggest_role_queries(profile, prefs, role, location)
        st.info("AI query suggestions: " + " | ".join(queries[:5]))

    scraper = JobScraper()
    all_jobs = []
    with st.spinner(f"Searching live jobs for {role} in {location}..."):
        for q in queries[:3]:
            batch = scraper.search(
                title=q,
                location=location,
                platforms=platforms,
                max_jobs=max_jobs,
                posted_within_days=posted_within_days,
                min_experience=min_exp,
                max_experience=max_exp,
            )
            all_jobs.extend(batch)

    dedup = {}
    for j in all_jobs:
        dedup[j.job_id] = j
    jobs = list(dedup.values())

    if not jobs:
        st.warning("No results found. Sources might be rate-limited; retry with broader filters.")
    else:
        matcher = JobMatcher(profile, prefs)
        ranked = matcher.score_jobs(jobs)
        st.session_state["search_results"] = ranked
        st.success(f"Found {len(ranked)} jobs from {len(queries[:3])} query passes.")

        st.markdown(llm.search_run_insights(role, location, ranked))

if "search_results" in st.session_state:
    ranked = st.session_state["search_results"]
    st.subheader(f"Results ({len(ranked)})")

    select_all = st.checkbox("Select all for saving")
    selected_indices = []

    for i, result in enumerate(ranked):
        job = result.job
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.markdown(f"**{job.title}**")
            st.caption(job.company)
            if result.reasons:
                st.caption(result.reasons[0])
        with col2:
            st.caption(f"📍 {job.location}")
            st.caption(f"{job.platform} | Match {int(result.score * 100)}%")
            if job.experience:
                st.caption(f"Exp: {job.experience}")
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
                res = ranked[idx]
                j = res.job
                quality = "excellent" if res.score >= 0.75 else ("good" if res.score >= 0.5 else "stretch")
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
                        "skills_matched": profile.core_skills[:5] if profile else [],
                        "status": "new",
                        "freshness": "active",
                    }
                )
            added = add_jobs_to_active(entries)
            st.success(f"Saved {added} new jobs to your database.")
            del st.session_state["search_results"]
            st.rerun()
