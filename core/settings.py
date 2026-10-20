"""
Settings management module for AI Interview Simulator.
Handles reading and writing local configuration to settings.json safely.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

BUILTIN_ROLES = [
    "Python Developer",
    "Java Developer",
    "Full Stack Developer",
    "AI Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Data Scientist",
    "DevOps Engineer",
]

DEFAULT_SETTINGS = {
    "default_role": "Python Developer",
    "default_difficulty": "Medium",
    "default_question_count": 5,
    "enable_question_timer": False,
    "groq_model": "openai/gpt-oss-120b",
    "custom_roles": [],
    "whisper_model": "whisper-large-v3-turbo",
    "enable_voice_answers": True,
    "default_voice_mode": "Append",
    "app_theme": "Dark",
}


def load_settings():
    """
    Load settings from settings.json.
    Falls back to default settings if file is missing or corrupted.
    """
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()

        # Merge with defaults to ensure all keys exist
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        if not isinstance(merged.get("custom_roles"), list):
            merged["custom_roles"] = []
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """
    Save a settings dict to settings.json safely.
    Returns True on success, False on failure.
    """
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False


def get_all_roles():
    """
    Get combined list of built-in and custom user roles.
    """
    settings = load_settings()
    custom = settings.get("custom_roles", [])
    roles = list(BUILTIN_ROLES)
    for r in custom:
        if isinstance(r, str) and r.strip() and r.strip() not in roles:
            roles.append(r.strip())
    return roles
