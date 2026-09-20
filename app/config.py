import os
import re


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_MAX_OUTPUT_TOKENS = int(os.getenv("OLLAMA_MAX_OUTPUT_TOKENS", "2048"))
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "2"))
OLLAMA_SEED = int(os.getenv("OLLAMA_SEED", "42"))
MIN_OUTPUT_TOKENS = 512

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "3000"))
CHUNK_OVERLAP_SENTENCES = int(os.getenv("CHUNK_OVERLAP_SENTENCES", "0"))
ABBREVIATION_PATTERN = re.compile(
    r"\b(?:Dr|Prof|Herr|Frau|z\.\s*B|d\.\s*h|bzw|usw|etc|vgl)\.",
    re.IGNORECASE,
)
PERIOD_MARKER = "__PERIOD__"


def output_tokens_for_chunk(chunk_size: int) -> int:
    """Schätzt das Ausgabelimit konservativ aus der Chunk-Größe."""
    return max(MIN_OUTPUT_TOKENS, min(OLLAMA_MAX_OUTPUT_TOKENS, chunk_size // 2))
