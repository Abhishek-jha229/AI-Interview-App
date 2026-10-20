"""
Analytics Dashboard page for AI Interview Simulator.
Renders dark-themed Plotly visualizations with glassmorphic metric cards
and multi-dimensional performance breakdowns.
"""

from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.database import (
    get_aspect_stats,
    get_dashboard_stats,
    get_interviews_filtered,
    get_score_timeline,
    get_stats_by_difficulty,
    get_stats_by_role,
)
from core.settings import get_all_roles
from core.theme import apply_plotly_theme, inject_custom_css

st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")
inject_custom_css()

st.markdown('<h1 class="gradient-title">📊 Performance Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#94A3B8; font-size:1.05rem; font-weight:500; margin-bottom:1.5rem;">'
    "Track your interview progress, score trends, and skill-level breakdowns."
    "</p>",
    unsafe_allow_html=True,
)

# -----------------------
# Filters Section
# -----------------------
with st.expander("🔍 Dashboard Filters", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        roles_list = ["All"] + get_all_roles()
        filter_role = st.selectbox("Role", roles_list, key="dash_role")

    with col2:
        filter_diff = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"], key="dash_diff")

    with col3:
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        date_range = st.date_input(
            "Date Range",
            value=(thirty_days_ago, today),
            key="dash_date",
        )

date_from = None
date_to = None
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    date_from = date_range[0].strftime("%Y-%m-%d")
    date_to = date_range[1].strftime("%Y-%m-%d")

# Fetch aggregate metrics
stats = get_dashboard_stats(
    role=filter_role,
    difficulty=filter_diff,
    date_from=date_from,
    date_to=date_to,
)

total_interviews = stats.get("total_interviews", 0)

if total_interviews == 0:
    st.markdown(
        """
        <div class="glass-card" style="text-align:center; padding: 48px;">
            <p style="font-size: 3rem; margin-bottom: 16px;">📭</p>
            <h3 style="color: #F8FAFC; font-weight: 700; margin-bottom: 8px;">No Data Yet</h3>
            <p style="color: #94A3B8; font-size: 1rem;">
                No interview records match your selected filters.<br/>
                Start an interview session to begin generating performance analytics!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_Interview.py", label="🚀 Start Interview Now", icon="🎤")
    st.stop()

# -----------------------
# Top Row Metrics
# -----------------------
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("🗂️ Total Interviews", total_interviews)

with m2:
    st.metric("❓ Questions Answered", stats.get("total_questions_answered", 0))

with m3:
    avg = stats.get("average_score", 0.0)
    st.metric("⭐ Average Score", f"{avg:.1f}/100" if avg else "—")

with m4:
    best = stats.get("highest_score", 0.0)
    st.metric("🏆 Best Score", f"{best:.1f}/100" if best else "—")

with m5:
    delta = stats.get("improvement_delta")
    if delta is not None:
        st.metric(
            "📈 Score Trend",
            f"{stats['last_5_avg']:.1f}",
            delta=f"{delta:+.1f} vs prev 5",
            delta_color="normal",
        )
    else:
        st.metric("📈 Score Trend", "—", help="Requires 6+ interviews to calculate trend")

st.divider()

# -----------------------
# Charts Row 1: Score Timeline & Aspect Ratings
# -----------------------
c_col1, c_col2 = st.columns([3, 2])

with c_col1:
    st.markdown('<h3 class="sub-gradient-title">📈 Score Progression Over Time</h3>', unsafe_allow_html=True)
    timeline_data = get_score_timeline(
        role=filter_role,
        difficulty=filter_diff,
        date_from=date_from,
        date_to=date_to,
    )
    if timeline_data:
        df_time = pd.DataFrame(timeline_data)
        fig_line = px.line(
            df_time,
            x="interview_date",
            y="average_score",
            color="role" if filter_role == "All" else None,
            markers=True,
            title="Interview Scores Chronologically",
            labels={"interview_date": "Date & Time", "average_score": "Average Score (/100)"},
        )
        # Glow effect on the score line
        fig_line.update_traces(
            line=dict(width=2.5),
            marker=dict(size=8, line=dict(width=2, color="#6366F1")),
        )
        if filter_role != "All":
            fig_line.update_traces(
                line_color="#818CF8",
                marker_color="#A855F7",
            )
        fig_line.update_yaxes(range=[0, 105])
        fig_line.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=370)
        apply_plotly_theme(fig_line)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.caption("No timeline data available.")

with c_col2:
    st.markdown('<h3 class="sub-gradient-title">🕸️ Skill Dimension Breakdown</h3>', unsafe_allow_html=True)
    aspects = get_aspect_stats(
        role=filter_role,
        difficulty=filter_diff,
        date_from=date_from,
        date_to=date_to,
    )

    categories = list(aspects.keys())
    values = list(aspects.values())

    fig_bar_aspect = go.Figure(
        go.Bar(
            x=categories,
            y=values,
            marker=dict(
                color=values,
                colorscale=[
                    [0.0, "#4F46E5"],
                    [0.5, "#8B5CF6"],
                    [1.0, "#EC4899"],
                ],
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            text=[f"{v:.0f}" for v in values],
            textposition="outside",
            textfont=dict(color="#F8FAFC", size=13, family="Plus Jakarta Sans"),
        )
    )
    fig_bar_aspect.update_yaxes(range=[0, 115])
    fig_bar_aspect.update_layout(
        title="Performance Across Evaluation Dimensions",
        margin=dict(l=20, r=20, t=40, b=20),
        height=370,
        showlegend=False,
    )
    apply_plotly_theme(fig_bar_aspect)
    st.plotly_chart(fig_bar_aspect, use_container_width=True)

st.divider()

# -----------------------
# Charts Row 2: Role & Difficulty Breakdowns
# -----------------------
b_col1, b_col2 = st.columns(2)

with b_col1:
    st.markdown('<h3 class="sub-gradient-title">💼 Average Score by Role</h3>', unsafe_allow_html=True)
    role_stats = get_stats_by_role(
        difficulty=filter_diff,
        date_from=date_from,
        date_to=date_to,
    )
    if role_stats:
        df_role = pd.DataFrame(role_stats)
        fig_role = go.Figure(
            go.Bar(
                x=df_role["role"],
                y=df_role["avg_score"],
                marker=dict(
                    color=df_role["avg_score"],
                    colorscale=[
                        [0.0, "#1E3A5F"],
                        [0.5, "#3B82F6"],
                        [1.0, "#38BDF8"],
                    ],
                    line=dict(color="rgba(0,0,0,0)"),
                ),
                text=[f"{s:.1f}" for s in df_role["avg_score"]],
                textposition="outside",
                textfont=dict(color="#F8FAFC", size=12),
            )
        )
        fig_role.update_yaxes(range=[0, 115])
        fig_role.update_layout(
            title="Average Performance per Job Role",
            height=340,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        apply_plotly_theme(fig_role)
        st.plotly_chart(fig_role, use_container_width=True)
    else:
        st.caption("No role breakdown data available.")

with b_col2:
    st.markdown('<h3 class="sub-gradient-title">🎯 Average Score by Difficulty</h3>', unsafe_allow_html=True)
    diff_stats = get_stats_by_difficulty(
        role=filter_role,
        date_from=date_from,
        date_to=date_to,
    )
    if diff_stats:
        df_diff = pd.DataFrame(diff_stats)
        DIFF_COLORS = {"Easy": "#10B981", "Medium": "#F59E0B", "Hard": "#F43F5E"}
        colors = [DIFF_COLORS.get(d, "#818CF8") for d in df_diff["difficulty"]]
        fig_diff = go.Figure(
            go.Bar(
                x=df_diff["difficulty"],
                y=df_diff["avg_score"],
                marker=dict(color=colors, line=dict(color="rgba(0,0,0,0)")),
                text=[f"{s:.1f}" for s in df_diff["avg_score"]],
                textposition="outside",
                textfont=dict(color="#F8FAFC", size=12),
            )
        )
        fig_diff.update_yaxes(range=[0, 115])
        fig_diff.update_layout(
            title="Performance by Difficulty Level",
            height=340,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        apply_plotly_theme(fig_diff)
        st.plotly_chart(fig_diff, use_container_width=True)
    else:
        st.caption("No difficulty breakdown data available.")

st.divider()

# -----------------------
# Table: 10 Most Recent Interviews
# -----------------------
st.markdown('<h3 class="sub-gradient-title">📋 Recent Filtered Interviews</h3>', unsafe_allow_html=True)
recent_list = get_interviews_filtered(
    role=filter_role,
    difficulty=filter_diff,
    date_from=date_from,
    date_to=date_to,
    sort_by="newest",
)[:10]

if recent_list:
    table_rows = []
    for iv in recent_list:
        score_val = iv["average_score"] or 0.0
        badge = "🟢" if score_val >= 75 else ("🟡" if score_val >= 50 else "🔴")
        table_rows.append({
            "": badge,
            "ID": iv["id"],
            "Candidate": iv["candidate_name"],
            "Role": iv["role"],
            "Difficulty": iv["difficulty"],
            "Average Score": f"{score_val:.1f}/100",
            "Date": iv["interview_date"],
            "Status": (iv.get("status") or "completed").replace("_", " ").title(),
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
