# Transcript Pattern Analyzer mit Ollama

Kleine lokale FastAPI-App für folgenden Use Case:

1. Das bestehende Interview-Transkript aus `data/interview.txt` laden
2. Das Transkript mit einem lokalen Ollama-Modell analysieren
3. Vordefinierte Muster mit Textbeleg, Begründung und Confidence ausgeben

## Architektur

```text
data/interview.txt
  |
  v
FastAPI
    |
    v
Ollama /api/chat
    |
    v
JSON: pattern + evidence + explanation + confidence
```

## 1. Ollama vorbereiten

Ollama starten:

```bash
ollama serve
```

Modell herunterladen, zum Beispiel:

```bash
ollama pull qwen2.5:7b
```

Wenn du ein anderes Modell verwenden willst:

Windows PowerShell:

```powershell
$env:OLLAMA_MODEL="granite3.3:8b"
```

Linux/macOS:

```bash
export OLLAMA_MODEL="granite3.3:8b"
```

## 2. Python-Umgebung

```bash
python -m venv .venvSS  
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Dann:

```bash
pip install -r requirements.txt
```

## 3. App starten

Im Projektordner:

```bash
uvicorn app.main:app --reload
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

```

Danach öffnen:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Interview analysieren

Die Browser-Oberfläche lädt automatisch `data/interview.txt`. Mit **Interview analysieren** wird genau dieses Transkript nach den definierten Mustern durchsucht.

Die API stellt zusätzlich `GET /health` und `GET /transcript` bereit. Die Analyse wird über `POST /analyze-interview` gestartet.

## Wichtige Dateien

- `app/main.py` – FastAPI-Endpunkte
- `app/ollama_client.py` – Ollama-Anbindung
- `app/analyzer.py` – Prompt und Musterlogik
- `app/schemas.py` – Ergebnis-Datenmodelle
- `templates/index.html` – einfache Browser-Oberfläche

## Hinweis für echte Interviewdaten

Bei echten personenbezogenen Interviewdaten sollte die gesamte Verarbeitung lokal bzw. in der freigegebenen Projektumgebung erfolgen. Dieses Beispiel sendet nichts an einen externen Cloud-Dienst; Ollama und Whisper laufen lokal.
