"""
AI abstraction layer for Groq API calls.
Handles client initialization, exponential backoff retries, question caching,
and response parsing.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

from core.prompts import interview_prompt
from core.settings import load_settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH, override=True)

DEPRECATED_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
}
DEFAULT_FALLBACK_MODEL = "openai/gpt-oss-120b"

# Global in-memory cache for generated questions: (role, difficulty, count) -> list of questions
_QUESTION_CACHE = {}
_client = None

_JUNK_HEADING = re.compile(
    r"^(here (are|is)|questions?|interview|note|json|output|"
    r"the following|generated questions)\b",
    re.IGNORECASE,
)
_NUMBERED_ITEM = re.compile(r"^\s*(?:Q?\d+[\.\):]|[-•*])\s*(.+)$")


class GroqError(Exception):
    """Base error for Groq call failures shown in the UI."""
    retryable = False


class GroqConfigError(GroqError):
    """Missing or invalid API key — retry will not help until configuration is updated."""
    retryable = False


class GroqRetryableError(GroqError):
    """Network / rate-limit / transient API failure — UI can offer Retry."""
    retryable = True


def get_model_name():
    """
    Retrieve model name from local settings or .env, overriding deprecated models.
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    settings = load_settings()

    # Settings.json takes priority if valid, then .env
    model = (settings.get("groq_model") or os.getenv("GROQ_MODEL") or "").strip()
    if not model or model in DEPRECATED_MODELS:
        model = DEFAULT_FALLBACK_MODEL
    return model


def get_groq_client():
    """
    Create or retrieve cached Groq client instance using GROQ_API_KEY.
    """
    global _client

    load_dotenv(dotenv_path=ENV_PATH, override=True)
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()

    if not api_key:
        raise GroqConfigError(
            "GROQ_API_KEY is missing. Add it to `.env` or set it in Settings and restart the app. "
            "Get a key at https://console.groq.com/keys"
        )

    if _client is None:
        _client = Groq(api_key=api_key)

    return _client


def chat_completion(messages, json_mode=False, max_retries=2):
    """
    Single Groq chat call with exponential backoff retries and error mapping.
    """
    client = get_groq_client()
    model = get_model_name()

    kwargs = {
        "model": model,
        "messages": messages,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content or not str(content).strip():
                raise GroqRetryableError("Groq returned an empty response.")
            return content.strip()

        except AuthenticationError as exc:
            raise GroqConfigError(
                "GROQ_API_KEY is invalid or expired. Update `.env` or Settings."
            ) from exc

        except (RateLimitError, APIConnectionError) as exc:
            last_exception = GroqRetryableError(
                "Groq rate limit reached or network connection failed. Retrying..."
            )
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise last_exception from exc

        except APIStatusError as exc:
            status = getattr(exc, "status_code", None)
            if status is not None and status >= 500:
                last_exception = GroqRetryableError(
                    f"Groq is temporarily unavailable (HTTP {status}). Retrying..."
                )
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise last_exception from exc
            raise GroqError(f"Groq request failed: {exc}") from exc

        except Exception as exc:
            last_exception = GroqRetryableError(f"Unexpected error calling Groq: {exc}")
            if attempt < max_retries:
                time.sleep(1.0)
                continue
            raise last_exception from exc

    raise last_exception or GroqRetryableError("Groq API call failed after retries.")


def _extract_json_text(raw):
    """Strip markdown fences and isolate the first JSON value in the string."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    if text.startswith("{") or text.startswith("["):
        return text

    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    if match:
        return match.group(1)

    return text


def _is_junk_question(text):
    cleaned = (text or "").strip()
    if len(cleaned) < 10:
        return True
    if cleaned.startswith("#"):
        return True
    if re.match(r"^[\d.\):\-\s]+$", cleaned):
        return True
    if _JUNK_HEADING.match(cleaned):
        return True
    return False


def _clean_question_list(items):
    questions = []
    seen = set()

    for item in items:
        if not isinstance(item, str):
            continue
        text = item.strip()
        numbered = _NUMBERED_ITEM.match(text)
        if numbered:
            text = numbered.group(1).strip()
        if _is_junk_question(text):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        questions.append(text)

    return questions


def _parse_questions_json(content):
    try:
        data = json.loads(_extract_json_text(content))
    except json.JSONDecodeError:
        return []

    raw = []
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = data.get("questions") or data.get("interview_questions") or []
        if isinstance(raw, str):
            raw = [raw]

    if not isinstance(raw, list):
        return []

    return _clean_question_list(raw)


def _parse_questions_regex(content):
    numbered = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        match = _NUMBERED_ITEM.match(line)
        if match:
            numbered.append(match.group(1).strip())

    if numbered:
        return _clean_question_list(numbered)

    return _clean_question_list(content.splitlines())


def generate_questions(role, difficulty, total_questions, bypass_cache=False):
    """
    Generate interview questions with caching, cleaning, and top-up fallback.
    """
    cache_key = (role.strip(), difficulty.strip(), int(total_questions))

    if not bypass_cache and cache_key in _QUESTION_CACHE:
        return list(_QUESTION_CACHE[cache_key])

    prompt = interview_prompt(role, difficulty, total_questions)

    content = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        json_mode=True,
    )

    questions = _parse_questions_json(content)
    if not questions:
        questions = _parse_questions_regex(content)

    # Top-up call if AI returned fewer questions than requested
    if len(questions) < total_questions:
        remaining = total_questions - len(questions)
        try:
            topup_prompt = interview_prompt(role, difficulty, remaining)
            topup_content = chat_completion(
                messages=[{"role": "user", "content": topup_prompt}],
                json_mode=True,
            )
            extra = _parse_questions_json(topup_content) or _parse_questions_regex(topup_content)
            questions = _clean_question_list(questions + extra)
        except Exception:
            pass  # Fall back to whatever questions we successfully obtained

    if not questions:
        raise GroqRetryableError(
            "Could not parse valid interview questions from the AI response. Please retry."
        )

    # Trim to requested count if model over-generated
    questions = questions[:total_questions]

    # Store in session cache
    _QUESTION_CACHE[cache_key] = list(questions)
    return questions


def test_groq_connection():
    """
    Quick test call to verify API key and model connectivity.
    Returns (success: bool, message: str)
    """
    try:
        res = chat_completion(
            messages=[{"role": "user", "content": "Respond with 'OK'."}],
            json_mode=False,
            max_retries=1,
        )
        return True, f"Connection successful! Model '{get_model_name()}' responded: {res[:50]}"
    except Exception as exc:
        return False, str(exc)
