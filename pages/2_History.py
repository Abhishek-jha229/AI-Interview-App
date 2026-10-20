"""
Interview History page for AI Interview Simulator.
Provides filtered search, sorting, glassmorphic interview cards,
glowing pill-badge ratings, cascade deletion, and CSV export.
"""

from datetime import datetime
import io
import pandas as pd
import streamlit as st

from core.database import (
    delete_interview,
    get_interview_details,
    get_interviews_filtered,
)
from core.settings import get_all_roles
from core.theme import get_pill_badge, inject_custom_css

st.set_page_config(page_title="Interview History", page_icon="📜", layout="wide")
inject_custom_css()

st.markdown('<h1 class="gradient-title">📜 Interview History & Reports</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:#94A3B8; font-size:1.05rem; font-weight:500; margin-bottom:1.5rem;">'
    "Browse, filter, and export your complete interview session history."
    "</p>",
    unsafe_allow_html=True,
)

# -----------------------
# Filters Section
# -----------------------
with st.expander("🔍 Search & Filter History", expanded=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        search_name = st.text_input("Candidate Name", placeholder="Search candidate...")

    with col2:
        roles_options = ["All"] + get_all_roles()
        filter_role = st.selectbox("Role", roles_options)

    with col3:
        filter_diff = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"])

    with col4:
        sort_choice = st.selectbox(
            "Sort Order",
            ["Newest First", "Oldest First", "Highest Score", "Lowest Score"],
        )

sort_map = {
    "Newest First": "newest",
    "Oldest First": "oldest",
    "Highest Score": "highest_score",
    "Lowest Score": "lowest_score",
}

# Fetch filtered records
interviews = get_interviews_filtered(
    candidate_name=search_name,
    role=filter_role,
    difficulty=filter_diff,
    sort_by=sort_map.get(sort_choice, "newest"),
)

if not interviews:
    st.info("No interview records found matching your filters.")
    st.stop()

# -----------------------
# Filtered Summary & Global Export
# -----------------------
st.caption(f"Showing {len(interviews)} interview record(s)")

# Export all filtered records as CSV
export_rows = []
for iv in interviews:
    export_rows.append({
        "ID": iv["id"],
        "Candidate Name": iv["candidate_name"],
        "Role": iv["role"],
        "Difficulty": iv["difficulty"],
        "Average Score": iv["average_score"],
        "Total Questions": iv["total_questions"],
        "Status": iv.get("status", "completed") or "completed",
        "Duration (sec)": iv.get("duration_seconds") or "",
        "Date": iv["interview_date"],
    })
df_export = pd.DataFrame(export_rows)
csv_buffer = df_export.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Export Filtered History to CSV",
    data=csv_buffer,
    file_name=f"interview_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)

st.divider()

# -----------------------
# Pagination State
# -----------------------
ITEMS_PER_PAGE = 10
if "history_page" not in st.session_state:
    st.session_state.history_page = 1

total_pages = max(1, (len(interviews) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
page = max(1, min(st.session_state.history_page, total_pages))

start_idx = (page - 1) * ITEMS_PER_PAGE
end_idx = start_idx + ITEMS_PER_PAGE
page_interviews = interviews[start_idx:end_idx]

# Delete confirmation tracking
if "delete_confirm_id" not in st.session_state:
    st.session_state.delete_confirm_id = None


def _score_color(score):
    """Return a CSS color string for a given score value."""
    if score >= 75:
        return "#34D399"
    elif score >= 50:
        return "#FBBF24"
    return "#FB7185"


# Render interview items
for iv in page_interviews:
    iv_id = iv["id"]
    candidate = iv.get("candidate_name") or "Anonymous"
    role = iv.get("role") or "—"
    diff = iv.get("difficulty") or "—"
    score = iv.get("average_score") or 0.0
    date_str = iv.get("interview_date") or "—"
    status = iv.get("status") or "completed"

    badge_color = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")
    title_label = f"{badge_color} {candidate} | {role} ({diff}) | {score:.1f}/100 | {date_str}"

    with st.expander(title_label):
        # Glassmorphic header info strip
        score_color = _score_color(score)
        st.markdown(
            f"""
            <div style="
                background: rgba(17, 24, 39, 0.55);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
                padding: 16px 20px;
                margin-bottom: 16px;
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                align-items: center;
            ">
                <div style="flex:1; min-width:160px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">CANDIDATE</p>
                    <p style="margin:0; color:#F8FAFC; font-size:1.1rem; font-weight:700;">{candidate}</p>
                </div>
                <div style="flex:1; min-width:140px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">ROLE</p>
                    <p style="margin:0; color:#F8FAFC; font-size:1rem; font-weight:600;">{role}</p>
                </div>
                <div style="flex:1; min-width:120px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">DIFFICULTY</p>
                    <p style="margin:0; color:#F8FAFC; font-size:1rem; font-weight:600;">{diff}</p>
                </div>
                <div style="flex:1; min-width:140px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">AVERAGE SCORE</p>
                    <p style="margin:0; color:{score_color}; font-size:1.6rem; font-weight:800;">{score:.1f}<span style="font-size:0.9rem; color:#94A3B8;">/100</span></p>
                </div>
                <div style="flex:1; min-width:120px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">STATUS</p>
                    <p style="margin:0; color:#F8FAFC; font-size:1rem; font-weight:600;">{status.replace("_"," ").title()}</p>
                </div>
                <div style="flex:1; min-width:130px;">
                    <p style="margin:0; color:#94A3B8; font-size:0.8rem; font-weight:600;">DATE</p>
                    <p style="margin:0; color:#F8FAFC; font-size:0.95rem; font-weight:600;">{date_str[:10] if len(date_str)>=10 else date_str}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Duration metric
        dur = iv.get("duration_seconds")
        if dur:
            mins, secs = divmod(dur, 60)
            st.caption(f"⏱️ Total duration: {mins}m {secs}s")

        st.divider()

        # Detailed questions
        details = get_interview_details(iv_id)

        if not details:
            st.caption("No question details recorded for this interview.")
        else:
            for idx, item in enumerate(details, start=1):
                q_score = item.get("score", 0.0) or 0.0
                acc = item.get("accuracy") or "—"
                tech = item.get("technical_depth") or "—"
                comm = item.get("communication") or "—"

                # Glowing pill badges for ratings
                badges_html = f"""
                <div style="margin: 6px 0 12px 0; display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                    <span style="color:#94A3B8; font-size:0.85rem; font-weight:600; margin-right:4px;">Q{idx}:</span>
                    {get_pill_badge(f"Score: {q_score:.0f}/100", score=q_score)}
                    {get_pill_badge(f"Accuracy: {acc}", variant="indigo")}
                    {get_pill_badge(f"Depth: {tech}", variant="purple")}
                    {get_pill_badge(f"Comm: {comm}", variant="indigo")}
                </div>
                """
                st.markdown(badges_html, unsafe_allow_html=True)

                with st.container():
                    st.markdown(f"**❓ Question {idx}:**")
                    st.markdown(
                        f'<div style="background:rgba(30,41,59,0.6); border-left:3px solid #6366F1; padding:12px 16px; border-radius:8px; color:#CBD5E1; margin-bottom:8px;">{item.get("question") or "—"}</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown("**✍️ Candidate Answer:**")
                    st.info(item.get("answer") or "—")

                missing = item.get("missing_points_parsed", [])
                if missing:
                    st.markdown("**⚠️ Missing Key Points:**")
                    for pt in missing:
                        st.write(f"• {pt}")

                st.markdown("**💬 AI Feedback:**")
                st.success(item.get("feedback") or "—")

                # Model Explanation (learning reference)
                model_exp = item.get("model_explanation", "") or ""
                if model_exp and model_exp != "No model explanation available.":
                    with st.expander("📖 View Ideal Model Answer & Explanation"):
                        st.markdown(
                            '<p style="color:#34D399; font-size:0.9rem; font-weight:600; margin-bottom:8px;">Study this to improve future answers:</p>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(model_exp)

                if idx < len(details):
                    st.markdown('<hr style="border-color: rgba(255,255,255,0.08);">', unsafe_allow_html=True)

        # Export single interview as CSV
        single_export_rows = []
        for idx, item in enumerate(details, start=1):
            single_export_rows.append({
                "Question #": idx,
                "Question": item.get("question"),
                "Answer": item.get("answer"),
                "Score": item.get("score"),
                "Accuracy": item.get("accuracy"),
                "Technical Depth": item.get("technical_depth"),
                "Communication": item.get("communication"),
                "Feedback": item.get("feedback"),
            })
        single_df = pd.DataFrame(single_export_rows)
        single_csv = single_df.to_csv(index=False).encode("utf-8")

        c_exp1, c_exp2 = st.columns([3, 1])
        with c_exp1:
            st.download_button(
                label=f"📄 Download Report for {candidate} (CSV)",
                data=single_csv,
                file_name=f"interview_report_{iv_id}_{candidate.replace(' ', '_')}.csv",
                mime="text/csv",
                key=f"dl_{iv_id}",
            )
        with c_exp2:
            if st.button("🗑️ Delete Record", key=f"del_btn_{iv_id}"):
                st.session_state.delete_confirm_id = iv_id

        # Delete confirmation dialog
        if st.session_state.delete_confirm_id == iv_id:
            st.error(f"⚠️ Are you sure you want to delete interview #{iv_id} for {candidate}? This cannot be undone.")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                if st.button("✅ Yes, Delete", key=f"confirm_del_{iv_id}"):
                    delete_interview(iv_id)
                    st.session_state.delete_confirm_id = None
                    st.success("Record deleted.")
                    st.rerun()
            with c_d2:
                if st.button("❌ Cancel", key=f"cancel_del_{iv_id}"):
                    st.session_state.delete_confirm_id = None
                    st.rerun()

# -----------------------
# Pagination Controls
# -----------------------
if total_pages > 1:
    st.divider()
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("⬅️ Previous", disabled=(page <= 1)):
            st.session_state.history_page = page - 1
            st.rerun()
    with p_col2:
        st.markdown(
            f'<p style="text-align:center; color:#94A3B8; font-weight:600;">Page {page} of {total_pages}</p>',
            unsafe_allow_html=True,
        )
    with p_col3:
        if st.button("Next ➡️", disabled=(page >= total_pages)):
            st.session_state.history_page = page + 1
            st.rerun()
