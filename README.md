# ApplyFlow

**From resume to offer, in one smooth flow.**

ApplyFlow understands your profile, searches for jobs across multiple platforms, scores every opening against your skills, and gives you a beautiful dashboard with cover letters and one-click apply links.

## Two Goals

1. **Understand the applicant** — Upload your resume, tell us your skills, experience, and what you're looking for.
2. **Show the best-fit jobs** — We search LinkedIn, Indeed, Naukri, Google Jobs, and more, then score and rank every job against your profile with auto-generated cover letters.

## Features

- **Smart Profile** — Resume parsing, skill extraction, career goals, and job preferences
- **Multi-Platform Search** — LinkedIn, Indeed, Naukri, Google Jobs, Foundit, Hirist, Wellfound
- **AI Scoring** — TF-IDF + multi-signal matching (title, skills, keywords, company, location)
- **Dashboard** — Card-based layout with match scores, quality badges, skill tags, cover letters, and apply links
- **Cover Letters** — Auto-generated per job based on your profile and matched skills
- **Tracking** — Mark jobs as applied, filter by status, track your pipeline
- **Per-User Storage** — Login system with isolated profile, jobs, and applications

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment (Streamlit Cloud)

1. Push to GitHub
2. Connect repo at [share.streamlit.io](https://share.streamlit.io)
3. Optional: Add secrets in Streamlit Cloud settings:
   - `SERPAPI_API_KEY` — for Google Jobs search
   - `OPENROUTER_API_KEY` or `OPENAI_API_KEY` — for AI insights

## Structure

```
app.py                  # Landing page + login/register
pages/
  1_Profile.py          # Understand the applicant
  2_Find_Jobs.py        # Search & score jobs
  3_Dashboard.py        # Card-based job dashboard
engine/
  profile.py            # Profile & preferences dataclasses
  matcher.py            # TF-IDF + multi-signal job scoring
  cover_letter.py       # Auto cover letter generation
  scraper.py            # Multi-platform job scraper
  state.py              # Per-user JSON persistence
  auth.py               # Login/register
  guard.py              # Session guards
  job_model.py          # JobListing dataclass
  resume_parser.py      # PDF parsing + skill extraction
```
