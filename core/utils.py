"""
Utility helper functions for AI Interview Simulator.
Provides score badge generation, time formatting, and text helpers.
"""


def get_score_badge(score):
    """
    Return a color-coded emoji badge based on score.
    Green >= 75, Amber 50-74, Red < 50.
    """
    if score is None:
        return "⚪ —"
    score = float(score)
    if score >= 75:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"


def format_duration(seconds):
    """
    Format duration in seconds into a human-readable MM:SS or HH:MM:SS string.
    """
    if not seconds or not isinstance(seconds, (int, float)):
        return "—"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins:02d}m {secs:02d}s"
    return f"{mins}m {secs:02d}s"
