"""
UI Theme & CSS Design System for AI Interview Simulator.
Provides glassmorphism styling, gradient typography, glowing pill badges,
Plotly chart styling, and HTML5 Text-to-Speech audio support.
"""

import streamlit as st


def inject_custom_css():
    """
    Inject global custom CSS into the Streamlit app.
    Applies modern glassmorphism, gradient buttons, custom fonts,
    and responsive dark theme refinements.
    """
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

    /* Global Typography & Font Settings */
    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Animated Gradient Headers */
    .gradient-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 40%, #EC4899 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem !important;
    }

    .sub-gradient-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    /* Glassmorphism Card Containers */
    .glass-card {
        background: rgba(17, 24, 39, 0.65) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
        transition: transform 0.25s ease, border-color 0.25s ease !important;
    }

    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Streamlit Metric Container Styling */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        border-color: rgba(129, 140, 248, 0.4) !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2) !important;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #94A3B8 !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #F8FAFC !important;
        font-size: 1.8rem !important;
    }

    /* Enhanced Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.35) !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.01) !important;
        background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%) !important;
        box-shadow: 0 8px 25px 0 rgba(124, 58, 237, 0.5) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    div.stButton > button:active {
        transform: translateY(0) scale(0.99) !important;
    }

    /* Page Link Buttons */
    div[data-testid="stPageLink"] a {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 12px 18px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stPageLink"] a:hover {
        background: rgba(79, 70, 229, 0.25) !important;
        border-color: rgba(129, 140, 248, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* Glowing Score Pill Badges */
    .pill-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin-right: 8px;
        margin-bottom: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }

    .pill-emerald {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }

    .pill-amber {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
    }

    .pill-rose {
        background: rgba(244, 63, 94, 0.15);
        color: #FB7185;
        border: 1px solid rgba(244, 63, 94, 0.35);
        box-shadow: 0 0 12px rgba(244, 63, 94, 0.2);
    }

    .pill-indigo {
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
    }

    .pill-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.35);
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.2);
    }

    /* Input & Text Area Customization */
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #818CF8 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Sidebar Refinements */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Progress bar fill */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366F1 0%, #A855F7 50%, #EC4899 100%) !important;
        border-radius: 10px !important;
    }

    /* Hide Streamlit UI elements */
    [data-testid="stToolbar"],
    [data-testid="stMainMenu"],
    #MainMenu,
    [data-testid="stAppDeployButton"],
    [data-testid="stDecoration"],
    footer {
        display:none !important;
        visibility:hidden !important;
    }
    </style>
    """
    try:
        from core.settings import load_settings
        current_theme = load_settings().get("app_theme", "Dark")
    except Exception:
        current_theme = "Dark"

    if current_theme == "Light":
        light_css = """
        <style>
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        section[data-testid="stSidebar"] {
            background: rgba(241, 245, 249, 0.95) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.85) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
        }
        div[data-testid="stMetric"] {
            background: rgba(241, 245, 249, 0.75) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #475569 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0F172A !important;
        }
        .stTextArea textarea, .stTextInput input, .stSelectbox select {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(0, 0, 0, 0.15) !important;
            color: #0F172A !important;
        }
        </style>
        """
        css += light_css

    st.markdown(css, unsafe_allow_html=True)


def get_pill_badge(label, score=None, variant=None):
    """
    Generate an HTML pill badge string.
    Automatically assigns emerald/amber/rose based on score if variant not provided.
    """
    if variant is None:
        if score is not None:
            val = float(score)
            if val >= 75:
                variant = "emerald"
            elif val >= 50:
                variant = "amber"
            else:
                variant = "rose"
        else:
            variant = "indigo"

    return f'<span class="pill-badge pill-{variant}">{label}</span>'


def apply_plotly_theme(fig):
    """
    Apply dark glassmorphism layout, glowing lines, and custom fonts to Plotly figures.
    """
    fig.update_layout(
        paper_bgcolor="rgba(15, 23, 42, 0.0)",
        plot_bgcolor="rgba(15, 23, 42, 0.0)",
        font=dict(
            family="Plus Jakarta Sans, sans-serif",
            color="#94A3B8",
            size=12,
        ),
        title=dict(
            font=dict(color="#F8FAFC", size=16, family="Plus Jakarta Sans"),
            x=0.0,
        ),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            zerolinecolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(color="#94A3B8"),
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.06)",
            zerolinecolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(color="#94A3B8"),
        ),
        legend=dict(
            font=dict(color="#F8FAFC"),
            bgcolor="rgba(15, 23, 42, 0.6)",
            bordercolor="rgba(255, 255, 255, 0.1)",
        ),
    )
    return fig


def render_tts_button(text_to_speak, button_key="tts_btn"):
    """
    Render a Text-To-Speech (TTS) button powered by the Web Speech API.
    Uses st.components.v1.html to ensure the JavaScript executes in an isolated,
    fully-featured iframe with guaranteed script execution on all renders.
    """
    clean_text = (
        text_to_speak.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700&display=swap');
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            overflow: hidden;
        }}
        .tts-container {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 2px;
        }}
        .tts-btn {{
            background: rgba(99, 102, 241, 0.18);
            color: #A5B4FC;
            border: 1px solid rgba(129, 140, 248, 0.45);
            border-radius: 10px;
            padding: 8px 18px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 0.92rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
            outline: none;
            user-select: none;
        }}
        .tts-btn:hover {{
            background: rgba(99, 102, 241, 0.28);
            border-color: rgba(165, 180, 252, 0.6);
            color: #C7D2FE;
            transform: translateY(-1px);
        }}
        .tts-btn.speaking {{
            background: rgba(244, 63, 94, 0.22);
            border-color: rgba(244, 63, 94, 0.6);
            color: #FDA4AF;
        }}
        .tts-indicator {{
            display: none;
            color: #38BDF8;
            font-size: 0.85rem;
            font-weight: 500;
            align-items: center;
            gap: 6px;
        }}
        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: #38BDF8;
            border-radius: 50%;
            animation: pulseAnim 1.2s infinite ease-in-out;
        }}
        @keyframes pulseAnim {{
            0% {{ transform: scale(0.85); opacity: 0.4; }}
            50% {{ transform: scale(1.3); opacity: 1; }}
            100% {{ transform: scale(0.85); opacity: 0.4; }}
        }}
    </style>
    </head>
    <body>
        <div class="tts-container">
            <button id="tts-btn" class="tts-btn" onclick="handleTTSClick()">
                <span id="tts-icon">🔊</span>
                <span id="tts-label">Listen to Question</span>
            </button>
            <span id="tts-indicator" class="tts-indicator">
                <span class="pulse-dot"></span>
                Speaking...
            </span>
        </div>

    <script>
        const textToSpeak = "{clean_text}";
        let isSpeaking = false;
        let cachedVoices = [];

        function getSynth() {{
            return window.speechSynthesis || (window.parent && window.parent.speechSynthesis) || null;
        }}

        function loadVoices() {{
            const synth = getSynth();
            if (!synth) return [];
            let v = synth.getVoices();
            if (v && v.length > 0) {{
                cachedVoices = v;
            }}
            return cachedVoices;
        }}

        const synth = getSynth();
        if (synth) {{
            loadVoices();
            if (synth.onvoiceschanged !== undefined) {{
                synth.onvoiceschanged = loadVoices;
            }}
        }}

        function pickFemaleVoice() {{
            const voices = loadVoices();
            if (!voices || voices.length === 0) return null;

            // Preferred high-quality natural female voices across OS/browsers
            const preferredNames = [
                "samantha", "victoria", "karen", "moira", "tessa", "zira",
                "google uk english female", "google us english female",
                "microsoft zira", "microsoft jenny", "natural", "female"
            ];

            // 1. Search for preferred English female voice
            for (const pref of preferredNames) {{
                const match = voices.find(v => 
                    v.name.toLowerCase().includes(pref) && v.lang.toLowerCase().startsWith("en")
                );
                if (match) return match;
            }}

            // 2. Search for any voice with female/woman keyword
            const genericFemale = voices.find(v => 
                v.name.toLowerCase().includes("female") || 
                v.name.toLowerCase().includes("woman")
            );
            if (genericFemale) return genericFemale;

            // 3. Any English voice
            const enVoice = voices.find(v => v.lang.toLowerCase().startsWith("en"));
            if (enVoice) return enVoice;

            return voices[0] || null;
        }}

        function updateUI(speaking) {{
            isSpeaking = speaking;
            const btn = document.getElementById('tts-btn');
            const icon = document.getElementById('tts-icon');
            const label = document.getElementById('tts-label');
            const indicator = document.getElementById('tts-indicator');

            if (speaking) {{
                btn.classList.add('speaking');
                icon.innerText = '⏹️';
                label.innerText = 'Stop Audio';
                indicator.style.display = 'inline-flex';
            }} else {{
                btn.classList.remove('speaking');
                icon.innerText = '🔊';
                label.innerText = 'Listen to Question';
                indicator.style.display = 'none';
            }}
        }}

        function handleTTSClick() {{
            const synth = getSynth();
            if (!synth) {{
                alert("Text-to-speech is not supported by your browser.");
                return;
            }}

            if (isSpeaking || synth.speaking) {{
                synth.cancel();
                updateUI(false);
                return;
            }}

            synth.cancel();

            // Direct synchronous invocation inside click handler ensures no autoplay block
            const utterance = new SpeechSynthesisUtterance(textToSpeak);
            utterance.rate = 0.95;
            utterance.pitch = 1.05;

            const voice = pickFemaleVoice();
            if (voice) {{
                utterance.voice = voice;
            }}

            utterance.onstart = function() {{
                updateUI(true);
            }};

            utterance.onend = function() {{
                updateUI(false);
            }};

            utterance.onerror = function(event) {{
                console.warn("TTS Playback issue:", event);
                updateUI(false);
            }};

            synth.speak(utterance);
        }}
    </script>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=52)


def render_voice_recorder_css():
    """
    Inject minimal, subtle CSS so the native st.audio_input recorder block sits
    neatly under the answer textarea. No JavaScript — the recorder itself is a
    real Streamlit widget (server-side transcription happens in core.speech).
    """
    css = """
    <style>
    .voice-recorder-block {
        background: rgba(17, 24, 39, 0.55);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 14px;
        padding: 14px 18px 4px 18px;
        margin-top: 10px;
        margin-bottom: 6px;
    }
    .voice-recorder-caption {
        color: #C084FC;
        font-size: 0.85rem;
        font-weight: 600;
        font-family: 'Plus Jakarta Sans', sans-serif;
        margin-bottom: 6px;
    }
    div[data-testid="stAudioInput"] {
        border-radius: 12px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_live_timer(start_timestamp: float):
    """
    Render a live-updating stopwatch using client-side JavaScript.
    Counts continuously from `start_timestamp` (epoch seconds) without requiring
    Streamlit Python reruns. Renders neatly inside the sidebar.
    """
    html_code = f"""
    <div id="live-timer-container" style="
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 10px 0 14px 0;
        display: flex;
        flex-direction: column;
        gap: 4px;
    ">
        <span style="color: #94A3B8; font-size: 0.82rem; font-weight: 600; font-family: 'Plus Jakarta Sans', sans-serif; display: flex; align-items: center; gap: 6px;">
            <span style="display:inline-block; width:7px; height:7px; background-color:#10B981; border-radius:50%; animation: liveDot 1.4s infinite ease-in-out;"></span>
            Total Time (Live)
        </span>
        <span id="live-timer-display" style="
            color: #F8FAFC;
            font-size: 1.5rem;
            font-weight: 800;
            font-family: 'Plus Jakarta Sans', monospace, sans-serif;
            letter-spacing: 0.04em;
        ">00:00</span>
    </div>

    <style>
    @keyframes liveDot {{
        0% {{ opacity: 0.3; transform: scale(0.85); }}
        50% {{ opacity: 1; transform: scale(1.2); }}
        100% {{ opacity: 0.3; transform: scale(0.85); }}
    }}
    </style>

    <script>
    (function() {{
        const startSec = {float(start_timestamp)};
        function updateTimer() {{
            const nowSec = Date.now() / 1000;
            let elapsed = Math.max(0, Math.floor(nowSec - startSec));
            
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            let displayStr = "";
            if (hours > 0) {{
                displayStr = String(hours).padStart(2, '0') + ":" + 
                             String(minutes).padStart(2, '0') + ":" + 
                             String(seconds).padStart(2, '0');
            }} else {{
                displayStr = String(minutes).padStart(2, '0') + ":" + 
                             String(seconds).padStart(2, '0');
            }}
            
            const el = document.getElementById('live-timer-display');
            if (el) {{
                el.innerText = displayStr;
            }}
        }}

        updateTimer();
        if (window._liveTimerInterval) {{
            clearInterval(window._liveTimerInterval);
        }}
        window._liveTimerInterval = setInterval(updateTimer, 1000);
    }})();
    </script>
    """
    st.components.v1.html(html_code, height=90)




