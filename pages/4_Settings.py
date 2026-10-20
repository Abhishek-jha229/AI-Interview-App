"""
Settings & Configuration page for AI Interview Simulator.
Manages Groq API connection test, model preferences, default interview options,
custom job roles, and data export / purge operations.
All sections styled with glassmorphic cards and gradient headers.
"""

import os
import pandas as pd
import streamlit as st

from core.ai import test_groq_connection
from core.analytics import get_analytics_summary
from core.database import clear_all_history, get_all_interviews
from core.settings import (
    BUILTIN_ROLES,
    load_settings,
    save_settings,
)
from core.theme import inject_custom_css

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
inject_custom_css()

# -----------------------
# Owner Authentication Gate
# -----------------------
if "is_owner_authenticated" not in st.session_state:
    st.session_state.is_owner_authenticated = False

# If not authenticated, show password prompt ONLY and halt execution
if not st.session_state.is_owner_authenticated:
    st.markdown('<h1 class="gradient-title">🔒 Protected Settings</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94A3B8; font-size:1.05rem; font-weight:500; margin-bottom:1.5rem;">'
        'This area is restricted to the application owner. Please enter your password to continue.'
        '</p>',
        unsafe_allow_html=True,
    )

    expected_password = None
    try:
        expected_password = st.secrets.get("OWNER_PASSWORD")
    except Exception:
        expected_password = None

    if not expected_password:
        st.error("⚠️ Owner password is not configured in `.streamlit/secrets.toml`. Access is blocked.")
        st.stop()

    with st.form("owner_login_form"):
        entered_password = st.text_input(
            "Owner Password",
            type="password",
            placeholder="Enter owner password...",
            help="Configured in .streamlit/secrets.toml",
        )
        submit_auth = st.form_submit_button("Unlock Settings", use_container_width=True)

        if submit_auth:
            if entered_password == expected_password:
                st.session_state.is_owner_authenticated = True
                st.success("✅ Authenticated successfully!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Access denied.")

    st.stop()

# -----------------------
# Authenticated Owner View
# -----------------------
c_head1, c_head2 = st.columns([5, 1])
with c_head1:
    st.markdown('<h1 class="gradient-title">⚙️ System Settings & Configuration</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94A3B8; font-size:1.05rem; font-weight:500; margin-bottom:1.5rem;">'
        "Manage your API keys, AI model, default preferences, custom roles, and database controls."
        "</p>",
        unsafe_allow_html=True,
    )
with c_head2:
    st.write("")
    if st.button("🔒 Lock", help="Lock settings and sign out", use_container_width=True):
        st.session_state.is_owner_authenticated = False
        st.rerun()

settings = load_settings()

# -----------------------
# Section 1: Groq API & Model Status
# -----------------------
st.markdown('<h2 class="sub-gradient-title">🔑 API Key & Model Configuration</h2>', unsafe_allow_html=True)

api_key = os.getenv("GROQ_API_KEY", "").strip()

c_api1, c_api2 = st.columns([3, 1])

with c_api1:
    if api_key:
        st.markdown(
            """
            <div style="
                background: rgba(16,185,129,0.1);
                border: 1px solid rgba(16,185,129,0.35);
                border-radius: 12px;
                padding: 14px 18px;
                color: #34D399;
                font-weight: 600;
                font-size: 0.95rem;
            ">
                ✅ &nbsp;<strong>AI Service API Key:</strong>&nbsp; Configured (Active)
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="
                background: rgba(244,63,94,0.1);
                border: 1px solid rgba(244,63,94,0.35);
                border-radius: 12px;
                padding: 14px 18px;
                color: #FB7185;
                font-weight: 600;
                font-size: 0.95rem;
            ">
                ❌ &nbsp;<strong>AI Service API Key:</strong>&nbsp; Missing — Add <code>GROQ_API_KEY=your_key</code> to <code>.env</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

with c_api2:
    st.write("")
    if st.button("🔌 Test Connection", use_container_width=True):
        with st.spinner("Testing AI service connection..."):
            ok, msg = test_groq_connection()
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")

st.write("")

# Model Selector
available_models = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b",
    "groq/compound",
    "groq/compound-mini",
]
current_model = settings.get("groq_model", "openai/gpt-oss-120b")
if current_model not in available_models:
    available_models.insert(0, current_model)

selected_model = st.selectbox(
    "Preferred AI Model",
    available_models,
    index=available_models.index(current_model),
    help="Select the AI model used for question generation and answer evaluations.",
)

st.divider()

# -----------------------
# Section 2: Interview Default Preferences
# -----------------------
st.markdown('<h2 class="sub-gradient-title">🎯 Default Interview Preferences</h2>', unsafe_allow_html=True)

p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    all_roles = list(BUILTIN_ROLES) + list(settings.get("custom_roles", []))
    cur_def_role = settings.get("default_role", "Python Developer")
    def_role_idx = all_roles.index(cur_def_role) if cur_def_role in all_roles else 0
    selected_def_role = st.selectbox("Default Candidate Role", all_roles, index=def_role_idx)

with p_col2:
    diff_opts = ["Easy", "Medium", "Hard"]
    cur_def_diff = settings.get("default_difficulty", "Medium")
    def_diff_idx = diff_opts.index(cur_def_diff) if cur_def_diff in diff_opts else 1
    selected_def_diff = st.selectbox("Default Difficulty Level", diff_opts, index=def_diff_idx)

with p_col3:
    cur_def_count = int(settings.get("default_question_count", 5))
    selected_def_count = st.slider("Default Question Count", 3, 15, cur_def_count)

# Per-question timer toggle
enable_timer = st.checkbox(
    "Enable Per-Question Informational Timer during interviews",
    value=bool(settings.get("enable_question_timer", False)),
    help="Displays elapsed time on the current question in the UI. Informational only — never blocks or auto-submits.",
)

st.divider()

# -----------------------
# Section 2b: Voice Answer Settings
# -----------------------
st.markdown('<h2 class="sub-gradient-title">🎙️ Voice Answer Settings</h2>', unsafe_allow_html=True)
st.caption(
    "When enabled, a **Record** button appears below every answer box during interviews. "
    "Your spoken answer is automatically transcribed — works in all browsers."
)

v_col1, v_col2, v_col3 = st.columns(3)

with v_col1:
    enable_voice = st.toggle(
        "Enable Voice Answers",
        value=bool(settings.get("enable_voice_answers", True)),
        help="Show the microphone recorder below each answer textarea during an interview session.",
    )

with v_col2:
    voice_mode_opts = ["Append", "Replace"]
    cur_voice_mode = settings.get("default_voice_mode", "Append")
    voice_mode_idx = voice_mode_opts.index(cur_voice_mode) if cur_voice_mode in voice_mode_opts else 0
    selected_voice_mode = st.selectbox(
        "Default Transcription Mode",
        voice_mode_opts,
        index=voice_mode_idx,
        help="**Append** adds new recordings to existing text. **Replace** overwrites it. Users can switch per-question during the interview.",
    )

with v_col3:
    whisper_models = [
        "whisper-large-v3-turbo",
        "whisper-large-v3",
        "distil-whisper-large-v3-en",
    ]
    cur_whisper = settings.get("whisper_model", "whisper-large-v3-turbo")
    if cur_whisper not in whisper_models:
        whisper_models.insert(0, cur_whisper)
    selected_whisper = st.selectbox(
        "Whisper Transcription Model",
        whisper_models,
        index=whisper_models.index(cur_whisper),
        help="**whisper-large-v3-turbo** is fastest and recommended. **whisper-large-v3** is highest accuracy. **distil-whisper** is English-only but very fast.",
    )

st.markdown(
    """
    <div style="background:rgba(168,85,247,0.08); border:1px solid rgba(168,85,247,0.25);
         border-radius:12px; padding:12px 16px; margin-top:8px;">
        <p style="color:#C084FC; font-size:0.9rem; font-weight:600; margin:0 0 4px 0;">🎤 How Voice Answers Work</p>
        <p style="color:#94A3B8; font-size:0.85rem; margin:0; line-height:1.6;">
            Click the record button → speak your answer → click stop → your answer is automatically
            transcribed and inserted into the answer box. You can then edit it before submitting.
            Works in all browsers — no Chrome/Edge requirement.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# -----------------------

# Section 3: Custom Role Management
# -----------------------
st.markdown('<h2 class="sub-gradient-title">💼 Custom Role Management</h2>', unsafe_allow_html=True)
st.caption("Add custom target roles to appear in your interview setup dropdown alongside built-in roles.")

custom_roles = list(settings.get("custom_roles", []))

cr_col1, cr_col2 = st.columns([3, 1])

with cr_col1:
    new_role = st.text_input("Add New Custom Role", placeholder="e.g. Cybersecurity Specialist")

with cr_col2:
    st.write(" ")
    st.write(" ")
    if st.button("➕ Add Role", use_container_width=True):
        if new_role and new_role.strip():
            clean_role = new_role.strip()
            if clean_role not in custom_roles and clean_role not in BUILTIN_ROLES:
                custom_roles.append(clean_role)
                settings["custom_roles"] = custom_roles
                save_settings(settings)
                st.success(f"Added custom role: '{clean_role}'")
                st.rerun()
            else:
                st.warning("That role already exists.")

if custom_roles:
    st.write("**Current Custom Roles:**")
    for r in list(custom_roles):
        c_r1, c_r2 = st.columns([4, 1])
        with c_r1:
            st.markdown(
                f'<div style="background:rgba(30,41,59,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:10px 14px; color:#CBD5E1; font-weight:500; margin-bottom:6px;">💼 {r}</div>',
                unsafe_allow_html=True,
            )
        with c_r2:
            st.write("")
            if st.button("🗑️ Remove", key=f"rem_role_{r}"):
                custom_roles.remove(r)
                settings["custom_roles"] = custom_roles
                save_settings(settings)
                st.success(f"Removed custom role: '{r}'")
                st.rerun()

st.divider()

# Save Preferences Button
if st.button("💾 Save All Settings", use_container_width=True):
    settings["groq_model"] = selected_model
    settings["default_role"] = selected_def_role
    settings["default_difficulty"] = selected_def_diff
    settings["default_question_count"] = selected_def_count
    settings["enable_question_timer"] = enable_timer
    settings["custom_roles"] = custom_roles
    settings["enable_voice_answers"] = enable_voice
    settings["whisper_model"] = selected_whisper
    settings["default_voice_mode"] = selected_voice_mode

    if save_settings(settings):
        st.success("✅ Settings saved successfully!")
    else:
        st.error("❌ Failed to save settings to settings.json.")

st.divider()

# -----------------------
# Section 4: Data Management & Reset
# -----------------------
st.markdown('<h2 class="sub-gradient-title">🧹 Data Management & Maintenance</h2>', unsafe_allow_html=True)

dm_col1, dm_col2 = st.columns(2)

with dm_col1:
    st.markdown(
        """
        <div class="glass-card">
            <h4 style="color:#38BDF8; font-weight:700; margin-bottom:8px;">📥 Export Full Database</h4>
            <p style="color:#94A3B8; font-size:0.9rem;">Download a complete CSV snapshot of all interview records for offline archiving or analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    all_ivs = get_all_interviews()
    if all_ivs:
        df_all = pd.DataFrame(all_ivs)
        csv_all = df_all.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Complete Interview Database (CSV)",
            data=csv_all,
            file_name="full_interview_database.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Database is empty. Nothing to export.")

with dm_col2:
    st.markdown(
        """
        <div class="glass-card" style="border-color: rgba(244,63,94,0.25);">
            <h4 style="color:#FB7185; font-weight:700; margin-bottom:8px;">⚠️ Clear All History</h4>
            <p style="color:#94A3B8; font-size:0.9rem;">Permanently deletes all interview records and question details from the database. This action is irreversible.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    confirm_text = st.text_input("Type 'DELETE' to enable clear history button:", key="confirm_clear_input")

    if st.button("🗑️ Clear All History", disabled=(confirm_text.strip() != "DELETE"), use_container_width=True):
        try:
            clear_all_history()
            st.success("✅ All interview history wiped successfully.")
            st.rerun()
        except Exception:
            st.error("Failed to clear history. Please try again.")

st.divider()

# -----------------------
# Section 5: Usage Analytics (Owner Only)
# -----------------------
st.markdown('<h2 class="sub-gradient-title">📊 Usage Analytics</h2>', unsafe_allow_html=True)
st.caption("Live session and performance metrics tracked automatically during interviews.")

analytics = get_analytics_summary()

a_col1, a_col2, a_col3 = st.columns(3)
with a_col1:
    st.metric("👥 Total Sessions", analytics.get("total_sessions", 0))
with a_col2:
    st.metric("❓ Questions Answered", analytics.get("total_questions", 0))
with a_col3:
    avg_s = analytics.get("avg_score", 0.0)
    st.metric("⭐ Average Score", f"{avg_s:.1f}/100" if avg_s else "—")

# Daily activity chart
daily_df = analytics.get("daily_df")
if daily_df is not None and not daily_df.empty:
    st.write("**Daily Active Sessions**")
    st.bar_chart(daily_df.set_index("date")["session_count"])

# Recent activity table
recent_df = analytics.get("recent_df")
if recent_df is not None and not recent_df.empty:
    st.write("**Recent Activity (last 50 events)**")
    st.dataframe(
        recent_df[["timestamp", "event_type", "question_number", "score", "total_time_taken"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No analytics events recorded yet. Start an interview session to begin tracking.")

