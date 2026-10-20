"""
Interactive AI Interview page.
Manages setup, live question flow, Text-to-Speech playback,
answer evaluations with glowing pill ratings, running timers, and result summaries.
"""

import hashlib
import json
import time
import streamlit as st

import traceback
from core.analytics import log_analytics_event
from core.database import save_interview, save_question_detail
from core.evaluator import evaluate_answer
from core.settings import get_all_roles, load_settings
from core.speech import transcribe_audio
from core.theme import (
    get_pill_badge,
    inject_custom_css,
    render_live_timer,
    render_tts_button,
    render_voice_recorder_css,
)
from core.ai import generate_questions, GroqConfigError, GroqRetryableError, GroqError
st.set_page_config(page_title="AI Interview", page_icon="🎤", layout="wide")
inject_custom_css()
render_voice_recorder_css()

st.markdown('<h1 class="gradient-title">🎤 AI Technical Interview</h1>', unsafe_allow_html=True)


# -----------------------
# State Initialization
# -----------------------

def _init_state():
    settings = load_settings()
    defaults = {
        "started": False,
        "completed": False,
        "show_result": False,
        "saved": False,
        "questions": [],
        "current_question": 0,
        "answers": [],
        "evaluations": [],
        "scores": [],
        "interview_data": {},
        "total_questions": 0,
        "requested_questions": settings.get("default_question_count", 5),
        "fewer_questions_notice": False,
        "confirm_restart": False,
        "confirm_end": False,
        "generate_error": None,
        "generate_retryable": False,
        "evaluate_error": None,
        "evaluate_retryable": False,
        "save_error": None,
        "average_score": 0.0,
        "ended_early": False,
        "celebrate": False,
        "start_time": None,
        "question_start_time": None,
        "duration_seconds": 0,
        "session_uuid": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if not st.session_state.session_uuid:
        import uuid
        st.session_state.session_uuid = str(uuid.uuid4())[:8]
        log_analytics_event(st.session_state.session_uuid, "session_started")


def reset_to_setup():
    """Clear current interview session state and return to setup form."""
    settings = load_settings()
    _clear_all_voice_state()
    st.session_state.started = False
    st.session_state.completed = False
    st.session_state.show_result = False
    st.session_state.saved = False
    st.session_state.questions = []
    st.session_state.current_question = 0
    st.session_state.answers = []
    st.session_state.evaluations = []
    st.session_state.scores = []
    st.session_state.interview_data = {}
    st.session_state.total_questions = 0
    st.session_state.requested_questions = settings.get("default_question_count", 5)
    st.session_state.fewer_questions_notice = False
    st.session_state.confirm_restart = False
    st.session_state.confirm_end = False
    st.session_state.generate_error = None
    st.session_state.generate_retryable = False
    st.session_state.evaluate_error = None
    st.session_state.evaluate_retryable = False
    st.session_state.save_error = None
    st.session_state.average_score = 0.0
    st.session_state.ended_early = False
    st.session_state.celebrate = False
    st.session_state.start_time = None
    st.session_state.question_start_time = None
    st.session_state.duration_seconds = 0


def show_api_error(message, retryable, retry_label, retry_key):
    st.error(message)
    if retryable:
        return st.button(retry_label, key=retry_key, use_container_width=True)
    return False


_VOICE_KEY_PREFIXES = (
    "audio_",
    "voice_hash_",
    "voice_mode_",
    "voice_error_",
    "voice_retryable_",
    "voice_pending_bytes_",
    "voice_clear_pending_",
)


def _clear_all_voice_state():
    """Remove every per-question voice-recorder session_state key (full reset)."""
    for k in list(st.session_state.keys()):
        if k.startswith(_VOICE_KEY_PREFIXES):
            del st.session_state[k]


def _clear_voice_state_for(index):
    """Remove voice-recorder session_state tied to a single question index."""
    for prefix in _VOICE_KEY_PREFIXES:
        k = f"{prefix}{index}"
        if k in st.session_state:
            del st.session_state[k]


def persist_current_interview(*, ended_early=False):
    """Save interview once to database."""
    if st.session_state.saved:
        return True

    attempted = min(
        len(st.session_state.evaluations),
        len(st.session_state.answers),
        len(st.session_state.scores),
        len(st.session_state.questions),
    )
    if attempted == 0:
        return False

    scores = st.session_state.scores[:attempted]
    average_score = sum(scores) / len(scores)
    data = st.session_state.interview_data

    duration = 0
    if st.session_state.start_time:
        duration = int(time.time() - st.session_state.start_time)
    st.session_state.duration_seconds = duration

    status = "ended_early" if ended_early else "completed"

    try:
        interview_id = save_interview(
            candidate_name=data.get("name", ""),
            role=data.get("role", ""),
            difficulty=data.get("difficulty", ""),
            average_score=average_score,
            total_questions=st.session_state.total_questions,
            status=status,
            duration_seconds=duration,
        )

        for i in range(attempted):
            ev = st.session_state.evaluations[i]
            save_question_detail(
                interview_id=interview_id,
                question=st.session_state.questions[i],
                answer=st.session_state.answers[i],
                score=st.session_state.scores[i],
                feedback=ev.get("feedback", ""),
                accuracy=ev.get("accuracy", "—"),
                technical_depth=ev.get("technical_depth", "—"),
                communication=ev.get("communication", "—"),
                missing_points=ev.get("missing_points", []),
                model_explanation=ev.get("model_explanation", ""),
            )
    except Exception as exc:
        st.session_state.save_error = "Could not save this interview to the database. Please try again."
        return False

    st.session_state.saved = True
    st.session_state.average_score = average_score
    st.session_state.save_error = None

    # Log analytics event for completed interview session
    log_analytics_event(
        session_id=st.session_state.get("session_uuid") or "anon",
        event_type="interview_completed",
        score=average_score,
        total_time_taken=duration,
    )

    return True


def go_to_results(*, ended_early=False):
    st.session_state.started = False
    st.session_state.completed = True
    st.session_state.show_result = True
    st.session_state.ended_early = ended_early
    st.session_state.confirm_end = False
    st.session_state.confirm_restart = False


def begin_interview(name, role, difficulty, requested_total, bypass_cache=False):
    st.session_state.generate_error = None
    st.session_state.generate_retryable = False
    _clear_all_voice_state()

    try:
        questions = generate_questions(role, difficulty, requested_total, bypass_cache=bypass_cache)
    except GroqConfigError:
        st.session_state.generate_error = "AI service is not configured correctly. Please check your settings."
        st.session_state.generate_retryable = False
        return False
    except GroqRetryableError:
        st.session_state.generate_error = "AI service is temporarily unavailable. Please try again in a moment."
        st.session_state.generate_retryable = True
        return False
    except GroqError:
        st.session_state.generate_error = "Failed to generate interview questions. Please try again."
        st.session_state.generate_retryable = False
        return False

    now = time.time()
    st.session_state.questions = questions
    st.session_state.total_questions = len(questions)
    st.session_state.requested_questions = requested_total
    st.session_state.fewer_questions_notice = len(questions) < requested_total
    st.session_state.current_question = 0
    st.session_state.answers = []
    st.session_state.evaluations = []
    st.session_state.scores = []
    st.session_state.saved = False
    st.session_state.completed = False
    st.session_state.show_result = False
    st.session_state.ended_early = False
    st.session_state.celebrate = False
    st.session_state.evaluate_error = None
    st.session_state.save_error = None
    st.session_state.start_time = now
    st.session_state.question_start_time = now
    st.session_state.interview_data = {
        "name": name.strip(),
        "role": role,
        "difficulty": difficulty,
    }
    st.session_state.started = True
    return True


def run_evaluation(question, answer, index):
    st.session_state.evaluate_error = None
    st.session_state.evaluate_retryable = False

    try:
        result = evaluate_answer(question, answer)
    except GroqConfigError:
        st.session_state.evaluate_error = "AI service is not configured correctly. Please check your settings."
        st.session_state.evaluate_retryable = False
        return False
    except GroqRetryableError:
        st.session_state.evaluate_error = "AI service is temporarily unavailable. Please try again in a moment."
        st.session_state.evaluate_retryable = True
        return False
    except GroqError:
        st.session_state.evaluate_error = "An error occurred while evaluating your answer. Please try again."
        st.session_state.evaluate_retryable = False
        return False

    if len(st.session_state.answers) > index:
        st.session_state.answers[index] = answer
    else:
        st.session_state.answers.append(answer)

    if len(st.session_state.scores) > index:
        st.session_state.scores[index] = result["score"]
    else:
        st.session_state.scores.append(result["score"])

    if len(st.session_state.evaluations) > index:
        st.session_state.evaluations[index] = result
    else:
        st.session_state.evaluations.append(result)

    # Log analytics event for question evaluation
    log_analytics_event(
        session_id=st.session_state.get("session_uuid") or "anon",
        event_type="question_answered",
        question_number=index + 1,
        score=result.get("score"),
    )

    return True


def render_feedback(result, is_last):
    st.divider()
    st.markdown('<h3 class="sub-gradient-title">📊 AI Feedback & Evaluation</h3>', unsafe_allow_html=True)

    acc = result.get("accuracy", "—")
    tech = result.get("technical_depth", "—")
    comm = result.get("communication", "—")
    score = result.get("score", 0)

    # HTML Glowing Badges Row
    badges_html = f"""
    <div style="margin-top: 10px; margin-bottom: 20px;">
        {get_pill_badge(f"Score: {score}/100", score=score)}
        {get_pill_badge(f"Accuracy: {acc}", variant="indigo")}
        {get_pill_badge(f"Depth: {tech}", variant="purple")}
        {get_pill_badge(f"Comm: {comm}", variant="indigo")}
    </div>
    """
    st.markdown(badges_html, unsafe_allow_html=True)

    st.write("### 🔍 Missing Points")
    missing = result.get("missing_points", [])
    if missing:
        for point in missing:
            st.write(f"• {point}")
    else:
        st.success("No missing key points identified 🎉")

    st.write("### 💬 Detailed AI Feedback")
    st.success(result.get("feedback", "No feedback provided."))

    # ── Model Explanation Panel ──────────────────────────────────────────────
    explanation = result.get("model_explanation", "")
    if explanation and explanation not in ("No model explanation available.", ""):
        st.divider()
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(59,130,246,0.08) 100%);
                border: 1px solid rgba(16,185,129,0.25);
                border-left: 4px solid #10B981;
                border-radius: 14px;
                padding: 20px 24px;
                margin-top: 8px;
            ">
                <p style="color:#34D399; font-weight:700; font-size:1.05rem; margin:0 0 10px 0;">📖 Model Answer & Explanation</p>
                <p style="color:#CBD5E1; font-size:0.85rem; margin:0 0 12px 0; font-style:italic;">
                    Study this ideal explanation to strengthen your understanding for next time.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(explanation)

    if is_last:
        st.info("✅ Final answer locked. Click **Finish Interview** to save and view your full report.")
    else:
        st.info("✅ Answer locked. Click **Next Question** to continue.")


def render_results():
    data = st.session_state.interview_data
    scores = st.session_state.scores
    attempted = len(scores)
    average = st.session_state.average_score
    if attempted and not average:
        average = sum(scores) / attempted

    st.markdown('<h2 class="gradient-title">📊 Interview Performance Summary</h2>', unsafe_allow_html=True)

    if st.session_state.celebrate:
        st.balloons()
        st.session_state.celebrate = False

    if st.session_state.ended_early:
        st.warning("⚠️ This interview was ended early. Only answered questions were saved.")

    if st.session_state.saved:
        st.success("✅ Interview saved to history successfully.")
    elif st.session_state.save_error:
        st.error(st.session_state.save_error)
        if st.button("Retry Saving Record", key="retry_save_results"):
            if persist_current_interview(ended_early=st.session_state.ended_early):
                st.rerun()

    # Metrics Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Score", f"{average:.1f}/100")
    with col2:
        st.metric("Questions Answered", f"{attempted} / {st.session_state.total_questions}")
    with col3:
        dur = st.session_state.duration_seconds
        mins, secs = divmod(dur, 60)
        st.metric("Total Duration", f"{mins}m {secs}s" if dur else "—")
    with col4:
        st.metric("Candidate", data.get("name", "—"))

    st.divider()

    if attempted > 0:
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))

        c_str1, c_str2 = st.columns(2)
        with c_str1:
            st.success(f"💪 **Strongest Question (#{best_idx + 1}):** Score {scores[best_idx]}/100")
            st.caption(st.session_state.questions[best_idx])
        with c_str2:
            if min(scores) < 80:
                st.warning(f"⚠️ **Area for Improvement (#{worst_idx + 1}):** Score {scores[worst_idx]}/100")
                st.caption(st.session_state.questions[worst_idx])
            else:
                st.success("🌟 Solid performance across all questions!")

    st.divider()

    st.subheader("📝 Question & Answer Breakdown")
    for i, ans in enumerate(st.session_state.answers):
        with st.expander(f"Question {i + 1}: Score {scores[i]}/100"):
            st.write("**Question:**")
            st.write(st.session_state.questions[i])
            st.write("**Your Answer:**")
            st.info(ans)
            if i < len(st.session_state.evaluations):
                ev = st.session_state.evaluations[i]
                st.write("**Ratings:**")
                st.write(f"- Accuracy: `{ev.get('accuracy', '—')}` | Depth: `{ev.get('technical_depth', '—')}` | Comm: `{ev.get('communication', '—')}`")
                st.write("**Feedback:**")
                st.write(ev.get("feedback", ""))

    st.divider()
    if st.button("🔄 Start New Interview", key="start_new_interview", use_container_width=True):
        reset_to_setup()
        st.rerun()


def render_sidebar_panel():
    if not st.session_state.started:
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("⏱️ Live Status")

    curr = st.session_state.current_question + 1
    total = st.session_state.total_questions
    st.sidebar.write(f"**Progress:** Question {curr} of {total}")

    # Robust running average calculation: filters out any non-numeric or None values
    raw_scores = st.session_state.get("scores", [])
    valid_scores = [
        float(s) for s in raw_scores 
        if s is not None and isinstance(s, (int, float))
    ]

    if valid_scores:
        running_avg = sum(valid_scores) / len(valid_scores)
        st.sidebar.metric(
            label="Running Average",
            value=f"{running_avg:.1f}/100",
            help=f"Based on {len(valid_scores)} answered question(s)"
        )
    else:
        st.sidebar.metric(
            label="Running Average",
            value="—",
            help="Submit your first answer to see your running score"
        )

    # Live-updating stopwatch timer via client-side JS (no page flicker/rerun lag)
    start_ts = st.session_state.get("start_time")
    if start_ts:
        render_live_timer(start_ts)
    else:
        st.sidebar.write("**Total Time:** `00:00`")


def render_setup():
    settings = load_settings()
    roles_list = get_all_roles()

    default_role = settings.get("default_role", "Python Developer")
    role_idx = roles_list.index(default_role) if default_role in roles_list else 0

    diff_list = ["Easy", "Medium", "Hard"]
    default_diff = settings.get("default_difficulty", "Medium")
    diff_idx = diff_list.index(default_diff) if default_diff in diff_list else 1

    default_count = int(settings.get("default_question_count", 5))

    name = st.text_input("Your Name", key="setup_name", placeholder="e.g. Alex Johnson")
    role = st.selectbox("Role", roles_list, index=role_idx, key="setup_role")
    difficulty = st.selectbox("Difficulty", diff_list, index=diff_idx, key="setup_difficulty")
    requested = st.slider("Number of Questions", 3, 15, default_count, key="setup_total")

    c_gen1, c_gen2 = st.columns([3, 1])
    with c_gen1:
        start_clicked = st.button("🚀 Start Interview", key="start_interview", use_container_width=True)
    with c_gen2:
        regen_clicked = st.button("🔄 Regenerate", help="Bypass cache & generate fresh questions", use_container_width=True)

    if st.session_state.generate_error:
        retry = show_api_error(
            st.session_state.generate_error,
            st.session_state.generate_retryable,
            "🔄 Retry generating questions",
            "retry_generate",
        )
        if retry:
            if not (name or "").strip():
                st.error("Please enter your name to proceed.")
            else:
                with st.spinner("Generating your interview questions..."):
                    ok = begin_interview(name, role, difficulty, requested, bypass_cache=True)
                if ok:
                    st.rerun()

    if start_clicked or regen_clicked:
        if not (name or "").strip():
            st.error("Please enter your name to proceed.")
        else:
            with st.spinner("Generating your interview questions..."):
                ok = begin_interview(name, role, difficulty, requested, bypass_cache=regen_clicked)
            if ok:
                st.rerun()


def _attempt_transcription(current, audio_bytes, settings):
    """
    Transcribe `audio_bytes` for question `current` and, on success, merge the
    result into the answer textarea's session_state (Append/Replace per the
    per-question voice mode), then rerun so it renders immediately. On
    failure, store an error + retryable flag for the UI and leave any text the
    user already typed completely untouched.
    """
    answer_key = f"answer_{current}"
    error_key = f"voice_error_{current}"
    retryable_key = f"voice_retryable_{current}"
    mode_key = f"voice_mode_{current}"

    with st.spinner("Transcribing..."):
        try:
            text = transcribe_audio(audio_bytes, language="en")
        except GroqConfigError:
            st.session_state[error_key] = "AI service is not configured correctly. Please check your settings."
            st.session_state[retryable_key] = False
            return
        except GroqRetryableError:
            st.session_state[error_key] = "Transcription service is temporarily unavailable. Please try again."
            st.session_state[retryable_key] = True
            return
        except GroqError:
            st.session_state[error_key] = "An error occurred during transcription. Please try again."
            st.session_state[retryable_key] = False
            return
        except Exception as exc:  # noqa: BLE001 - never let a raw traceback reach the UI
            # Log full traceback to server console for debugging
            print("[Transcription] Unexpected error:")
            traceback.print_exc()
            st.session_state[error_key] = "An unexpected error occurred during transcription. Please try again."
            st.session_state[retryable_key] = True
            return

    mode = st.session_state.get(mode_key) or settings.get("default_voice_mode", "Append")
    existing = (st.session_state.get(answer_key) or "").strip()
    if mode == "Append" and existing:
        st.session_state[answer_key] = f"{existing} {text}".strip()
    else:
        st.session_state[answer_key] = text

    st.session_state[error_key] = None
    st.session_state[retryable_key] = False
    st.rerun()


def _process_voice_recording(current, settings):
    """
    Detect a new (not-yet-processed) audio recording for `current` and kick off
    transcription, and apply any deferred "Clear answer" request.

    CRITICAL STREAMLIT DETAIL: a widget's session_state value cannot be
    reassigned after that widget has already been instantiated in the same
    script run. The answer textarea is bound to session_state[f"answer_{i}"],
    so any code that wants to change the answer text (a fresh transcript, or
    the Clear-answer action) must run and finish mutating that key BEFORE
    st.text_area(key=f"answer_{i}", ...) is called later in this same run.
    That's why this function is called first, and why it only ever *reads*
    st.session_state[f"audio_{i}"] (the audio_input widget's own state,
    already populated by Streamlit before the script starts) rather than
    rendering the audio_input widget itself — the widget is drawn later, in
    render_voice_block(), to preserve the required visual layout order.
    """
    answer_key = f"answer_{current}"
    audio_key = f"audio_{current}"
    hash_key = f"voice_hash_{current}"
    clear_pending_key = f"voice_clear_pending_{current}"

    if st.session_state.get(clear_pending_key):
        st.session_state[answer_key] = ""
        _clear_voice_state_for(current)
        return

    if not hasattr(st, "audio_input"):
        return

    audio_value = st.session_state.get(audio_key)
    if audio_value is None:
        return

    try:
        raw_bytes = audio_value.getvalue()
    except AttributeError:
        raw_bytes = audio_value.read()

    if not raw_bytes:
        return

    new_hash = hashlib.sha256(raw_bytes).hexdigest()
    if st.session_state.get(hash_key) == new_hash:
        return  # Same recording already handled - never transcribe twice across reruns.

    # Mark as seen immediately so a failed attempt doesn't re-trigger on every
    # rerun; the "Retry transcription" button re-attempts these same bytes.
    st.session_state[hash_key] = new_hash
    st.session_state[f"voice_pending_bytes_{current}"] = raw_bytes
    _attempt_transcription(current, raw_bytes, settings)


def render_voice_block(current, already_evaluated, settings):
    """
    Compact voice-recording block rendered directly below the answer textarea.
    Uses st.audio_input (Streamlit native widget) for recording.
    Server-side transcription — no browser API needed, works everywhere.
    Hidden once the answer is locked/evaluated.
    """
    if already_evaluated:
        return

    if not settings.get("enable_voice_answers", True):
        return

    if not hasattr(st, "audio_input"):
        st.caption("🎙️ Voice answers need Streamlit ≥ 1.23 — typing works as usual.")
        return

    audio_key = f"audio_{current}"
    mode_key = f"voice_mode_{current}"
    error_key = f"voice_error_{current}"
    retryable_key = f"voice_retryable_{current}"
    clear_key = f"voice_clear_pending_{current}"

    default_mode = settings.get("default_voice_mode", "Append")
    mode_options = ["Append", "Replace"]
    default_idx = mode_options.index(default_mode) if default_mode in mode_options else 0

    st.markdown('<div class="voice-recorder-block">', unsafe_allow_html=True)

    # Header row
    st.markdown(
        '<p class="voice-recorder-caption">'
        '🎙️ Or speak your answer — recorded audio is transcribed automatically'
        '</p>',
        unsafe_allow_html=True,
    )

    # How-to note
    st.markdown(
        '<p style="color:#64748B; font-size:0.78rem; margin:-2px 0 8px 0;">'
        '① Press the mic button below to start recording &nbsp;'
        '② Speak your answer &nbsp;'
        '③ Press stop — text appears in the answer box above &nbsp;'
        '④ Edit if needed, then click Submit'
        '</p>',
        unsafe_allow_html=True,
    )

    # Pulsing indicator style
    st.markdown("""
        <style>
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        .pulsing-dot {
            height: 10px; width: 10px; background-color: #ef4444; border-radius: 50%;
            display: inline-block; animation: pulse 1.5s infinite; margin-right: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.audio_input("Record your answer", key=audio_key, label_visibility="collapsed")

    c1, c2 = st.columns([3, 1])
    with c1:
        st.radio(
            "Transcription mode",
            mode_options,
            index=default_idx,
            key=mode_key,
            horizontal=True,
            label_visibility="collapsed",
            help="**Append** adds new recording to existing text. **Replace** overwrites it.",
        )
    with c2:
        if st.button("🧹 Clear", key=f"clear_btn_{current}", use_container_width=True,
                     help="Clear the answer box"):
            st.session_state[clear_key] = True
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get(error_key):
        retryable = bool(st.session_state.get(retryable_key))
        retry = show_api_error(
            st.session_state[error_key],
            retryable,
            "🔄 Retry transcription",
            f"retry_transcribe_{current}",
        )
        if retry:
            pending = st.session_state.get(f"voice_pending_bytes_{current}")
            if pending:
                _attempt_transcription(current, pending, settings)


def render_interview():
    render_sidebar_panel()

    questions = st.session_state.questions
    total = len(questions)
    st.session_state.total_questions = total

    if total == 0:
        st.error("No questions available. Returning to setup.")
        reset_to_setup()
        st.rerun()

    current = st.session_state.current_question
    current = max(0, min(current, total - 1))
    st.session_state.current_question = current
    is_last = current == total - 1

    if st.session_state.fewer_questions_notice:
        st.info(f"The AI provided {total} calibrated question(s) for your session.")

    st.progress((current + 1) / total)

    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        st.write(f"### Question {current + 1} of {total}")
    with col2:
        if st.button("🔄 Restart", key="restart_interview"):
            st.session_state.confirm_restart = True
            st.session_state.confirm_end = False
    with col3:
        if st.button("❌ End Early", key="end_interview"):
            st.session_state.confirm_end = True
            st.session_state.confirm_restart = False

    settings = load_settings()
    if settings.get("enable_question_timer", False):
        if st.session_state.question_start_time:
            q_elapsed = int(time.time() - st.session_state.question_start_time)
            q_mins, q_secs = divmod(q_elapsed, 60)
            st.caption(f"⏱️ Time on this question: `{q_mins:02d}:{q_secs:02d}` (Informational)")

    if st.session_state.confirm_restart:
        st.warning("⚠️ Restarting will discard all current progress.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, Restart", key="confirm_restart_yes"):
                reset_to_setup()
                st.rerun()
        with c2:
            if st.button("❌ Cancel", key="confirm_restart_no"):
                st.session_state.confirm_restart = False
                st.rerun()

    if st.session_state.confirm_end:
        attempted = len(st.session_state.evaluations)
        if attempted:
            st.error(f"⚠️ End interview now? {attempted} answered question(s) will be saved.")
        else:
            st.error("⚠️ End interview now? No questions answered yet, nothing will be saved.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, End & Save", key="confirm_end_yes"):
                if attempted:
                    persist_current_interview(ended_early=True)
                    go_to_results(ended_early=True)
                else:
                    reset_to_setup()
                st.rerun()
        with c2:
            if st.button("❌ Cancel", key="confirm_end_no"):
                st.session_state.confirm_end = False
                st.rerun()

    # Glassmorphic Question Box
    current_q_text = questions[current]
    st.markdown(
        f"""
        <div class="glass-card">
            <h3 style="color: #F8FAFC; font-size: 1.35rem; font-weight: 700; margin-bottom: 0px;">
                {current_q_text}
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # HTML5 Text-to-Speech Playback Button
    render_tts_button(current_q_text, button_key=f"q_{current}")

    already_evaluated = len(st.session_state.evaluations) > current

    # Must run BEFORE st.text_area() below — see docstring on
    # _process_voice_recording for why.
    if not already_evaluated:
        _process_voice_recording(current, settings)

    answer = st.text_area(
        "Write your technical answer below:",
        key=f"answer_{current}",
        height=200,
        disabled=already_evaluated,
        placeholder="Provide a detailed explanation including concepts, code snippets, or architecture trade-offs...",
    )

    if not already_evaluated and answer and len(answer.strip()) < 20:
        st.caption("⚠️ *Answer is quite brief (< 20 characters). Elaborating further will improve your score.*")

    # Voice recorder — placed BELOW textarea for clean visual flow
    render_voice_block(current, already_evaluated, settings)

    if st.session_state.evaluate_error:
        retry = show_api_error(
            st.session_state.evaluate_error,
            st.session_state.evaluate_retryable,
            "🔄 Retry Evaluation",
            "retry_evaluate",
        )
        if retry and (answer or "").strip():
            with st.spinner("AI is evaluating your answer..."):
                ok = run_evaluation(questions[current], answer.strip(), current)
            if ok:
                st.rerun()

    if not already_evaluated:
        if st.button("✅ Submit Answer", key=f"submit_{current}", use_container_width=True):
            if not (answer or "").strip():
                st.warning("Please enter your answer before submitting.")
            else:
                with st.spinner("AI is evaluating your answer..."):
                    ok = run_evaluation(questions[current], answer.strip(), current)
                if ok:
                    st.rerun()

    if already_evaluated:
        render_feedback(st.session_state.evaluations[current], is_last)
        st.divider()

        finish_label = "🏁 Finish Interview" if is_last else "➡️ Next Question"
        if st.button(finish_label, key=f"advance_{current}", use_container_width=True):
            if is_last:
                persist_current_interview(ended_early=False)
                st.session_state.celebrate = True
                go_to_results(ended_early=False)
                st.rerun()
            else:
                st.session_state.current_question = current + 1
                st.session_state.question_start_time = time.time()
                st.session_state.evaluate_error = None
                _clear_voice_state_for(current)
                st.rerun()


# Page router
_init_state()

if st.session_state.completed or st.session_state.show_result:
    render_results()
elif not st.session_state.started:
    render_setup()
else:
    render_interview()
