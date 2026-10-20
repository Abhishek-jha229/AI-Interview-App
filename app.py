"""
Main entrypoint & router for AI Interview Simulator.
Configures dynamic multi-page navigation via st.navigation() and st.Page().
Conditionally exposes the Settings page ONLY to authenticated owners.
"""

import streamlit as st

from core.database import create_tables, get_dashboard_stats
from core.settings import load_settings
from core.theme import inject_custom_css


def render_home_page():
    """Main landing page content: quick-stats, feature highlights, and navigation cards."""
    inject_custom_css()
    create_tables()
    settings = load_settings()

    # Hero Banner
    st.markdown('<h1 class="gradient-title">🤖 AI Interview Simulator</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #94A3B8; font-size: 1.15rem; font-weight: 500; margin-bottom: 2rem;">'
        'Master your technical interviews with realistic AI-generated questions and real-time multi-dimensional scoring.'
        '</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Quick Stats Row
    stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👥 Total Interviews", stats.get("total_interviews", 0))

    with col2:
        st.metric("❓ Questions Answered", stats.get("total_questions_answered", 0))

    with col3:
        avg = stats.get("average_score", 0.0)
        st.metric("⭐ Average Score", f"{avg:.1f}/100" if avg else "—")

    with col4:
        best = stats.get("highest_score", 0.0)
        st.metric("🏆 Best Score", f"{best:.1f}/100" if best else "—")

    st.divider()

    # Navigation Action Cards
    c_btn1, c_btn2, c_btn3 = st.columns([2, 2, 2])

    with c_btn1:
        st.page_link(
            page_interview,
            label="🚀 Start New Interview",
            use_container_width=True,
        )

    with c_btn2:
        st.page_link(
            page_history,
            label="📜 View History",
            use_container_width=True,
        )

    with c_btn3:
        st.page_link(
            page_dashboard,
            label="📊 Performance Analytics",
            use_container_width=True,
        )

    st.divider()

    # Feature Highlights Cards
    st.markdown('<h2 class="sub-gradient-title">💡 Why Prepare with AI Simulator?</h2>', unsafe_allow_html=True)

    f_col1, f_col2, f_col3 = st.columns(3)

    with f_col1:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: #818CF8; font-size: 1.25rem; font-weight: 700; margin-bottom: 8px;">🎯 Targeted Scenarios</h3>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                Practice role-specific interview questions for Python, Java, AI, Full Stack, and Custom Engineering roles with 3 calibrated difficulty levels.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f_col2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: #C084FC; font-size: 1.25rem; font-weight: 700; margin-bottom: 8px;">📊 Deep Evaluation</h3>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                Get immediate feedback scoring your technical <b>Accuracy</b>, <b>Depth</b>, and <b>Communication</b> alongside key missed points.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with f_col3:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: #38BDF8; font-size: 1.25rem; font-weight: 700; margin-bottom: 8px;">📈 Growth Analytics</h3>
            <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6;">
                Track your progress through Plotly charts, performance trends, and export complete interview reports to CSV anytime.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.info("👈 Select a tool from the sidebar navigation to get started!")


# ----------------------------------------------------
# Declarative Navigation (Streamlit >= 1.36)
# ----------------------------------------------------
if "is_owner_authenticated" not in st.session_state:
    st.session_state.is_owner_authenticated = False

# Check for owner login trigger via URL query parameter (e.g. ?admin=true)
query_params = st.query_params
is_admin_requested = query_params.get("admin") == "true"

# If owner requested login and is not yet authenticated, show the login dialog inline
if is_admin_requested and not st.session_state.is_owner_authenticated:
    st.set_page_config(page_title="Owner Login", page_icon="🔒", layout="centered")
    inject_custom_css()

    st.markdown('<h1 class="gradient-title">🔒 Owner Authentication</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94A3B8; font-size:1.05rem; font-weight:500; margin-bottom:1.5rem;">'
        'Enter your owner password to unlock administrative settings and configuration.'
        '</p>',
        unsafe_allow_html=True,
    )

    expected_password = None
    try:
        expected_password = st.secrets.get("OWNER_PASSWORD")
    except Exception:
        expected_password = None

    if not expected_password:
        st.error("⚠️ Owner password is not configured in `.streamlit/secrets.toml`.")
        st.stop()

    with st.form("owner_login_prompt"):
        entered = st.text_input("Owner Password", type="password", placeholder="Enter owner password...")
        submit = st.form_submit_button("Unlock Settings", use_container_width=True)

        if submit:
            if entered == expected_password:
                st.session_state.is_owner_authenticated = True
                # Clean query param so URL returns to clean root on next interaction
                del st.query_params["admin"]
                st.success("✅ Authenticated! Settings unlocked in sidebar.")
                st.rerun()
            else:
                st.error("❌ Incorrect password.")

    st.stop()

# Base pages available to all users
page_home = st.Page(render_home_page, title="Home", icon="🏠", default=True)
page_interview = st.Page("pages/1_Interview.py", title="AI Interview", icon="🎤")
page_history = st.Page("pages/2_History.py", title="History", icon="📜")
page_dashboard = st.Page("pages/3_Dashboard.py", title="Dashboard", icon="📊")

nav_pages = [page_home, page_interview, page_history, page_dashboard]

# Conditionally include Settings ONLY if authenticated in the current session
if st.session_state.get("is_owner_authenticated", False):
    page_settings = st.Page("pages/4_Settings.py", title="Settings", icon="⚙️")
    nav_pages.append(page_settings)

# Execute navigation router
pg = st.navigation(nav_pages)
pg.run()