import streamlit as st
import pandas as pd
import plotly.express as px
from engine.state import load_applications, update_application_status

st.set_page_config(page_title="Tracker | JobPilot", page_icon="📋", layout="wide")
st.title("Application Tracker")
st.caption("Track and manage all your job applications in one place.")

apps = load_applications()

if not apps:
    st.info("No applications tracked yet. Go to the Dashboard and mark jobs as applied.")
    st.page_link("pages/2_Dashboard.py", label="Go to Dashboard", icon="📊")
    st.stop()

STATUSES = ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]

# --- Pipeline Stats ---
status_counts = {}
for a in apps:
    s = a.get("status", "applied")
    status_counts[s] = status_counts.get(s, 0) + 1

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Applied", len(apps))
c2.metric("Screening", status_counts.get("screening", 0))
c3.metric("Interview", status_counts.get("interview", 0))
c4.metric("Offers", status_counts.get("offer", 0))
c5.metric("Rejected", status_counts.get("rejected", 0))

# --- Pipeline Funnel ---
pipeline_data = []
for s in ["applied", "screening", "interview", "offer"]:
    pipeline_data.append({"Stage": s.capitalize(), "Count": status_counts.get(s, 0)})

if any(d["Count"] > 0 for d in pipeline_data):
    df_pipe = pd.DataFrame(pipeline_data)
    fig = px.funnel(df_pipe, x="Count", y="Stage", title="Application Pipeline")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

# --- Application List ---
st.subheader("All Applications")

status_filter = st.selectbox("Filter by status", ["All"] + STATUSES)

filtered_apps = apps if status_filter == "All" else [a for a in apps if a.get("status") == status_filter]

for i, app in enumerate(filtered_apps):
    with st.container():
        cols = st.columns([3, 2, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{app.get('title', 'Unknown')}**")
            st.caption(app.get("company", ""))
        with cols[1]:
            st.caption(f"Applied: {app.get('date_applied', 'N/A')}")
            if app.get("notes"):
                st.caption(f"Notes: {app['notes']}")
        with cols[2]:
            new_status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(app.get("status", "applied")),
                key=f"status_{i}_{app['job_id']}",
            )
        with cols[3]:
            notes = st.text_input("Notes", value=app.get("notes", ""), key=f"notes_{i}_{app['job_id']}")
        with cols[4]:
            if st.button("Update", key=f"update_{i}_{app['job_id']}", use_container_width=True):
                update_application_status(app["job_id"], new_status, notes)
                st.success("Updated!")
                st.rerun()
            if app.get("url"):
                st.link_button("View", app["url"], use_container_width=True)
        st.divider()

# --- Export ---
with st.expander("Export Data"):
    df = pd.DataFrame(apps)
    csv = df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="applications.csv", mime="text/csv")
