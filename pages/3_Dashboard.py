"""Dashboard — Your best-fit jobs, scored, filterable, with cover letters and apply links."""

import streamlit as st

st.set_page_config(page_title="Dashboard | ApplyFlow", page_icon="📊", layout="wide")

from engine.guard import require_login, get_username, sidebar_user_info
from engine.state import (
    load_profile,
    load_user_saved_jobs,
    save_user_saved_jobs,
    load_applications,
    save_application,
)

sidebar_user_info()
require_login()
username = get_username()

profile, prefs = load_profile(username)
if not profile or not profile.is_complete():
    st.warning("Complete your profile first.")
    st.page_link("pages/1_Profile.py", label="Set Up Profile", icon="👤")
    st.stop()

jobs = load_user_saved_jobs(username)
apps = load_applications(username)
applied_ids = {f"{a['company'].lower()}|{a['title'].lower()}" for a in apps}

if not jobs:
    st.markdown("# 📊 Dashboard")
    st.info("No jobs in your dashboard yet. Search for jobs first!")
    st.page_link("pages/2_Find_Jobs.py", label="Find Jobs", icon="🔍")
    st.stop()

# ── Mark jobs that are already applied ─────────────────────────────
for j in jobs:
    key = f"{j.get('company','').lower()}|{j.get('title','').lower()}"
    if key in applied_ids:
        j["status"] = "applied"

# ── Sort by score ──────────────────────────────────────────────────
jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)

# ── Stats ──────────────────────────────────────────────────────────
total = len(jobs)
excellent = sum(1 for j in jobs if j.get("match_quality") == "excellent")
good = sum(1 for j in jobs if j.get("match_quality") == "good")
stretch = sum(1 for j in jobs if j.get("match_quality") == "stretch")
applied_count = sum(1 for j in jobs if j.get("status") == "applied")

# ── Full-page custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
:root {
    --green: #22c984;
    --blue: #5b8def;
    --yellow: #f0b429;
    --orange: #e8763a;
    --purple: #a78bfa;
    --bg: #0f1117;
    --card-bg: #1a1d27;
    --card-border: #2a2d3a;
    --text-primary: #e6e8f0;
    --text-secondary: #9ca3af;
    --text-tertiary: #6b7280;
}
.stats-row { display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; }
.stat-box { padding:14px 20px; border-radius:12px; border:1px solid var(--card-border);
  background:var(--card-bg); text-align:center; min-width:90px; flex:1; }
.stat-n { font-size:26px; font-weight:900; }
.stat-l { font-size:11px; color:var(--text-tertiary); text-transform:uppercase;
  letter-spacing:.5px; margin-top:2px; }

.toolbar { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
.fb { padding:6px 14px; border-radius:6px; border:1px solid var(--card-border);
  background:transparent; color:var(--text-secondary); font-size:11px; font-weight:700;
  cursor:pointer; text-transform:uppercase; letter-spacing:.4px; }
.fb.on { background:rgba(91,141,239,.1); color:var(--blue); border-color:var(--blue); }

.jc { border:1px solid var(--card-border); border-radius:12px; background:var(--card-bg);
  margin-bottom:8px; overflow:hidden; transition:border-color .15s; }
.jc:hover { border-color: var(--blue); }
.jc-top { display:flex; align-items:center; padding:14px 18px; gap:14px; }
.jc-score { min-width:44px; height:44px; border-radius:10px; display:flex;
  align-items:center; justify-content:center; font-size:16px; font-weight:900; flex-shrink:0; }
.jc-score.high { background:rgba(34,201,132,.12); color:var(--green); }
.jc-score.mid { background:rgba(91,141,239,.12); color:var(--blue); }
.jc-score.low { background:rgba(240,180,41,.12); color:var(--yellow); }
.jc-info { flex:1; min-width:0; }
.jc-co { font-size:14px; font-weight:700; color:var(--text-primary); }
.jc-ti { font-size:12px; color:var(--text-secondary); white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }
.jc-meta { display:flex; gap:5px; margin-top:4px; flex-wrap:wrap; }
.tag { padding:2px 7px; border-radius:4px; font-size:10px; font-weight:700;
  text-transform:uppercase; letter-spacing:.3px; }
.tag.exc { background:rgba(34,201,132,.1); color:var(--green); }
.tag.good { background:rgba(91,141,239,.1); color:var(--blue); }
.tag.str { background:rgba(240,180,41,.1); color:var(--yellow); }
.tag.meta { background:#1f2233; color:var(--text-secondary); }
.tag.hot { background:rgba(232,118,58,.1); color:var(--orange); }
.tag.sk { background:#1f2233; color:var(--text-secondary); }
.tag.skh { background:rgba(34,201,132,.08); color:var(--green); }

.btn-apply { padding:7px 14px; border-radius:7px; border:none; font-size:11px;
  font-weight:700; cursor:pointer; text-decoration:none; white-space:nowrap;
  background:linear-gradient(135deg,var(--blue),#3d6ad6); color:#fff;
  box-shadow:0 2px 6px rgba(91,141,239,.2); }
.btn-apply:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(91,141,239,.3); }
.btn-done { padding:7px 14px; border-radius:7px; border:none; font-size:11px;
  font-weight:700; background:rgba(167,139,250,.1); color:var(--purple); cursor:default; }

.panel { padding:12px 18px 16px; border-top:1px solid var(--card-border); }
.panel h4 { font-size:11px; text-transform:uppercase; letter-spacing:.8px;
  color:var(--text-tertiary); margin:12px 0 6px; font-weight:700; }
.cl-box { background:#12141c; border:1px solid var(--card-border); border-radius:8px;
  padding:14px; font-size:12px; color:var(--text-secondary); white-space:pre-wrap;
  line-height:1.6; max-height:280px; overflow-y:auto; }
.url-box { background:#12141c; border:1px solid var(--card-border); border-radius:6px;
  padding:8px 12px; }
.url-box a { color:var(--blue); word-break:break-all; font-size:11px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
  <div>
    <h1 style="margin:0;font-size:28px">📊 Dashboard</h1>
    <div style="color:#9ca3af;font-size:13px">Click any card to expand details, cover letter, and apply link.</div>
  </div>
  <div style="padding:8px 18px;border-radius:20px;background:rgba(91,141,239,.1);
    color:#5b8def;font-weight:800;font-size:13px">{total} Jobs Ready</div>
</div>
""", unsafe_allow_html=True)

# ── Stats Row ──────────────────────────────────────────────────────
st.markdown(f"""
<div class="stats-row">
  <div class="stat-box"><div class="stat-n" style="color:var(--green)">{excellent}</div><div class="stat-l">Excellent</div></div>
  <div class="stat-box"><div class="stat-n" style="color:var(--blue)">{good}</div><div class="stat-l">Good</div></div>
  <div class="stat-box"><div class="stat-n" style="color:var(--yellow)">{stretch}</div><div class="stat-l">Stretch</div></div>
  <div class="stat-box"><div class="stat-n" style="color:var(--purple)">{applied_count}</div><div class="stat-l">Applied</div></div>
</div>
""", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────
fcol1, fcol2, fcol3 = st.columns([2, 2, 3])
with fcol1:
    quality_filter = st.selectbox(
        "Match Quality", ["All", "Excellent", "Good", "Stretch"],
        label_visibility="collapsed",
    )
with fcol2:
    status_filter = st.selectbox(
        "Status", ["All Status", "New", "Applied"],
        label_visibility="collapsed",
    )
with fcol3:
    search_text = st.text_input(
        "Search",
        placeholder="Search company, title, skill…",
        label_visibility="collapsed",
    )

# ── Apply filters ─────────────────────────────────────────────────
filtered = jobs
if quality_filter != "All":
    filtered = [j for j in filtered if j.get("match_quality", "").lower() == quality_filter.lower()]
if status_filter == "New":
    filtered = [j for j in filtered if j.get("status", "new") != "applied"]
elif status_filter == "Applied":
    filtered = [j for j in filtered if j.get("status") == "applied"]
if search_text:
    q = search_text.lower()
    filtered = [j for j in filtered if q in " ".join([
        j.get("company", ""), j.get("title", ""), j.get("location", ""),
        " ".join(j.get("skills_matched", [])),
    ]).lower()]

st.caption(f"Showing **{len(filtered)}** of {total} jobs")

# ── Job Cards ──────────────────────────────────────────────────────
HOT_SKILLS = {"LLM", "RAG", "Agents", "GenAI", "PyTorch", "NLP", "Deep Learning",
              "Computer Vision", "YOLO", "LangChain", "Kubernetes", "MLOps"}

for idx, j in enumerate(filtered):
    score = j.get("match_score", 0)
    quality = j.get("match_quality", "good")
    company = j.get("company", "")
    title = j.get("title", "")
    location = j.get("location", "")
    experience = j.get("experience", "")
    url = j.get("url", "")
    platform = j.get("platform", "")
    status = j.get("status", "new")
    freshness = j.get("freshness", "")
    skills = j.get("skills_matched", [])
    cover = j.get("cover_letter", "")

    score_class = "high" if quality == "excellent" else ("mid" if quality == "good" else "low")
    quality_tag = "exc" if quality == "excellent" else ("good" if quality == "good" else "str")
    is_applied = status == "applied"

    is_hot = freshness and any(w in freshness.lower() for w in ["hour", "just", "today", "minute"])

    # Build skills tags HTML
    skills_html = ""
    for s in skills[:8]:
        cls = "skh" if s in HOT_SKILLS else "sk"
        skills_html += f'<span class="tag {cls}">{s}</span>'

    # Card header
    card_html = f"""
    <div class="jc-top">
      <div class="jc-score {score_class}">{score}</div>
      <div class="jc-info">
        <div class="jc-co">{company}</div>
        <div class="jc-ti">{title}</div>
        <div class="jc-meta">
          <span class="tag {quality_tag}">{quality}</span>
          <span class="tag meta">{location}</span>
          {'<span class="tag meta">' + experience + '</span>' if experience else ''}
          {'<span class="tag ' + ('hot' if is_hot else 'meta') + '">' + freshness + '</span>' if freshness else ''}
          <span class="tag meta">{platform}</span>
        </div>
      </div>
    </div>
    """

    with st.expander(f"**{score}** — {company} · {title}", expanded=False):
        st.markdown(f'<div class="jc">{card_html}</div>', unsafe_allow_html=True)

        # Skills
        if skills:
            st.markdown(f'<h4 style="font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#6b7280;font-weight:700;margin:8px 0 4px">Skills Matched</h4><div class="jc-meta">{skills_html}</div>', unsafe_allow_html=True)

        # Cover Letter
        if cover:
            st.markdown('<h4 style="font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#6b7280;font-weight:700;margin:12px 0 4px">Cover Letter</h4>', unsafe_allow_html=True)
            st.code(cover, language=None)
            st.download_button(
                "Download Cover Letter",
                cover,
                file_name=f"cover_letter_{company.replace(' ', '_')}.txt",
                key=f"dl_{idx}",
            )

        # Apply URL
        if url:
            st.markdown(f'<div class="url-box"><a href="{url}" target="_blank">{url}</a></div>', unsafe_allow_html=True)

        # Action buttons
        col_apply, col_mark = st.columns([1, 1])
        with col_apply:
            if url:
                st.link_button("Apply ↗", url, type="primary", use_container_width=True)
        with col_mark:
            if is_applied:
                st.success("✓ Applied")
            else:
                if st.button("Mark as Applied", key=f"mark_{idx}", use_container_width=True):
                    save_application(
                        job_id=f"{company}|{title}",
                        company=company,
                        title=title,
                        url=url,
                        status="applied",
                        username=username,
                    )
                    j["status"] = "applied"
                    save_user_saved_jobs(jobs, username)
                    st.rerun()
