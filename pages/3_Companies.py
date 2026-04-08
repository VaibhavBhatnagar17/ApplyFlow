import streamlit as st
import pandas as pd
from engine.company_db import load_companies, filter_companies, get_industries, get_tier_label
from engine.guard import require_login, sidebar_user_info

st.set_page_config(page_title="Companies | ApplyFlow", page_icon="🏢", layout="wide")
sidebar_user_info()
require_login()

st.title("Company Database")
st.caption("Browse 250+ companies hiring for AI/ML/Data Science roles.")

companies = load_companies()
if not companies:
    st.error("No company data found. Add company_research.json to data/.")
    st.stop()

st.sidebar.subheader("Filters")

tier_options = {"All": None, "Dream (Tier 1)": 1, "Strong Fit (Tier 2)": 2, "Good Match (Tier 3)": 3}
tier_choice = st.sidebar.radio("Tier", list(tier_options.keys()))
tier_val = tier_options[tier_choice]

industries = get_industries(companies)
industry_choice = st.sidebar.selectbox("Industry", ["All"] + industries)

location_choice = st.sidebar.text_input("Location filter", placeholder="e.g., Bangalore")
search = st.sidebar.text_input("Search", placeholder="Company name, industry...")

filtered = filter_companies(
    companies, tier=tier_val,
    industry=industry_choice if industry_choice != "All" else None,
    location=location_choice or None,
    search=search or None,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Companies", len(companies))
c2.metric("Filtered", len(filtered))
c3.metric("Dream Tier", sum(1 for c in companies if c.get("tier") == 1))
c4.metric("With India Office", sum(1 for c in companies if c.get("india_offices")))

st.subheader(f"Companies ({len(filtered)})")

rows = []
for c in filtered:
    offices = ", ".join(c.get("india_offices", [])) if c.get("india_offices") else "—"
    fit_reasons = c.get("why_good_fit", [])
    fit_text = "; ".join(fit_reasons[:2]) if fit_reasons else "—"
    rows.append({
        "Company": c.get("name", ""),
        "Tier": get_tier_label(c.get("tier", 3)),
        "Industry": c.get("industry", ""),
        "HQ": c.get("hq", ""),
        "India Offices": offices,
        "Remote": "Yes" if c.get("remote_friendly") else "No",
        "Why Good Fit": fit_text,
        "Careers URL": c.get("careers_url", ""),
    })

if rows:
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        column_config={
            "Careers URL": st.column_config.LinkColumn("Careers", display_text="Open"),
            "Company": st.column_config.TextColumn(width="medium"),
            "Why Good Fit": st.column_config.TextColumn(width="large"),
        },
        hide_index=True, use_container_width=True, height=600,
    )
else:
    st.info("No companies match your filters.")

with st.expander("Industry Breakdown"):
    industry_counts = {}
    for c in companies:
        ind = c.get("industry", "Other")
        industry_counts[ind] = industry_counts.get(ind, 0) + 1
    for ind, count in sorted(industry_counts.items(), key=lambda x: -x[1]):
        st.write(f"**{ind}**: {count} companies")
