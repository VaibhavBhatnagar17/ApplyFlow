# ApplyFlow

**Your AI-powered job search co-pilot — from resume to offer, in one smooth flow.**

Stop juggling spreadsheets, bookmarks, and 15 open tabs. ApplyFlow puts your entire job search into a single intelligent dashboard: upload your resume, tell it what you're looking for, and it scores every opening against your profile, writes tailored cover letters, and tracks every application from "applied" to "offer."

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- **Smart Resume Parsing** — Upload a PDF and ApplyFlow auto-extracts your skills, experience, and contact info
- **Intelligent Job Matching** — 146+ curated listings scored against your profile using TF-IDF cosine similarity and multi-signal matching
- **Company Intelligence** — Browse 250+ companies with tier rankings, career page links, India office info, and "why you're a fit" rationale
- **Live Job Search** — Search LinkedIn, Indeed, and Naukri directly from the app and save results to your dashboard
- **One-Click Cover Letters** — Generate tailored, achievement-backed cover letters for any job in your database
- **Application Tracker** — Pipeline funnel from Applied → Screening → Interview → Offer with status updates and CSV export

## How It Works

```
Resume + Preferences → Profile Engine → Job Matcher → Scored Dashboard
                                                   ↓
                                        Cover Letter Generator
                                                   ↓
                                        Application Tracker
```

## Deploy Free

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, pick `app.py`, deploy — live in 2 minutes

## Tech Stack

- **Python** — the only language you need
- **Streamlit** — instant web UI from Python scripts
- **scikit-learn** — TF-IDF matching engine
- **pdfplumber** — resume PDF parsing
- **Plotly** — interactive charts and funnel visualizations

## License

MIT
