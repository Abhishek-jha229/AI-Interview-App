"""
Evaluator module for AI Interview Simulator.
Scores candidate answers via Groq, applies a client-side garbage filter,
normalizes structured evaluation results, and extracts model explanations.
"""

import json
import re

from core.ai import GroqError, GroqRetryableError, _extract_json_text, chat_completion
from core.prompts import evaluation_prompt

REQUIRED_KEYS = (
    "score",
    "accuracy",
    "technical_depth",
    "communication",
    "missing_points",
    "feedback",
    "model_explanation",
)

# Patterns that strongly indicate a garbage / non-answer
_GARBAGE_RE = re.compile(
    r"^[a-z]{1,6}$|"           # single short lowercase word (sdaf, asd, test, hi)
    r"^[^a-zA-Z]*$|"           # no letters at all
    r"^(.)\1{3,}$|"            # same character repeated 4+ times (aaaa, ....., /////)
    r"^\s*$",                  # blank / whitespace only
    re.IGNORECASE,
)

_MIN_WORD_COUNT = 4            # fewer than 4 real words → guaranteed low score


def _is_garbage(answer: str) -> bool:
    stripped = answer.strip()
    if _GARBAGE_RE.match(stripped):
        return True
    word_count = len(stripped.split())
    if word_count < _MIN_WORD_COUNT:
        return True
    return False


def _normalize_evaluation(data: dict) -> dict:
    if not isinstance(data, dict):
        raise GroqRetryableError("AI evaluation response was not a JSON object. Please retry.")

    try:
        score = float(data.get("score", 0))
    except (TypeError, ValueError) as exc:
        raise GroqRetryableError("AI evaluation score was not a valid number. Please retry.") from exc

    score = max(0.0, min(100.0, score))
    if score.is_integer():
        score = int(score)

    missing_points = data.get("missing_points") or []
    if isinstance(missing_points, str):
        missing_points = [missing_points] if missing_points.strip() else []
    if not isinstance(missing_points, list):
        missing_points = []
    missing_points = [str(p).strip() for p in missing_points if str(p).strip()]

    return {
        "score": score,
        "accuracy": str(data.get("accuracy") or "Needs Improvement").strip(),
        "technical_depth": str(data.get("technical_depth") or "Superficial").strip(),
        "communication": str(data.get("communication") or "Unclear").strip(),
        "missing_points": missing_points,
        "feedback": str(data.get("feedback") or "").strip() or "No feedback provided.",
        "model_explanation": str(data.get("model_explanation") or "").strip() or "No model explanation available.",
    }


def evaluate_answer(question: str, answer: str) -> dict:
    """
    Score a candidate answer via Groq JSON response.

    - Applies a client-side garbage filter: if the answer is clearly junk
      (random chars, < 4 words), the Groq score is CAPPED at 5/100 regardless
      of what the model returns.
    - Retries once on malformed JSON before raising a GroqRetryableError.
    - Never fabricates a default score; always either succeeds or raises.
    """
    garbage = _is_garbage(answer)
    prompt = evaluation_prompt(question, answer)

    content = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        json_mode=True,
    )

    parsed = None

    # First parse attempt
    try:
        parsed = json.loads(_extract_json_text(content))
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    # One retry on malformed JSON
    if not parsed:
        try:
            content_retry = chat_completion(
                messages=[
                    {"role": "user", "content": prompt},
                    {
                        "role": "system",
                        "content": "Your output MUST be strictly valid JSON with no markdown or extra text.",
                    },
                ],
                json_mode=True,
            )
            parsed = json.loads(_extract_json_text(content_retry))
        except Exception as exc:
            raise GroqRetryableError(
                "Could not parse the AI evaluation response as valid JSON. Please click Retry evaluation."
            ) from exc

    try:
        result = _normalize_evaluation(parsed)
    except GroqError:
        raise
    except Exception as exc:
        raise GroqRetryableError(
            f"Could not normalize the AI evaluation response: {exc}"
        ) from exc

    # Client-side garbage enforcement: cap score to 5 max for junk answers
    if garbage and result["score"] > 5:
        result["score"] = 5
        result["accuracy"] = "Needs Improvement"
        result["technical_depth"] = "Superficial"
        result["communication"] = "Unclear"
        if not result["missing_points"]:
            result["missing_points"] = ["Answer was not a valid technical response to the question."]

    return result
