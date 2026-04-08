import streamlit as st
import pandas as pd
import plotly.express as px

from engine.guard import require_login, sidebar_user_info, get_username
from engine.state import load_user_saved_jobs, load_applications, update_application_status

st.set_page_config(page_title="Saved & Applied | ApplyFlow", page_icon="📁", layout="wide")
sidebar_user_info()
require_login()

username = get_username()
st.title("Saved & Applied Jobs")
st.caption("Unified view of everything you saved and everything you applied to.")

saved = load_user_saved_jobs(username)
apps = load_applications(username)
app_ids = {a["job_id"] for a in apps}

c1, c2, c3 = st.columns(3)
c1.metric("Saved Jobs", len(saved))
c2.metric("Applied Jobs", len(apps))
c3.metric("Not Applied Yet", max(len(saved) - len(apps), 0))

if apps:
    status_counts = {}
    for a in apps:
        s = a.get("status", "applied")
        status_counts[s] = status_counts.get(s, 0) + 1
    df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
    fig = px.bar(df_status, x="Status", y="Count", title="Application Status Breakdown")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Saved Openings")
if not saved:
    st.info("No saved jobs yet. Use Job Search to save live openings.")
else:
    search = st.text_input("Search saved jobs")
    filtered_saved = saved
    if search:
        s = search.lower()
        filtered_saved = [j for j in saved if s in j.get("title", "").lower() or s in j.get("company", "").lower()]

    for i, j in enumerate(filtered_saved):
        job_id = f"{j.get('company','')}|{j.get('title','')}|{j.get('url','')}".lower()
        is_applied = any((a.get("company", "").lower() == j.get("company", "").lower() and a.get("title", "").lower() == j.get("title", "").lower()) for a in apps)
        cols = st.columns([3, 2, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{j.get('title','')}**")
            st.caption(j.get("company", ""))
        with cols[1]:
            st.caption(f"📍 {j.get('location','')}")
            st.caption(f"Exp: {j.get('experience','n/a')}")
        with cols[2]:
            st.caption(j.get("match_quality", ""))
            st.caption(j.get("platform", ""))
        with cols[3]:
            if j.get("url"):
                st.link_button("Open", j.get("url"), use_container_width=True)
        with cols[4]:
            st.success("Applied") if is_applied else st.info("Saved")
        st.divider()

st.subheader("Applied Timeline")
if not apps:
    st.info("No applications yet.")
else:
    statuses = ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]
    for i, app in enumerate(apps):
        cols = st.columns([3, 2, 1, 1])
        with cols[0]:
            st.markdown(f"**{app.get('title','')}**")
            st.caption(app.get("company", ""))
        with cols[1]:
            st.caption(f"Applied: {app.get('date_applied','n/a')}")
            st.caption(app.get("notes", ""))
        with cols[2]:
            status = st.selectbox("Status", statuses, index=statuses.index(app.get("status", "applied")), key=f"status_{i}")
        with cols[3]:
            if st.button("Update", key=f"update_{i}", use_container_width=True):
                update_application_status(app.get("job_id", ""), status, app.get("notes", ""), username=username)
                st.rerun()
            if app.get("url"):
                st.link_button("View", app["url"], use_container_width=True)
        st.divider()
