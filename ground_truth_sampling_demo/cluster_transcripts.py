from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import requests
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "transcripts"
DEFAULT_OUTPUT = ROOT / "output" / "selection_report.json"


def load_transcripts(folder: Path) -> tuple[list[str], list[str]]:
    files = sorted(folder.glob("*.txt"))
    if not files:
        raise SystemExit(f"Keine .txt-Dateien in {folder} gefunden.")
    return [f.name for f in files], [f.read_text(encoding="utf-8") for f in files]


def ollama_embeddings(texts: list[str], model: str, url: str) -> np.ndarray:
    response = requests.post(
        f"{url.rstrip('/')}/api/embed",
        json={"model": model, "input": texts},
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    embeddings = data.get("embeddings")
    if not embeddings or len(embeddings) != len(texts):
        raise RuntimeError("Ollama hat keine passenden Embeddings zurückgegeben.")
    return np.asarray(embeddings, dtype=float)


def tfidf_embeddings(texts: list[str]) -> np.ndarray:
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
    )
    return vectorizer.fit_transform(texts).toarray()


def choose_cluster_count(n_documents: int, requested: int | None) -> int:
    if requested is not None:
        return max(2, min(requested, n_documents))
    # Kleine, nachvollziehbare Heuristik für die Demo.
    return max(2, min(round(math.sqrt(n_documents)), n_documents))


def cluster_and_rank(
    matrix: np.ndarray,
    names: list[str],
    texts: list[str],
    n_clusters: int,
    representatives_per_cluster: int,
    outlier_count: int,
) -> dict[str, Any]:
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(matrix)

    distances_to_centroid = np.linalg.norm(matrix - model.cluster_centers_[labels], axis=1)

    clusters: list[dict[str, Any]] = []
    selected_names: set[str] = set()

    for cluster_id in range(n_clusters):
        idx = np.where(labels == cluster_id)[0]
        ranked = idx[np.argsort(distances_to_centroid[idx])]
        representatives = ranked[:representatives_per_cluster]
        selected_names.update(names[i] for i in representatives)

        clusters.append(
            {
                "cluster": int(cluster_id),
                "size": int(len(idx)),
                "representatives": [names[i] for i in representatives],
                "members": [
                    {
                        "file": names[i],
                        "distance_to_centroid": round(float(distances_to_centroid[i]), 4),
                    }
                    for i in idx
                ],
            }
        )

    # Globale Ausreißer: Dokumente, die zu allen anderen vergleichsweise weit entfernt sind.
    distance_matrix = pairwise_distances(matrix, metric="cosine")
    mean_distance = distance_matrix.mean(axis=1)
    outlier_idx = np.argsort(mean_distance)[::-1][:outlier_count]
    outliers = [
        {
            "file": names[i],
            "mean_cosine_distance": round(float(mean_distance[i]), 4),
            "reason": "inhaltlich ungewöhnlich im Vergleich zum restlichen Korpus",
        }
        for i in outlier_idx
    ]
    selected_names.update(names[i] for i in outlier_idx)

    # Einfache Zusatzsignale. Sie ersetzen keine Ground Truth, helfen aber beim Sampling.
    metadata = []
    for name, text in zip(names, texts):
        metadata.append(
            {
                "file": name,
                "characters": len(text),
                "question_marks": text.count("?"),
                "negation_hits": sum(text.lower().count(term) for term in [" nein", " keine", " nicht", "nie"]),
                "medication_terms": sum(
                    text.lower().count(term)
                    for term in ["ibuprofen", "paracetamol", "ramipril", "diclofenac", "amoxicillin", "medikament"]
                ),
            }
        )

    return {
        "document_count": len(names),
        "cluster_count": n_clusters,
        "clusters": clusters,
        "outliers": outliers,
        "recommended_for_manual_ground_truth": sorted(selected_names),
        "document_metadata": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wählt aus vielen Transkripten repräsentative und ungewöhnliche Kandidaten für manuelle Ground-Truth-Annotation aus."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--backend", choices=["ollama", "tfidf"], default="ollama")
    parser.add_argument("--embedding-model", default=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
    parser.add_argument("--ollama-url", default=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--clusters", type=int, default=None)
    parser.add_argument("--representatives-per-cluster", type=int, default=1)
    parser.add_argument("--outliers", type=int, default=2)
    args = parser.parse_args()

    names, texts = load_transcripts(args.input)

    if args.backend == "ollama":
        print(f"Erzeuge Embeddings mit Ollama-Modell: {args.embedding_model}")
        matrix = ollama_embeddings(texts, args.embedding_model, args.ollama_url)
    else:
        print("Erzeuge TF-IDF-Vektoren (Fallback ohne Ollama-Embedding-Modell).")
        matrix = tfidf_embeddings(texts)

    n_clusters = choose_cluster_count(len(names), args.clusters)
    report = cluster_and_rank(
        matrix,
        names,
        texts,
        n_clusters=n_clusters,
        representatives_per_cluster=max(1, args.representatives_per_cluster),
        outlier_count=max(1, min(args.outliers, len(names))),
    )
    report["backend"] = args.backend
    report["embedding_model"] = args.embedding_model if args.backend == "ollama" else None

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nKandidaten für manuelle Ground Truth:")
    for filename in report["recommended_for_manual_ground_truth"]:
        print(f"  - {filename}")

    print("\nAuffällige / seltene Kandidaten:")
    for item in report["outliers"]:
        print(f"  - {item['file']} (Distanz {item['mean_cosine_distance']})")

    print(f"\nBericht gespeichert: {args.output}")


if __name__ == "__main__":
    main()
