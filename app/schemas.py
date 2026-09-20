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


class AnalysisRequest(BaseModel):
    """Optionen für einen einzelnen Analyseaufruf."""

    transcript: str
    model: str | None = None
    device: str = Field(default="auto", pattern="^(auto|gpu|cpu)$")
    timeout: float | None = Field(default=None, ge=5, le=600)
    chunk_size: int | None = Field(default=None, ge=500, le=20000)
