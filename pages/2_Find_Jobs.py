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

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
.search-hero {
    background: linear-gradient(135deg, #13161d 0%, #1a1f2e 100%);
    border: 1px solid #2a2f3d; border-radius: 16px;
    padding: 24px 28px; margin-bottom: 20px;
}
.search-hero h1 { font-size: 26px; margin-bottom: 4px; }
.search-hero p { color: #8c93a8; font-size: 14px; }
.result-card {
    padding: 12px 18px; margin: 6px 0; border-radius: 10px;
    border: 1px solid #2a2f3d; background: #13161d;
    display: flex; align-items: center; gap: 14px;
    transition: border-color .15s;
}
.result-card:hover { border-color: #3d4a6a; }
.r-score {
    min-width: 42px; height: 42px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 15px; flex-shrink: 0;
}
.r-info { flex: 1; min-width: 0; }
.r-co { font-weight: 700; font-size: 14px; }
.r-ti { font-size: 12px; color: #8c93a8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.r-skills { font-size: 10px; color: #6b7280; margin-top: 2px; }
.r-btn {
    padding: 6px 14px; border-radius: 6px;
    background: linear-gradient(135deg, #5b8def, #3d6ad6); color: #fff;
    font-size: 11px; font-weight: 700; text-decoration: none; white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="search-hero">
    <h1>🔍 Find Jobs</h1>
    <p>We search multiple platforms and score every job against your profile — with auto-generated cover letters.</p>
</div>
""", unsafe_allow_html=True)

# ── Search Configuration ───────────────────────────────────────────
with st.form("search_form"):
    c1, c2 = st.columns(2)
    with c1:
        dr = prefs.target_titles[:5] if prefs.target_titles else TARGET_ROLES[:3]
        roles = st.multiselect("Roles to search", TARGET_ROLES,
            default=[r for r in dr if r in TARGET_ROLES])
    with c2:
        dl = prefs.target_locations[:3] if prefs.target_locations else TARGET_LOCATIONS[:2]
        locations = st.multiselect("Locations", TARGET_LOCATIONS,
            default=[l for l in dl if l in TARGET_LOCATIONS])

    c3, c4, c5 = st.columns(3)
    with c3:
        platforms = st.multiselect("Platforms", SUPPORTED_PLATFORMS,
            default=["linkedin", "indeed", "naukri"],
            help="google_jobs requires a SerpAPI key (see below).")
    with c4:
        freshness = st.selectbox("Posted within", ["7 days", "14 days", "30 days"], index=1)
    with c5:
        e1, e2 = st.columns(2)
        with e1:
            min_exp = st.number_input("Min exp", 0, 40, value=max(profile.years_experience - 2, 0))
        with e2:
            max_exp = st.number_input("Max exp", 0, 40, value=profile.years_experience + 5)

    search_btn = st.form_submit_button("🔍 Search & Score Jobs", type="primary", use_container_width=True)

with st.expander("⚙️ Google Jobs (SerpAPI key)", expanded=False):
    saved_key = load_user_serpapi_key(username)
    user_key = st.text_input("SerpAPI Key", value=saved_key, type="password",
        help="Get a free key at serpapi.com — enables Google Jobs results.")
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
        st.warning("Google Jobs daily limit reached. Skipping.")
        platforms = [p for p in platforms if p != "google_jobs"]
        use_google = False

    scraper = JobScraper()
    all_jobs = []
    google_calls = 0
    total_combos = len(roles) * len(locations)

    progress = st.progress(0, text="Searching…")
    done = 0

    for role in roles:
        for loc in locations:
            run_plats = list(platforms)
            if "google_jobs" in run_plats and google_left - google_calls <= 0:
                run_plats = [p for p in run_plats if p != "google_jobs"]

            batch = scraper.search(
                title=role, location=loc, platforms=run_plats,
                max_jobs=30, posted_within_days=posted_days,
                min_experience=min_exp, max_experience=max_exp,
                serpapi_key=serpapi_key,
            )
            all_jobs.extend(batch)
            if "google_jobs" in run_plats:
                google_calls += 1
            done += 1
            progress.progress(done / total_combos, text=f"Searched {role} in {loc}…")

    progress.empty()

    if google_calls > 0:
        increment_google_jobs_usage(username, google_calls)

    seen_ids = set()
    unique = []
    for j in all_jobs:
        if j.job_id not in seen_ids:
            seen_ids.add(j.job_id)
            unique.append(j)

    if not unique:
        st.warning("No jobs found. Try broader roles or different locations.")
        st.stop()

    matcher = JobMatcher(profile, prefs)
    results = matcher.score_jobs(unique)
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

    # ── Results summary ────────────────────────────────────────────
    exc = sum(1 for e in entries if e["match_quality"] == "excellent")
    good = sum(1 for e in entries if e["match_quality"] == "good")
    stretch = sum(1 for e in entries if e["match_quality"] == "stretch")

    st.markdown(f"""
    <div style="background:#13161d;border:1px solid #2a2f3d;border-radius:12px;padding:18px 24px;margin:16px 0">
        <div style="font-size:18px;font-weight:700;margin-bottom:8px">
            Found {len(entries)} matching jobs — added {added} new
        </div>
        <div style="display:flex;gap:16px;font-size:13px">
            <span style="color:#22c984;font-weight:700">{exc} Excellent</span>
            <span style="color:#5b8def;font-weight:700">{good} Good</span>
            <span style="color:#f0b429;font-weight:700">{stretch} Stretch</span>
            <span style="color:#8c93a8">Total in dashboard: {total_saved}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Preview top matches ────────────────────────────────────────
    st.markdown("### Top Matches")
    for e in entries[:15]:
        score = e["match_score"]
        q = e["match_quality"]
        color = "#22c984" if q == "excellent" else ("#5b8def" if q == "good" else "#f0b429")
        bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},.12)"
        skills_str = ", ".join(e["skills_matched"][:6]) if e["skills_matched"] else "—"

        st.markdown(f"""
        <div class="result-card">
            <div class="r-score" style="background:{bg};color:{color}">{score}</div>
            <div class="r-info">
                <div class="r-co">{e['company']}</div>
                <div class="r-ti">{e['title']}</div>
                <div class="r-skills">{skills_str} · {e['platform']} · {e['location']}</div>
            </div>
            <a href="{e['url']}" target="_blank" class="r-btn">Apply ↗</a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("pages/3_Dashboard.py", label="Open Full Dashboard →", icon="📊")
