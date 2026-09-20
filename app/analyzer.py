import logging
import re
import time

from .config import (
    ABBREVIATION_PATTERN,
    CHUNK_OVERLAP_SENTENCES,
    CHUNK_SIZE,
    PERIOD_MARKER,
    output_tokens_for_chunk,
)
from .ollama_client import OLLAMA_MODEL, OllamaError, chat_json
from .patterns import DEFAULT_PATTERNS
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import AnalysisResponse, Match


logger = logging.getLogger(__name__)


def split_sentences(text: str) -> list[str]:
    protected_text = ABBREVIATION_PATTERN.sub(
        lambda match: match.group().replace(".", PERIOD_MARKER),
        text.strip(),
    )
    sentences = re.split(
        r'(?<=[.!?])\s+|\n+',
        protected_text,
    )

    return [
        sentence.replace(PERIOD_MARKER, ".").strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_text(
    text: str,
    max_chars: int = CHUNK_SIZE,
    overlap_sentences: int = CHUNK_OVERLAP_SENTENCES,
) -> list[str]:

    sentences = split_sentences(text)

    chunks = []
    current_sentences = []

    for sentence in sentences:
        candidate = " ".join(
            current_sentences + [sentence]
        )

        if current_sentences and len(candidate) > max_chars:
            chunks.append(" ".join(current_sentences))

            current_sentences = (
                current_sentences[-overlap_sentences:]
                if overlap_sentences > 0
                else []
            )

        current_sentences.append(sentence)

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def analyze_chunk(
    chunk: str,
    model: str | None = None,
    timeout: float | None = None,
    device: str = "auto",
) -> list[Match]:
    user_prompt = build_user_prompt(chunk)

    raw = chat_json(
        SYSTEM_PROMPT,
        user_prompt,
        model=model,
        timeout=timeout,
        max_output_tokens=output_tokens_for_chunk(len(chunk)),
        device=device,
    )

    matches = []
    for item in raw.get("matches", []):
        if not isinstance(item, dict):
            continue
        item = dict(item)
        try:
            matches.append(Match.model_validate(item))
        except ValueError:
            continue

    allowed = {
        pattern.name
        for pattern in DEFAULT_PATTERNS
    }

    return filter_matches(matches, allowed, chunk)


def filter_matches(
    matches: list[Match],
    allowed: set[str],
    source_text: str = "",
) -> list[Match]:
    medical_context = re.compile(
        r"schmerz|symptom|beschwer|atem|luft|fieber|übel|allerg|medikament|tablett|"
        r"ibuprofen|therapie|behandlung|operation|krankheit|vorerkrank|drog|alkohol|"
        r"rauchen|hirnblutung|schlaganfall|herzinfarkt|krebs",
        re.IGNORECASE,
    )
    denial = re.compile(
        r"\bnein\b|\bnicht\b|\bkeine[nrms]?\b|\bkein[e]?\b|\bnichts\b|\bohne\b",
        re.IGNORECASE,
    )
    treatment = re.compile(
        r"medikament|tablett|ibuprofen|paracetamol|therapie|behandlung|genommen|nehme|einnahme|dosier",
        re.IGNORECASE,
    )

    filtered = []
    for match in matches:
        if match.pattern not in allowed:
            continue
        evidence = match.evidence.strip()
        if not evidence or len(evidence) > 320:
            continue
        if source_text and not _evidence_in_source(evidence, source_text):
            continue
        if match.pattern == "medikamente_behandlung" and not treatment.search(
            evidence
        ):
            continue
        if match.pattern == "verneinung_ausschluss" and (
            not denial.search(evidence) or not medical_context.search(evidence)
        ):
            continue
        filtered.append(match)

    return filtered


def _evidence_in_source(evidence: str, source_text: str) -> bool:
    normalize = lambda value: re.sub(r"\s+", " ", value.casefold()).strip()
    return normalize(evidence) in normalize(source_text)


def remove_duplicate_matches(
    matches: list[Match]
) -> list[Match]:

    unique_matches = []
    seen_evidence = set()

    for match in matches:
        key = re.sub(r"\s+", " ", match.evidence.strip().lower())

        if not key or key in seen_evidence:
            continue

        if any(
            key in re.sub(r"\s+", " ", existing.evidence.strip().lower())
            or re.sub(r"\s+", " ", existing.evidence.strip().lower()) in key
            for existing in unique_matches
        ):
            continue

        seen_evidence.add(key)
        unique_matches.append(match)

    return unique_matches


def analyze_transcript(
    transcript: str,
    model: str | None = None,
    timeout: float | None = None,
    chunk_size: int | None = None,
    device: str = "auto",
) -> AnalysisResponse:
    chunks = chunk_text(transcript, max_chars=chunk_size or CHUNK_SIZE)
    started_at = time.perf_counter()

    all_matches = []
    failed_chunks = []

    for chunk_index, chunk in enumerate(chunks, start=1):
        chunk_started_at = time.perf_counter()
        try:
            all_matches.extend(
                analyze_chunk(chunk, model=model, timeout=timeout, device=device)
            )
        except OllamaError as exc:
            failed_chunks.append(chunk_index)
            logger.warning(
                "Chunk %d/%d fehlgeschlagen und wird übersprungen: %s",
                chunk_index,
                len(chunks),
                exc,
            )
        finally:
            logger.info(
                "Chunk %d/%d verarbeitet in %.2f Sekunden",
                chunk_index,
                len(chunks),
                time.perf_counter() - chunk_started_at,
            )

    all_matches = remove_duplicate_matches(
        all_matches
    )
    duration_seconds = round(time.perf_counter() - started_at, 3)
    logger.info(
        "Analyse abgeschlossen: %d Chunks, %d fehlgeschlagen, %.2f Sekunden",
        len(chunks),
        len(failed_chunks),
        duration_seconds,
    )

    return AnalysisResponse(
        transcript=transcript,
        matches=all_matches,
        model=model or OLLAMA_MODEL,
        duration_seconds=duration_seconds,
        chunk_count=len(chunks),
        failed_chunks=failed_chunks,
    )