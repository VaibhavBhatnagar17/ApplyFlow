"""Find Jobs — Search across platforms and auto-score against your profile."""

import streamlit as st
from dataclasses import asdict

st.set_page_config(page_title="Find Jobs | ApplyFlow", page_icon="🔍", layout="wide")

from engine.guard import require_login, get_username, sidebar_user_info
from engine.profile import TARGET_ROLES, TARGET_LOCATIONS
from engine.scraper import JobScraper, SUPPORTED_PLATFORMS
from engine.matcher import JobMatcher
from engine.cover_letter import CoverLetterGenerator
from engine.state import (
    load_profile,
    load_user_saved_jobs,
    add_jobs_for_user,
    load_user_serpapi_key,
    save_user_serpapi_key,
    google_jobs_remaining,
    increment_google_jobs_usage,
    GOOGLE_JOBS_DAILY_LIMIT,
)

sidebar_user_info()
require_login()
username = get_username()

profile, prefs = load_profile(username)
if not profile or not profile.is_complete():
    st.warning("Please complete your profile first so we can score jobs for you.")
    st.page_link("pages/1_Profile.py", label="Set Up Profile", icon="👤")
    st.stop()

st.markdown("# 🔍 Find Jobs")
st.caption("We search multiple platforms and score every job against your profile.")

# ── Search Configuration ───────────────────────────────────────────
with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        default_roles = prefs.target_titles[:5] if prefs.target_titles else TARGET_ROLES[:3]
        roles = st.multiselect(
            "Roles to search",
            TARGET_ROLES,
            default=[r for r in default_roles if r in TARGET_ROLES],
        )
    with col2:
        default_locs = prefs.target_locations[:3] if prefs.target_locations else TARGET_LOCATIONS[:2]
        locations = st.multiselect(
            "Locations",
            TARGET_LOCATIONS,
            default=[l for l in default_locs if l in TARGET_LOCATIONS],
        )

    col3, col4, col5 = st.columns(3)
    with col3:
        platforms = st.multiselect(
            "Platforms",
            SUPPORTED_PLATFORMS,
            default=["linkedin", "indeed", "naukri"],
            help="google_jobs requires a SerpAPI key (see below).",
        )
    with col4:
        freshness = st.selectbox("Posted within", ["7 days", "14 days", "30 days"], index=1)
    with col5:
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            min_exp = st.number_input("Min exp (yrs)", 0, 40, value=max(profile.years_experience - 2, 0))
        with exp_col2:
            max_exp = st.number_input("Max exp (yrs)", 0, 40, value=profile.years_experience + 5)

    search_btn = st.form_submit_button("Search & Score Jobs", type="primary", use_container_width=True)

with st.expander("Google Jobs (SerpAPI key)", expanded=False):
    saved_key = load_user_serpapi_key(username)
    user_key = st.text_input(
        "SerpAPI Key",
        value=saved_key,
        type="password",
        help="Get a free key at serpapi.com — enables Google Jobs results.",
    )
    if user_key != saved_key:
        save_user_serpapi_key(user_key, username)
        st.success("Key saved.")
    remaining = google_jobs_remaining(username)
    st.caption(f"Google Jobs: **{remaining}** / **{GOOGLE_JOBS_DAILY_LIMIT}** daily searches remaining.")

# ── Run Search ─────────────────────────────────────────────────────
if search_btn:
    if not roles:
        st.error("Select at least one role.")
        st.stop()
    if not locations:
        st.error("Select at least one location.")
        st.stop()
    if not platforms:
        st.error("Select at least one platform.")
        st.stop()

    posted_days = int(freshness.split()[0])
    serpapi_key = load_user_serpapi_key(username)

    use_google = "google_jobs" in platforms
    google_left = google_jobs_remaining(username)
    if use_google and google_left <= 0:
        st.warning("Google Jobs daily limit reached. Skipping Google Jobs.")
        platforms = [p for p in platforms if p != "google_jobs"]
        use_google = False

    scraper = JobScraper()
    all_jobs = []
    google_calls = 0

    progress = st.progress(0, text="Searching…")
    total = len(roles) * len(locations)
    done = 0

    for role in roles:
        for loc in locations:
            run_platforms = list(platforms)
            if "google_jobs" in run_platforms and google_left - google_calls <= 0:
                run_platforms = [p for p in run_platforms if p != "google_jobs"]

            batch = scraper.search(
                title=role,
                location=loc,
                platforms=run_platforms,
                max_jobs=30,
                posted_within_days=posted_days,
                min_experience=min_exp,
                max_experience=max_exp,
                serpapi_key=serpapi_key,
            )
            all_jobs.extend(batch)
            if "google_jobs" in run_platforms:
                google_calls += 1

            done += 1
            progress.progress(done / total, text=f"Searched {role} in {loc}…")

    progress.empty()

    if google_calls > 0:
        increment_google_jobs_usage(username, google_calls)

    # Deduplicate
    seen_ids = set()
    unique = []
    for j in all_jobs:
        if j.job_id not in seen_ids:
            seen_ids.add(j.job_id)
            unique.append(j)

    if not unique:
        st.warning("No jobs found. Try broader roles or different locations.")
        st.stop()

    # Score against profile
    matcher = JobMatcher(profile, prefs)
    results = matcher.score_jobs(unique)

    # Generate cover letters and determine match quality
    cover_gen = CoverLetterGenerator(profile)
    entries = []
    for r in results:
        if r.score < prefs.min_match_score:
            continue

        quality = "excellent" if r.score >= 0.75 else ("good" if r.score >= 0.50 else "stretch")
        cover = cover_gen.generate(r.job)

        matched_skills = [s for s in profile.core_skills
                          if s.lower() in f"{r.job.title} {r.job.description}".lower()]

        entries.append({
            "company": r.job.company,
            "title": r.job.title,
            "location": r.job.location,
            "experience": r.job.experience,
            "url": r.job.url,
            "platform": r.job.platform,
            "match_quality": quality,
            "match_score": round(r.score * 100),
            "skills_matched": matched_skills,
            "status": "new",
            "freshness": r.job.posted_date or r.job.freshness or "",
            "cover_letter": cover,
            "description": r.job.description[:500],
        })

    added = add_jobs_for_user(entries, username)
    total_saved = len(load_user_saved_jobs(username))

    st.success(f"Found **{len(entries)}** matching jobs. Added **{added}** new to your dashboard (total: {total_saved}).")

    # Quick preview
    st.markdown("### Top Matches")
    for e in entries[:10]:
        score = e["match_score"]
        q = e["match_quality"]
        color = "#22c984" if q == "excellent" else ("#5b8def" if q == "good" else "#f0b429")
        skills_str = ", ".join(e["skills_matched"][:6]) if e["skills_matched"] else "—"
        st.markdown(
            f"<div style='padding:10px 16px;margin:4px 0;border-radius:8px;border:1px solid #333;"
            f"display:flex;align-items:center;gap:12px'>"
            f"<span style='min-width:40px;height:40px;border-radius:8px;display:flex;"
            f"align-items:center;justify-content:center;font-weight:900;font-size:15px;"
            f"background:rgba({','.join(str(int(color[i:i+2],16)) for i in (1,3,5))},.12);"
            f"color:{color}'>{score}</span>"
            f"<div style='flex:1;min-width:0'>"
            f"<div style='font-weight:700;font-size:14px'>{e['company']}</div>"
            f"<div style='font-size:12px;color:#999;overflow:hidden;text-overflow:ellipsis;"
            f"white-space:nowrap'>{e['title']}</div>"
            f"<div style='font-size:10px;color:#777;margin-top:2px'>{skills_str}</div>"
            f"</div>"
            f"<a href='{e['url']}' target='_blank' style='padding:6px 14px;border-radius:6px;"
            f"background:linear-gradient(135deg,#5b8def,#3d6ad6);color:#fff;font-size:11px;"
            f"font-weight:700;text-decoration:none'>Apply ↗</a>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.page_link("pages/3_Dashboard.py", label="Open Full Dashboard →", icon="📊")
