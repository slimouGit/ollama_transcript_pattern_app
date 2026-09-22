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


# ---------------------------------------------------------------------------
# Einfach gesagt:
# 1) Lade alle Transkripte
# 2) Wandle sie in Zahlen um
# 3) Gruppiere ähnliche Texte mit K-Means
# 4) Suche danach ungewöhnliche Ausreißer
# 5) Erzeuge einen Bericht, welche Dateien manuell annotiert werden sollten
# ---------------------------------------------------------------------------


def load_transcripts(folder: Path) -> tuple[list[str], list[str]]:
    """Liest alle .txt-Dateien aus einem Ordner und liefert Namen + Inhalte."""
    files = sorted(folder.glob("*.txt"))
    if not files:
        raise SystemExit(f"Keine .txt-Dateien in {folder} gefunden.")
    # Wenn man mehrere Texte hat, bekommt man eine Liste mit Dateinamen und eine Liste mit Inhalten.
    return [f.name for f in files], [f.read_text(encoding="utf-8") for f in files]


def ollama_embeddings(texts: list[str], model: str, url: str) -> np.ndarray:
    """Fragt Ollama nach Embeddings für die Texte. Embeddings = Zahlenvektoren, die Textähnlichkeit ausdrücken."""
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
    # np.asarray sorgt dafür, dass aus der Antwort ein numpy-Array wird.
    return np.asarray(embeddings, dtype=float)


def tfidf_embeddings(texts: list[str]) -> np.ndarray:
    """Erzeugt TF-IDF-Vektoren als einfacher Fallback, wenn Ollama nicht benutzt wird."""
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
    )
    # Aus dem Text wird eine Matrix aus Zahlen gebaut, die Wörter/ Wortkombinationen zählt.
    return vectorizer.fit_transform(texts).toarray()


def choose_cluster_count(n_documents: int, requested: int | None) -> int:
    """Wählt eine vernünftige Anzahl an Clustern aus. Für die Demo reicht eine einfache Heuristik."""
    if requested is not None:
        return max(2, min(requested, n_documents))
    # Kleine, nachvollziehbare Heuristik für die Demo:
    # Bei 12 Dokumenten ist die Wurzel ungefähr 3,5 -> also 4 Cluster.
    return max(2, min(round(math.sqrt(n_documents)), n_documents))


def cluster_and_rank(
    matrix: np.ndarray,
    names: list[str],
    texts: list[str],
    n_clusters: int,
    representatives_per_cluster: int,
    outlier_count: int,
) -> dict[str, Any]:
    """Gruppiert Texte, sucht Vertreter pro Cluster und markiert ungewöhnliche Fälle."""
    # K-Means macht aus vielen Textvektoren Gruppen.
    # Dokumente in derselben Gruppe sind einander inhaltlich ähnlicher.
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(matrix)

    # Distanz zum eigenen Clusterzentrum: Wie weit ist ein Text vom typischen Muster seiner Gruppe entfernt?
    distances_to_centroid = np.linalg.norm(matrix - model.cluster_centers_[labels], axis=1)

    clusters: list[dict[str, Any]] = []
    selected_names: set[str] = set()

    for cluster_id in range(n_clusters):
        idx = np.where(labels == cluster_id)[0]
        # Die Dateien werden nach Distanz sortiert: nah am Zentrum zuerst.
        ranked = idx[np.argsort(distances_to_centroid[idx])]
        # Typische Vertreter: die "nahesten" Dokumente an der Mitte des Clusters.
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

    # Globale Ausreißer:
    # Dokumente, die im Vergleich zum Rest des Korpus sehr weit entfernt sind.
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

    # Einfache Zusatzinfos. Sie sind keine Ground Truth, aber sie helfen beim Verständnis der Texte.
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
        # Diese Liste gibt die Datei-Namen an, die für manuelle Ground-Truth-Annotation empfohlen werden.
        "recommended_for_manual_ground_truth": sorted(selected_names),
        "document_metadata": metadata,
    }


def main() -> None:
    """Hauptfunktion: liest die Dateien, erzeugt Vektoren, clustert und speichert den Bericht."""
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

    # Schritt 1: Lade alle Texte und Dateinamen.
    names, texts = load_transcripts(args.input)

    # Schritt 2: Wandle die Texte in Zahlenvektoren um.
    if args.backend == "ollama":
        print(f"Erzeuge Embeddings mit Ollama-Modell: {args.embedding_model}")
        matrix = ollama_embeddings(texts, args.embedding_model, args.ollama_url)
    else:
        print("Erzeuge TF-IDF-Vektoren (Fallback ohne Ollama-Embedding-Modell).")
        matrix = tfidf_embeddings(texts)

    # Schritt 3: Entscheide, wie viele Cluster wir bilden wollen.
    n_clusters = choose_cluster_count(len(names), args.clusters)

    # Schritt 4: Führe Clustering und Ausreißer-Erkennung durch.
    report = cluster_and_rank(
        matrix,
        names,
        texts,
        n_clusters=n_clusters,
        representatives_per_cluster=max(1, args.representatives_per_cluster),
        outlier_count=max(1, min(args.outliers, len(names))),
    )

    # Zusatzinfos im Bericht, damit man nachvollziehen kann, mit welchem Backend gearbeitet wurde.
    report["backend"] = args.backend
    report["embedding_model"] = args.embedding_model if args.backend == "ollama" else None

    # Schritt 5: Speichere den Bericht auf der Festplatte.
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
