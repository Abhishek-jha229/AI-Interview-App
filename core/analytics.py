"""
Analytics database module for AI Interview Simulator.
Handles tracking usage metrics into a local SQLite database (analytics.db).
Data is stored securely and accessible only from the owner-authenticated Settings page.
"""

from datetime import datetime
import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS_DB_PATH = os.path.join(BASE_DIR, "analytics.db")


def get_analytics_connection():
    """Create a connection to the analytics SQLite database."""
    conn = sqlite3.connect(ANALYTICS_DB_PATH)
    return conn


def init_analytics_db():
    """Initialize the analytics database schema."""
    try:
        with get_analytics_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                question_number INTEGER,
                score REAL,
                total_time_taken INTEGER
            );
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_timestamp 
            ON usage_analytics(timestamp);
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_session 
            ON usage_analytics(session_id);
            """)
            conn.commit()
    except Exception:
        pass


def log_analytics_event(session_id: str, event_type: str, question_number: int = None, score: float = None, total_time_taken: int = None):
    """Safely log an analytics event in the background."""
    try:
        init_analytics_db()
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_analytics_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO usage_analytics (
                session_id, timestamp, event_type, question_number, score, total_time_taken
            ) VALUES (?, ?, ?, ?, ?, ?);
            """, (session_id, now_iso, event_type, question_number, score, total_time_taken))
            conn.commit()
    except Exception:
        pass


def get_analytics_summary():
    """Retrieve summarized analytics metrics and recent events for owner reporting."""
    init_analytics_db()
    try:
        with get_analytics_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM usage_analytics;")
            total_sessions = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM usage_analytics WHERE event_type = 'question_answered';")
            total_questions = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(score) FROM usage_analytics WHERE score IS NOT NULL;")
            avg_score_row = cursor.fetchone()[0]
            avg_score = float(avg_score_row) if avg_score_row is not None else 0.0
            
            df_recent = pd.read_sql_query("""
                SELECT timestamp, event_type, question_number, score, total_time_taken, session_id
                FROM usage_analytics
                ORDER BY id DESC
                LIMIT 50;
            """, conn)
            
            df_daily = pd.read_sql_query("""
                SELECT substr(timestamp, 1, 10) as date, COUNT(DISTINCT session_id) as session_count
                FROM usage_analytics
                GROUP BY substr(timestamp, 1, 10)
                ORDER BY date ASC;
            """, conn)
            
            return {
                "total_sessions": total_sessions,
                "total_questions": total_questions,
                "avg_score": avg_score,
                "recent_df": df_recent,
                "daily_df": df_daily,
            }
    except Exception:
        return {
            "total_sessions": 0,
            "total_questions": 0,
            "avg_score": 0.0,
            "recent_df": pd.DataFrame(),
            "daily_df": pd.DataFrame(),
        }
