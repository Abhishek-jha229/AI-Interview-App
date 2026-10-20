"""
Speech-to-text transcription layer for AI Interview Simulator.
Wraps Groq's Whisper transcription endpoint, reusing the shared Groq client
and error hierarchy from core.ai so the UI can handle failures consistently.
"""

import os

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from core.ai import GroqConfigError, GroqError, GroqRetryableError, get_groq_client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

DEFAULT_WHISPER_MODEL = "whisper-large-v3-turbo"
MAX_AUDIO_BYTES = 24 * 1024 * 1024  # 24 MB, matches Groq's transcription upload limit


def get_whisper_model():
    """
    Resolve the Whisper model to use, preferring settings.json then .env,
    falling back to the turbo model.
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    model = ""
    try:
        # Local import avoids a hard circular dependency at module load time.
        from core.settings import load_settings

        settings = load_settings()
        model = (settings.get("whisper_model") or "").strip()
    except Exception:
        model = ""

    if not model:
        model = (os.getenv("WHISPER_MODEL") or "").strip()

    if not model:
        model = DEFAULT_WHISPER_MODEL

    return model


def transcribe_audio(audio_bytes, filename="answer.wav", language=None):
    """
    Transcribe recorded audio bytes to text using Groq's Whisper API.

    Args:
        audio_bytes: Raw audio bytes (e.g. from st.audio_input()).
        filename: Filename hint sent with the upload; extension informs Groq's decoder.
        language: Optional ISO-639-1 language code (e.g. "en") to bias transcription.
            Left as None to let Whisper auto-detect the spoken language.

    Returns:
        str: The transcribed text, stripped of leading/trailing whitespace.

    Raises:
        GroqConfigError: The Groq API key is missing/invalid — retrying won't help
            until the user fixes configuration.
        GroqRetryableError: A transient failure (network, rate limit, 5xx, empty
            audio issues that might be a fluke) — the UI may offer a Retry button.
        GroqError: Any other non-retryable failure from the Groq API.
    """
    if not audio_bytes:
        raise GroqRetryableError("No audio was recorded. Please try recording again.")

    size = len(audio_bytes)
    if size == 0:
        raise GroqRetryableError("The recording was empty. Please try recording again.")

    if size > MAX_AUDIO_BYTES:
        raise GroqError(
            f"Recording is too large ({size / (1024 * 1024):.1f} MB). "
            f"Please keep recordings under {MAX_AUDIO_BYTES / (1024 * 1024):.0f} MB "
            "— try a shorter answer or record in smaller chunks."
        )

    load_dotenv(dotenv_path=ENV_PATH, override=True)
    client = get_groq_client()
    model = get_whisper_model()

    kwargs = {
        "file": (filename or "answer.wav", audio_bytes),
        "model": model,
        "response_format": "text",
    }
    if language:
        kwargs["language"] = language

    try:
        result = client.audio.transcriptions.create(**kwargs)
    except AuthenticationError as exc:
        raise GroqConfigError(
            "GROQ_API_KEY is invalid or expired. Update `.env` or Settings."
        ) from exc
    except (RateLimitError, APIConnectionError) as exc:
        raise GroqRetryableError(
            "Groq rate limit reached or network connection failed while transcribing. "
            "Please retry."
        ) from exc
    except APIStatusError as exc:
        status = getattr(exc, "status_code", None)
        if status is not None and status >= 500:
            raise GroqRetryableError(
                f"Groq is temporarily unavailable (HTTP {status}) while transcribing. Please retry."
            ) from exc
        raise GroqError(f"Transcription request failed: {exc}") from exc
    except Exception as exc:
        raise GroqRetryableError(f"Unexpected error while transcribing audio: {exc}") from exc

    # response_format="text" can return either a plain string or an object
    # with a `.text` attribute depending on SDK version — handle both.
    if isinstance(result, str):
        text = result
    else:
        text = getattr(result, "text", "") or ""

    text = text.strip()
    if not text:
        raise GroqRetryableError(
            "Transcription returned no text. The recording may have been silent — please try again."
        )

    return text
