from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
GROUND_TRUTH_PATH = BASE_DIR / "data" / "ground_truth.json"


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def evidence_matches(predicted_evidence: str, expected_evidence: str) -> bool:
    pred = normalize_text(predicted_evidence)
    expected = normalize_text(expected_evidence)

    if not pred or not expected:
        return pred == expected

    return pred == expected or pred in expected or expected in pred


def _metrics_for_items(predictions: list[dict[str, Any]], ground_truth: list[dict[str, Any]]) -> dict[str, int | float]:
    tp = 0
    fp = 0
    matched_ground_truth_indexes: set[int] = set()

    for pred_index, prediction in enumerate(predictions):
        matched_index = None
        for gt_index, expected in enumerate(ground_truth):
            if gt_index in matched_ground_truth_indexes:
                continue
            if prediction.get("pattern") != expected.get("pattern"):
                continue
            if evidence_matches(
                str(prediction.get("evidence", "")),
                str(expected.get("evidence", "")),
            ):
                matched_index = gt_index
                break

        if matched_index is not None:
            tp += 1
            matched_ground_truth_indexes.add(matched_index)
        else:
            fp += 1

    fn = len(ground_truth) - len(matched_ground_truth_indexes)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_matches(predictions: list[dict[str, Any]], ground_truth: list[dict[str, Any]]) -> dict[str, Any]:
    """Vergleicht Modell-Ergebnisse mit einer Ground-Truth-Liste und gibt Kennzahlen zurück."""
    metrics = _metrics_for_items(predictions, ground_truth)

    pattern_names = sorted({item["pattern"] for item in predictions} | {item["pattern"] for item in ground_truth})
    per_pattern: dict[str, dict[str, Any]] = {}

    for pattern_name in pattern_names:
        pred_items = [item for item in predictions if item.get("pattern") == pattern_name]
        gt_items = [item for item in ground_truth if item.get("pattern") == pattern_name]
        per_pattern[pattern_name] = _metrics_for_items(pred_items, gt_items)

    return {
        "summary": metrics,
        "by_pattern": per_pattern,
        "predicted_matches": len(predictions),
        "ground_truth_matches": len(ground_truth),
    }


def load_ground_truth(path: Path = GROUND_TRUTH_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        return data.get("matches", [])
    return data
