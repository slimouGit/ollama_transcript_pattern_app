from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .schemas import AnalysisRequest, AnalysisResponse


RESULTS_DIR = Path(__file__).resolve().parent.parent / "analysis_results"


def write_analysis_report(
    analysis: AnalysisResponse,
    request: AnalysisRequest,
    evaluation: dict[str, Any],
) -> Path:
    """Schreibt einen vollständigen, menschenlesbaren Bericht eines Analyse-Laufs."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone()
    filename = f"analyse_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.txt"
    path = RESULTS_DIR / filename

    parameters = {
        "model": analysis.model,
        "device": request.device,
        "timeout_seconds": request.timeout,
        "chunk_size": request.chunk_size,
        "temperature": request.temperature,
        "top_k": request.top_k,
        "top_p": request.top_p,
        "seed": request.seed,
        "output_tokens": request.output_tokens,
    }

    lines = [
        "TRANSCRIPT PATTERN ANALYZER - ANALYSEBERICHT",
        "=" * 52,
        f"Zeitpunkt: {timestamp.isoformat()}",
        f"Modell: {analysis.model}",
        "",
        "PARAMETER",
        "-" * 52,
    ]
    lines.extend(f"{key}: {value}" for key, value in parameters.items())
    lines.extend(
        [
            "",
            "LAUF-METADATEN",
            "-" * 52,
            f"Dauer Sekunden: {analysis.duration_seconds}",
            f"Anzahl Chunks: {analysis.chunk_count}",
            f"Fehlgeschlagene Chunks: {analysis.failed_chunks}",
            f"Anzahl Treffer: {len(analysis.matches)}",
            "",
            "DEVICE-INFORMATIONEN",
            "-" * 52,
            f"Angefordert: {analysis.device_info.get('requested_device')}",
            f"Tatsächlich genutzt: {analysis.device_info.get('actual_runtime_device')}",
            f"CPU: {analysis.device_info.get('cpu_name')}",
            f"GPU erkannt: {analysis.device_info.get('gpu_detected')}",
            f"GPU: {analysis.device_info.get('gpu_name')}",
            f"GPU VRAM GB: {analysis.device_info.get('gpu_vram_gb')}",
            f"RAM GB: {analysis.device_info.get('ram_gb')}",
            f"Ollama-Modell: {analysis.device_info.get('selected_ollama_model')}",
            f"Runtime-Details: {analysis.device_info.get('ollama_runtime')}",
            "",
            "TREFFER",
            "-" * 52,
        ]
    )

    if analysis.matches:
        for index, match in enumerate(analysis.matches, start=1):
            confidence = (
                "nicht verfügbar"
                if match.confidence is None
                else f"{match.confidence:.4f} ({match.confidence * 100:.1f} %)"
            )
            lines.extend(
                [
                    f"[{index}] Muster: {match.pattern}",
                    f"Evidence: {match.evidence}",
                    f"Begründung: {match.explanation}",
                    f"Confidence: {confidence}",
                    "",
                ]
            )
    else:
        lines.append("Keine Treffer.")

    summary = evaluation.get("summary", {})
    lines.extend(
        [
            "EVALUATION",
            "-" * 52,
            f"Ground Truth geladen: {evaluation.get('ground_truth_loaded')}",
            f"Ground-Truth-Treffer: {evaluation.get('ground_truth_matches')}",
            f"Vorhergesagte Treffer: {evaluation.get('predicted_matches')}",
            f"Precision: {summary.get('precision')}",
            f"Recall: {summary.get('recall')}",
            f"F1: {summary.get('f1')}",
            f"TP: {summary.get('tp')} | FP: {summary.get('fp')} | FN: {summary.get('fn')}",
            "",
            "METRIKEN NACH MUSTER",
            "-" * 52,
        ]
    )
    for pattern, metrics in evaluation.get("by_pattern", {}).items():
        lines.append(
            f"{pattern}: Precision={metrics.get('precision')}, "
            f"Recall={metrics.get('recall')}, F1={metrics.get('f1')}, "
            f"TP={metrics.get('tp')}, FP={metrics.get('fp')}, FN={metrics.get('fn')}"
        )

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
