from pathlib import Path
from hashlib import sha256
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .analyzer import analyze_transcript
from .device_info import get_device_info
from .evaluation import evaluate_matches, load_ground_truth
from .ollama_client import OLLAMA_MODEL, OllamaError, available_models, health
from .result_writer import write_analysis_report
from .schemas import AnalysisRequest, AnalysisResponse


BASE_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPT_PATH = BASE_DIR / "data" / "interview.txt"
DATA_DIR = BASE_DIR / "data"
app = FastAPI(title="Transcript Pattern Analyzer", version="1.0.0")
latest_analysis: AnalysisResponse | None = None
latest_request: AnalysisRequest | None = None
analysis_cache: dict[str, AnalysisResponse] = {}
analysis_lock = Lock()
MAX_CACHE_ENTRIES = 32


@app.get("/", response_class=HTMLResponse)
def index():
    # Liefert die Browser-Oberfläche aus dem templates-Ordner.
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


def read_transcript() -> str:
    # Liest das feste Interview und verhindert eine Analyse ohne Text.
    try:
        transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Das Interview-Transkript konnte nicht gelesen werden.") from exc

    if not transcript:
        raise HTTPException(status_code=422, detail="Das Interview-Transkript ist leer.")
    return transcript


def transcript_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.txt"))


def read_transcript_file(filename: str) -> str:
    path = DATA_DIR / filename
    if path.parent != DATA_DIR or path.suffix.lower() != ".txt" or not path.is_file():
        raise HTTPException(status_code=404, detail="Transkript nicht gefunden.")

    try:
        transcript = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Das Transkript konnte nicht gelesen werden.") from exc

    if not transcript:
        raise HTTPException(status_code=422, detail="Das Transkript ist leer.")
    return transcript


@app.get("/health")
def health_check():
    # Prüft, ob Ollama erreichbar ist.
    return health()


@app.get("/device-info")
def device_info(requested_device: str = "auto", model: str | None = None):
    if requested_device not in {"auto", "cpu", "gpu"}:
        raise HTTPException(status_code=422, detail="requested_device muss auto, cpu oder gpu sein.")
    return get_device_info(requested_device=requested_device, model=model)


@app.get("/models")
def models():
    try:
        return {"models": available_models()}
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/transcript")
def transcript():
    # Stellt das Interview für die Oberfläche bereit.
    return {"transcript": read_transcript()}


@app.get("/transcripts")
def transcripts():
    return {"transcripts": [path.name for path in transcript_files()]}


@app.get("/transcripts/{filename}")
def transcript_by_filename(filename: str):
    return {"filename": filename, "transcript": read_transcript_file(filename)}


def analysis_cache_key(options: AnalysisRequest, transcript: str) -> str:
    settings = "|".join(
        [
            transcript,
            options.model or OLLAMA_MODEL,
            options.device,
            str(options.timeout),
            str(options.chunk_size),
            str(options.temperature),
            str(options.top_k),
            str(options.top_p),
            str(options.seed),
            str(options.output_tokens),
        ]
    )
    return sha256(settings.encode("utf-8")).hexdigest()


@app.post("/analyze-interview", response_model=AnalysisResponse)
def analyze_interview(options: AnalysisRequest | None = None):
    # Analysiert das Interview mit den Optionen dieses Laufs.
    global latest_analysis, latest_request
    latest_analysis = None
    options = options or AnalysisRequest()
    latest_request = options
    transcript_text = options.transcript.strip()
    if not transcript_text:
        raise HTTPException(status_code=422, detail="Das Transkript ist leer.")
    cache_key = analysis_cache_key(options, transcript_text)
    with analysis_lock:
        cached_analysis = analysis_cache.get(cache_key)
        if cached_analysis is not None:
            cached_analysis.device_info = get_device_info(
                requested_device=options.device,
                model=cached_analysis.model,
            )
            latest_analysis = cached_analysis
            return cached_analysis

        try:
            latest_analysis = analyze_transcript(
                transcript_text,
                model=options.model,
                timeout=options.timeout,
                chunk_size=options.chunk_size,
                device=options.device,
                temperature=options.temperature,
                top_k=options.top_k,
                top_p=options.top_p,
                seed=options.seed,
                output_tokens=options.output_tokens,
            )
            latest_analysis.device_info = get_device_info(
                requested_device=options.device,
                model=latest_analysis.model,
            )
        except OllamaError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        if len(analysis_cache) >= MAX_CACHE_ENTRIES:
            analysis_cache.pop(next(iter(analysis_cache)))
        analysis_cache[cache_key] = latest_analysis
        return latest_analysis


@app.get("/evaluate")
def evaluate_current_analysis():
    """Bewertet ausschließlich das zuletzt gespeicherte Analyseergebnis."""
    if latest_analysis is None or latest_request is None:
        raise HTTPException(
            status_code=409,
            detail="Bitte zuerst die Analyse ausführen.",
        )

    ground_truth = load_ground_truth()
    predictions = [
        {"pattern": match.pattern, "evidence": match.evidence}
        for match in latest_analysis.matches
    ]

    result = {
        "model": latest_analysis.model,
        "ground_truth_loaded": bool(ground_truth),
        "evaluation": evaluate_matches(predictions, ground_truth),
    }
    try:
        report_path = write_analysis_report(
            latest_analysis,
            latest_request,
            {
                "ground_truth_loaded": result["ground_truth_loaded"],
                **result["evaluation"],
            },
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Analysebericht konnte nicht gespeichert werden: {exc}") from exc

    result["report_file"] = str(report_path.relative_to(BASE_DIR))
    return result


