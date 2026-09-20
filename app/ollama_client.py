import json
import re
import time
from typing import Any, Dict

import requests

from .config import OLLAMA_MODEL, OLLAMA_RETRIES, OLLAMA_SEED, OLLAMA_TIMEOUT, OLLAMA_URL


class OllamaError(RuntimeError):
    """Diese Klasse beschreibt einen Fehler bei der Kommunikation mit Ollama."""

    pass


def chat_json(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    timeout: float | None = None,
    max_output_tokens: int = 2048,
    device: str = "auto",
) -> Dict[str, Any]:
    # Sendet den Analyseprompt an Ollama und erwartet eine JSON-Antwort.
    options: dict[str, Any] = {
        "temperature": 0,
        "seed": OLLAMA_SEED,
        "top_k": 1,
        "top_p": 1,
        "num_predict": max_output_tokens,
    }
    if device == "cpu":
        options["num_gpu"] = 0
    elif device == "gpu":
        options["num_gpu"] = -1

    payload = {
        "model": model or OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": options,
    }

    last_error: OllamaError | None = None
    for attempt in range(OLLAMA_RETRIES + 1):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=timeout or OLLAMA_TIMEOUT,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            result = _parse_json_content(content)
            if not isinstance(result.get("matches"), list):
                raise OllamaError("Ollama-JSON enthält keine gültige 'matches'-Liste.")
            return result
        except requests.RequestException as exc:
            last_error = OllamaError(
                f"Ollama ist nicht erreichbar: {exc}. Läuft 'ollama serve' und ist das Modell vorhanden?"
            )
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            last_error = OllamaError(
                "Ollama hat keine gültige JSON-Antwort geliefert."
            )
        except OllamaError as exc:
            last_error = exc

        if attempt < OLLAMA_RETRIES:
            time.sleep(0.5 * (attempt + 1))

    raise last_error or OllamaError("Ollama-Aufruf fehlgeschlagen.")


def _parse_json_content(content: str) -> Dict[str, Any]:
    if not isinstance(content, str):
        raise TypeError("Die Ollama-Antwort ist kein Text.")

    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE
        ).strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for position, character in enumerate(cleaned):
            if character != "{":
                continue
            try:
                result, _ = decoder.raw_decode(cleaned[position:])
                break
            except json.JSONDecodeError:
                continue
        else:
            raise

    if not isinstance(result, dict):
        raise TypeError("Die Ollama-Antwort ist kein JSON-Objekt.")
    return result


def health() -> Dict[str, Any]:
    # Prüft Ollama ohne eine Analyse zu starten.
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return {"ok": True, "model": OLLAMA_MODEL}
    except requests.RequestException as exc:
        return {"ok": False, "model": OLLAMA_MODEL, "detail": str(exc)}


def available_models() -> list[str]:
    """Liest die lokal installierten Ollama-Modelle."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return [
            item["name"]
            for item in models
            if item.get("name") and "embed" not in item["name"].lower()
        ]
    except (requests.RequestException, TypeError, AttributeError, KeyError) as exc:
        raise OllamaError(f"Ollama-Modelle konnten nicht geladen werden: {exc}") from exc
