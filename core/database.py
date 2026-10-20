"""
Database layer for AI Interview Simulator.
Handles SQLite connection lifecycle, schema migrations, and queries safely.
"""

from datetime import datetime
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "interview.db")


def get_connection():
    """
    Connect to SQLite database with foreign keys enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables():
    """
    Create tables and execute safe migrations for existing databases.
    Applies indexes for performant querying.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Base table: interviews
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                role TEXT,
                difficulty TEXT,
                average_score REAL,
                total_questions INTEGER,
                interview_date TEXT,
                status TEXT DEFAULT 'completed',
                duration_seconds INTEGER NULL
            );
            """)

            # Base table: interview_details
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER,
                question TEXT,
                answer TEXT,
                score REAL,
                feedback TEXT,
                accuracy TEXT,
                technical_depth TEXT,
                communication TEXT,
                missing_points TEXT,
                model_explanation TEXT,
                FOREIGN KEY(interview_id) REFERENCES interviews(id) ON DELETE CASCADE
            );
            """)

            # Migration check for interviews
            cursor.execute("PRAGMA table_info(interviews);")
            interview_cols = [row[1] for row in cursor.fetchall()]

            if "status" not in interview_cols:
                cursor.execute(
                    "ALTER TABLE interviews ADD COLUMN status TEXT DEFAULT 'completed';"
                )
            if "duration_seconds" not in interview_cols:
                cursor.execute(
                    "ALTER TABLE interviews ADD COLUMN duration_seconds INTEGER NULL;"
                )

            # Migration check for interview_details
            cursor.execute("PRAGMA table_info(interview_details);")
            detail_cols = [row[1] for row in cursor.fetchall()]

            if "accuracy" not in detail_cols:
                cursor.execute(
                    "ALTER TABLE interview_details ADD COLUMN accuracy TEXT;"
                )
            if "technical_depth" not in detail_cols:
                cursor.execute(
                    "ALTER TABLE interview_details ADD COLUMN technical_depth TEXT;"
                )
            if "communication" not in detail_cols:
                cursor.execute(
                    "ALTER TABLE interview_details ADD COLUMN communication TEXT;"
                )
            if "missing_points" not in detail_cols:
                cursor.execute(
                    "ALTER TABLE interview_details ADD COLUMN missing_points TEXT;"
                )
            if "model_explanation" not in detail_cols:
                cursor.execute(
                    "ALTER TABLE interview_details ADD COLUMN model_explanation TEXT;"
                )

            # Performance indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_interviews_date ON interviews(interview_date);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_details_interview_id ON interview_details(interview_id);"
            )
            conn.commit()
    except Exception as exc:
        # Never crash module load on DB init
        print(f"Database initialization warning: {exc}")


def save_interview(
    candidate_name,
    role,
    difficulty,
    average_score,
    total_questions,
    status="completed",
    duration_seconds=None,
):
    """
    Save a new interview summary row.
    Returns the integer ID of the created interview.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interviews (
                    candidate_name, role, difficulty, average_score,
                    total_questions, interview_date, status, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    (candidate_name or "").strip(),
                    role,
                    difficulty,
                    float(average_score),
                    int(total_questions),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    status,
                    duration_seconds,
                ),
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as exc:
        raise RuntimeError(f"Failed to save interview record: {exc}") from exc


def save_question_detail(
    interview_id,
    question,
    answer,
    score,
    feedback,
    accuracy=None,
    technical_depth=None,
    communication=None,
    missing_points=None,
    model_explanation=None,
):
    """
    Save evaluation detail for one answered question.
    Converts missing_points list to JSON string if needed.
    Stores model_explanation text for post-answer learning display.
    """
    if isinstance(missing_points, (list, dict)):
        missing_points_str = json.dumps(missing_points)
    else:
        missing_points_str = str(missing_points or "")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO interview_details (
                    interview_id, question, answer, score, feedback,
                    accuracy, technical_depth, communication, missing_points, model_explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    interview_id,
                    question,
                    answer,
                    float(score),
                    feedback,
                    accuracy,
                    technical_depth,
                    communication,
                    missing_points_str,
                    model_explanation,
                ),
            )
            conn.commit()
    except Exception as exc:
        raise RuntimeError(f"Failed to save question evaluation detail: {exc}") from exc


def delete_interview(interview_id):
    """
    Delete an interview by ID.
    Cascade deletes related details if foreign key cascade is active,
    or explicitly deletes details as a fail-safe.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM interview_details WHERE interview_id = ?;", (interview_id,))
            cursor.execute("DELETE FROM interviews WHERE id = ?;", (interview_id,))
            conn.commit()
            return True
    except Exception as exc:
        raise RuntimeError(f"Failed to delete interview #{interview_id}: {exc}") from exc


def clear_all_history():
    """
    Completely wipe all saved interview records and details.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM interview_details;")
            cursor.execute("DELETE FROM interviews;")
            conn.commit()
            return True
    except Exception as exc:
        raise RuntimeError(f"Failed to clear interview history: {exc}") from exc


def get_all_interviews():
    """
    Retrieve all interviews sorted newest first.
    Returns list of dicts.
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interviews ORDER BY id DESC;")
            return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []


def get_interview_details(interview_id):
    """
    Retrieve all detail rows for a given interview ID sorted by ID.
    Parses JSON missing_points into python list cleanly.
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM interview_details WHERE interview_id = ? ORDER BY id;",
                (interview_id,),
            )
            rows = [dict(row) for row in cursor.fetchall()]
            for r in rows:
                mp = r.get("missing_points")
                if mp:
                    try:
                        r["missing_points_parsed"] = json.loads(mp)
                    except Exception:
                        r["missing_points_parsed"] = [mp] if str(mp).strip() else []
                else:
                    r["missing_points_parsed"] = []
            return rows
    except Exception:
        return []


def _build_filter_where(role=None, difficulty=None, date_from=None, date_to=None, candidate_name=None):
    """
    Internal helper to construct WHERE SQL clauses and parameter tuples safely.
    """
    clauses = []
    params = []

    if candidate_name and candidate_name.strip():
        clauses.append("LOWER(candidate_name) LIKE ?")
        params.append(f"%{candidate_name.strip().lower()}%")

    if role and role != "All":
        clauses.append("role = ?")
        params.append(role)

    if difficulty and difficulty != "All":
        clauses.append("difficulty = ?")
        params.append(difficulty)

    if date_from:
        clauses.append("interview_date >= ?")
        params.append(f"{date_from} 00:00:00")

    if date_to:
        clauses.append("interview_date <= ?")
        params.append(f"{date_to} 23:59:59")

    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where_sql, params


def get_interviews_filtered(
    candidate_name=None,
    role=None,
    difficulty=None,
    date_from=None,
    date_to=None,
    sort_by="newest",
):
    """
    Retrieve filtered and sorted interviews list.
    sort_by options: 'newest', 'oldest', 'highest_score', 'lowest_score'
    """
    where_sql, params = _build_filter_where(
        role=role,
        difficulty=difficulty,
        date_from=date_from,
        date_to=date_to,
        candidate_name=candidate_name,
    )

    order_map = {
        "newest": "id DESC",
        "oldest": "id ASC",
        "highest_score": "average_score DESC, id DESC",
        "lowest_score": "average_score ASC, id DESC",
    }
    order_clause = order_map.get(sort_by, "id DESC")

    query = f"SELECT * FROM interviews{where_sql} ORDER BY {order_clause};"

    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []


def get_dashboard_stats(role=None, difficulty=None, date_from=None, date_to=None):
    """
    Compute aggregate dashboard metrics respecting optional filters:
    - total_interviews
    - total_questions_answered
    - average_score
    - highest_score
    - lowest_score
    - last_5_avg
    - prev_5_avg
    """
    where_sql, params = _build_filter_where(
        role=role, difficulty=difficulty, date_from=date_from, date_to=date_to
    )

    empty_result = {
        "total_interviews": 0,
        "total_questions_answered": 0,
        "average_score": 0.0,
        "highest_score": 0.0,
        "lowest_score": 0.0,
        "last_5_avg": None,
        "prev_5_avg": None,
        "improvement_delta": None,
    }

    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Main summary metrics
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS total_interviews,
                    AVG(average_score) AS average_score,
                    MAX(average_score) AS highest_score,
                    MIN(average_score) AS lowest_score
                FROM interviews{where_sql}
            """,
                params,
            )
            row = cursor.fetchone()
            if not row or row["total_interviews"] == 0:
                return empty_result

            total_interviews = row["total_interviews"] or 0
            avg_score = float(row["average_score"]) if row["average_score"] is not None else 0.0
            max_score = float(row["highest_score"]) if row["highest_score"] is not None else 0.0
            min_score = float(row["lowest_score"]) if row["lowest_score"] is not None else 0.0

            # Count total questions answered in filtered set
            cursor.execute(
                f"""
                SELECT COUNT(d.id) as q_count
                FROM interview_details d
                JOIN interviews i ON d.interview_id = i.id
                {where_sql.replace('interview_date', 'i.interview_date').replace('role', 'i.role').replace('difficulty', 'i.difficulty').replace('candidate_name', 'i.candidate_name')}
            """,
                params,
            )
            q_row = cursor.fetchone()
            total_questions = q_row["q_count"] if q_row else 0

            # Trend metrics: last 5 vs previous 5
            cursor.execute(
                f"""
                SELECT average_score FROM interviews{where_sql} ORDER BY id DESC LIMIT 10
            """,
                params,
            )
            recent_scores = [r["average_score"] for r in cursor.fetchall()]

            last_5_avg = None
            prev_5_avg = None
            delta = None

            if len(recent_scores) >= 1:
                last_5 = recent_scores[:5]
                last_5_avg = sum(last_5) / len(last_5)

            if len(recent_scores) > 5:
                prev_5 = recent_scores[5:10]
                prev_5_avg = sum(prev_5) / len(prev_5)
                delta = last_5_avg - prev_5_avg

            return {
                "total_interviews": total_interviews,
                "total_questions_answered": total_questions,
                "average_score": avg_score,
                "highest_score": max_score,
                "lowest_score": min_score,
                "last_5_avg": last_5_avg,
                "prev_5_avg": prev_5_avg,
                "improvement_delta": delta,
            }
    except Exception:
        return empty_result


def get_stats_by_role(date_from=None, date_to=None, difficulty=None):
    """
    Get average scores grouped by role.
    """
    where_sql, params = _build_filter_where(
        difficulty=difficulty, date_from=date_from, date_to=date_to
    )
    query = f"""
        SELECT role, AVG(average_score) as avg_score, COUNT(*) as count
        FROM interviews{where_sql}
        GROUP BY role
        ORDER BY avg_score DESC;
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
    except Exception:
        return []


def get_stats_by_difficulty(date_from=None, date_to=None, role=None):
    """
    Get average scores grouped by difficulty.
    """
    where_sql, params = _build_filter_where(
        role=role, date_from=date_from, date_to=date_to
    )
    query = f"""
        SELECT difficulty, AVG(average_score) as avg_score, COUNT(*) as count
        FROM interviews{where_sql}
        GROUP BY difficulty
        ORDER BY CASE difficulty
            WHEN 'Easy' THEN 1
            WHEN 'Medium' THEN 2
            WHEN 'Hard' THEN 3
            ELSE 4 END;
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
    except Exception:
        return []


def get_score_timeline(role=None, difficulty=None, date_from=None, date_to=None):
    """
    Get score timeline sorted by interview date ascending.
    """
    where_sql, params = _build_filter_where(
        role=role, difficulty=difficulty, date_from=date_from, date_to=date_to
    )
    query = f"""
        SELECT id, candidate_name, role, difficulty, average_score, interview_date
        FROM interviews{where_sql}
        ORDER BY id ASC;
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
    except Exception:
        return []


def get_aspect_stats(role=None, difficulty=None, date_from=None, date_to=None):
    """
    Map textual evaluations (Accuracy, Technical Depth, Communication)
    into numerical scores to render aspect performance radar/bar charts.
    Ratings:
      - Excellent / Outstanding / Great -> 95
      - Good / Above Average -> 80
      - Average / Fair -> 65
      - Needs Improvement / Poor -> 45
    """
    where_sql, params = _build_filter_where(
        role=role, difficulty=difficulty, date_from=date_from, date_to=date_to
    )

    rating_map = {
        "excellent": 95,
        "outstanding": 95,
        "great": 90,
        "good": 80,
        "above average": 80,
        "average": 65,
        "fair": 60,
        "needs improvement": 45,
        "poor": 30,
    }

    query = f"""
        SELECT d.accuracy, d.technical_depth, d.communication
        FROM interview_details d
        JOIN interviews i ON d.interview_id = i.id
        {where_sql.replace('interview_date', 'i.interview_date').replace('role', 'i.role').replace('difficulty', 'i.difficulty').replace('candidate_name', 'i.candidate_name')}
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return {"Accuracy": 0.0, "Technical Depth": 0.0, "Communication": 0.0}

            acc_scores, tech_scores, comm_scores = [], [], []

            for r in rows:
                acc = str(r["accuracy"] or "").strip().lower()
                tech = str(r["technical_depth"] or "").strip().lower()
                comm = str(r["communication"] or "").strip().lower()

                for key, val in rating_map.items():
                    if key in acc:
                        acc_scores.append(val)
                        break
                for key, val in rating_map.items():
                    if key in tech:
                        tech_scores.append(val)
                        break
                for key, val in rating_map.items():
                    if key in comm:
                        comm_scores.append(val)
                        break

            return {
                "Accuracy": sum(acc_scores) / len(acc_scores) if acc_scores else 75.0,
                "Technical Depth": sum(tech_scores) / len(tech_scores) if tech_scores else 75.0,
                "Communication": sum(comm_scores) / len(comm_scores) if comm_scores else 75.0,
            }
    except Exception:
        return {"Accuracy": 0.0, "Technical Depth": 0.0, "Communication": 0.0}


# Initialize DB and migration on import
create_tables()