# Ground-Truth-Sampling-Demo

Dieses Verzeichnis zeigt den Schritt **vor** der manuellen Ground-Truth-Erstellung.
Es verändert die bestehende Transcript-Pattern-App nicht.

## Idee

Bei 1.000 Interviews wird nicht zuerst für alle 1.000 eine Ground Truth erstellt. Stattdessen:

1. Alle Transkripte werden automatisch in Vektoren (Embeddings) umgewandelt.
2. Ähnliche Interviews werden mit K-Means gruppiert.
3. Pro Cluster wird mindestens ein typischer Vertreter ausgewählt.
4. Zusätzlich werden inhaltliche Ausreißer ausgewählt, damit seltene Fälle nicht nur wegen ihrer Seltenheit verschwinden.
5. Nur die ausgewählten Interviews werden manuell nach dem **identischen Pattern-Gerüst** annotiert.
6. Diese Dateien bilden den Evaluations-/Ground-Truth-Datensatz.

Wichtig: Die Cluster **sind nicht die Ground Truth**. Sie helfen nur dabei, eine möglichst sinnvolle Stichprobe für die Ground Truth auszuwählen.

## Enthaltene Demo-Daten

`transcripts/` enthält 12 vollständig synthetische medizinische Interviews. `interview_012_rare.txt` enthält absichtlich einen seltenen Tauchunfall-Kontext, damit man sehen kann, ob der Ausreißer-Mechanismus ihn hervorhebt.

## Installation

Im Projektordner:

```powershell
pip install -r ground_truth_sampling_demo/requirements.txt
```

Für die empfohlene Variante mit lokalen Ollama-Embeddings:

```powershell
ollama pull nomic-embed-text
python ground_truth_sampling_demo/cluster_transcripts.py --backend ollama
```

Ohne zusätzliches Ollama-Embedding-Modell kann die Demo mit TF-IDF ausgeführt werden:

```powershell
python ground_truth_sampling_demo/cluster_transcripts.py --backend tfidf
```

Der Bericht landet in:

```text
ground_truth_sampling_demo/output/selection_report.json
```

## Was man danach macht

Für jedes in `recommended_for_manual_ground_truth` ausgewählte Transkript wird eine eigene JSON-Datei erstellt, z. B.:

```text
ground_truth/interview_003.json
ground_truth/interview_008.json
ground_truth/interview_012_rare.json
```

Alle Dateien verwenden dasselbe Gerüst bzw. dieselben Pattern-Namen wie die bestehende App. `ground_truth/ground_truth_template.json` ist dafür eine Vorlage.

Die Evidence muss anschließend **wirklich anhand des jeweiligen Transkripts geprüft** werden. Ein LLM kann Vorannotation liefern, aber die Referenzdaten sollten für eine belastbare Evaluation menschlich validiert werden.

## Warum Embeddings statt das LLM direkt "Cluster bilden" zu lassen?

Für viele Dokumente ist es üblicher und reproduzierbarer, jeden Text in einen Zahlenvektor umzuwandeln und diese Vektoren mathematisch zu clustern. Ein generatives LLM kann danach optional Cluster beschreiben oder Vorannotation liefern. Für die Auswahl der Ground-Truth-Stichprobe ist die Embedding-Variante einfacher zu messen und günstiger.
