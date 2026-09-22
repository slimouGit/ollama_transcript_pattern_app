# Ground-Truth-Sampling-Workflow

## Ziel

Dieses Verzeichnis zeigt den Schritt vor der manuellen Ground-Truth-Erstellung. Es dient dazu, aus einer großen Menge von Transkripten eine sinnvolle, kleine Auswahl für manuelle Annotation zu bestimmen, ohne alle Dokumente einzeln zu prüfen.

Die zentrale Idee ist:

- nicht alle Transkripte werden händisch annotiert
- zuerst werden ähnliche Dokumente gruppiert
- danach werden repräsentative und seltene Fälle ausgewählt
- erst diese Auswahl wird manuell validiert und als Ground Truth verwendet

---

## Ablauf

### 1. Transkripte sammeln

Alle Textdateien werden aus dem Ordner `transcripts/` geladen.

Beispiel:

- interview_001.txt
- interview_002.txt
- interview_003.txt
- ...
- interview_012_rare.txt

### 2. Text in Vektoren umwandeln

Jedes Interview wird in einen numerischen Vektor übersetzt.

Es gibt zwei mögliche Varianten:

1. Ollama-Embeddings
   - mit einem lokalen Modell wie `nomic-embed-text`
   - geeignet, wenn semantische Ähnlichkeit stärker berücksichtigt werden soll

2. TF-IDF-Vektoren
   - als einfacher Fallback ohne zusätzliches Ollama-Modell
   - gut für eine kompakte, nachvollziehbare Demo

### 3. Clusterbildung

Die Vektoren werden mit K-Means in Gruppen unterteilt.

Damit werden ähnliche Interviews auf Basis ihrer inhaltlichen Nähe zusammengefasst.

### 4. Repräsentative Vertreter pro Cluster auswählen

Aus jedem Cluster wird mindestens ein typischer Vertreter bestimmt. Das hilft dabei, die wichtigsten Muster im Datensatz abzudecken, ohne jede einzelne Datei manuell zu prüfen.

### 5. Ausreißer identifizieren

Zusätzlich werden Dokumente mit ungewöhnlichen Inhaltseigenschaften ausgewählt. Damit werden seltene Fälle nicht übersehen, nur weil sie wenig häufig vorkommen.

Beispiel:

- ein ungewöhnlicher medizinischer Verlauf
- ein seltenes Ereignis wie ein Tauchunfall-Kontext
- ein stark abweichendes Interview im Vergleich zur Gesamtmenge

### 6. Auswahl für manuelle Ground Truth festlegen

Die Ergebnisse werden in einem Bericht zusammengefasst, z. B. in:

- `output/selection_report.json`

Dort stehen unter anderem:

- `clusters`
- `outliers`
- `recommended_for_manual_ground_truth`
- `document_metadata`

### 7. Manuelle Annotation

Nur die ausgewählten Dokumente werden gemäß einem festen Muster bewertet.

Dafür dient das Template in:

- `ground_truth/ground_truth_template.json`

Die vorhandenen Pattern-Namen entsprechen dem Gerüst der bestehenden App, z. B.:

- `beschwerden_symptome`
- `frage_antwort_struktur`
- `zeitangabe_verlauf`
- `medikamente_behandlung`
- `vorgeschichte_risikofaktoren`
- `verneinung_ausschluss`

### 8. Evaluationsdatensatz erstellen

Für jedes ausgewählte Transkript wird eine eigene JSON-Datei erstellt, zum Beispiel:

- `ground_truth/interview_003.json`
- `ground_truth/interview_008.json`
- `ground_truth/interview_012_rare.json`

Diese Dateien bilden dann den Ground-Truth-/Evaluationsdatensatz.

---

## Warum Embeddings statt direktes LLM-Clustering?

Für viele Dokumentensätze ist die Vektor- und Cluster-Variante sinnvoller als ein direktes "LLM soll Clusters bilden".

Vorteile:

- reproduzierbar
- messbar
- günstiger
- skalierbar für größere Mengen

Ein LLM kann danach optional helfen, Cluster zu beschreiben oder Vorannotationen zu erzeugen. Für die Auswahl der Ground-Truth-Stichprobe ist der Vektoransatz aber meistens klarer und robuster.

---

## Wichtige Hinweise

- Die Cluster sind nicht die Ground Truth.
- Sie dienen nur als Auswahlhilfe.
- Die Evidence muss im jeweiligen Transkript tatsächlich überprüft werden.
- Die finalen Referenzdaten sollten menschlich validiert werden.

---

## Verwendete Dateien

- `cluster_transcripts.py` – Hauptlogik für Auswahl und Sampling
- `requirements.txt` – benötigte Abhängigkeiten
- `README.md` – kurze Projektbeschreibung
- `transcripts/` – Eingabedaten
- `output/selection_report.json` – Auswahlbericht
- `ground_truth/ground_truth_template.json` – Annotationsvorlage

---

## Beispielhafte Interpretation des Outputs

Im generierten Bericht kann die Auswahl so aussehen:

- repräsentative Kandidaten aus den Clustern
- besonders auffällige Kandidaten wie `interview_008.txt`
- seltene Fälle wie `interview_012_rare.txt`

Damit wird sichergestellt, dass der Ground-Truth-Datensatz nicht nur "durchschnittliche" Fälle enthält, sondern auch atypische, aber relevante Ausprägungen.
