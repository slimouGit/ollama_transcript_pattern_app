from typing import List
from pydantic import BaseModel, Field


class PatternDefinition(BaseModel):
    """Diese Klasse speichert den Namen und die Beschreibung eines Suchmusters."""

    name: str
    description: str


class Match(BaseModel):
    """Diese Klasse speichert einen Treffer mit Textbeleg und Confidence-Wert."""

    pattern: str
    evidence: str
    explanation: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AnalysisResponse(BaseModel):
    """Diese Klasse speichert das vollständige Ergebnis der Interviewanalyse."""

    transcript: str
    matches: List[Match]
    model: str
    duration_seconds: float | None = None
    chunk_count: int = 0
    failed_chunks: list[int] = Field(default_factory=list)
    parameters: dict[str, int | float | str | None] = Field(default_factory=dict)
    device_info: dict[str, object] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Optionen für einen einzelnen Analyseaufruf."""

    transcript: str
    model: str | None = None
    device: str = Field(default="auto", pattern="^(auto|gpu|cpu)$")
    timeout: float | None = Field(default=None, ge=5, le=600)
    chunk_size: int | None = Field(default=None, ge=500, le=20000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_k: int = Field(default=1, ge=1, le=100)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    seed: int = Field(default=42, ge=0, le=2147483647)
    output_tokens: int = Field(default=512, ge=128, le=2048)
