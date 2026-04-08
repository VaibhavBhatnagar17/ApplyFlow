"""Auth guard and session helpers used by all pages."""

import streamlit as st


def get_username() -> str | None:
    return st.session_state.get("username")


def require_login():
    """Call at the top of any page that needs auth. Stops execution if not logged in."""
    if not get_username():
        st.warning("Please log in to access this page.")
        st.page_link("app.py", label="Go to Login", icon="🔐")
        st.stop()


def sidebar_user_info():
    """Show user info or login prompt in sidebar."""
    username = get_username()
    if username:
        display = st.session_state.get("display_name", username)
        st.sidebar.markdown(f"### ApplyFlow")
        st.sidebar.success(f"**{display}**")
        if st.sidebar.button("Logout", use_container_width=True):
            for key in ["username", "display_name"]:
                st.session_state.pop(key, None)
            st.rerun()
    else:
        st.sidebar.markdown("### ApplyFlow")
        st.sidebar.info("Log in to get started.")
