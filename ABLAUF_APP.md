# Ablauf der App: vom Seitenaufruf bis zur Evaluation

Dieses Dokument beschreibt den aktuellen Ablauf der App. Analyse und Evaluation sind getrennt: Ollama wird nur während der Analyse aufgerufen. Die Evaluation arbeitet anschließend mit dem gespeicherten Analyseergebnis.

## 1. Seite wird geladen

1. Der Browser ruft `GET /` auf.
2. FastAPI liefert [templates/index.html](templates/index.html).
3. Das Frontend startet parallel:
   - `GET /transcript`
   - `GET /models`
   - `GET /device-info`

## 2. Transkript und Modelle laden

### Transkript

1. `GET /transcript` ruft in [app/main.py](app/main.py) `read_transcript()` auf.
2. `data/interview.txt` wird gelesen.
3. Das Frontend setzt den Inhalt in das bearbeitbare Feld `#transcript`.
4. Unterhalb des Textfelds wird die aktuelle Zeichenanzahl angezeigt.

### Modelle

1. `GET /models` ruft `available_models()` auf.
2. Der Backend-Client fragt Ollama über `GET /api/tags` ab.
3. Die lokal installierten Modellnamen werden an das Frontend zurückgegeben.
4. Das Frontend füllt damit die Modellauswahl.

## 3. Nutzer wählt Analyse-Einstellungen

Vor dem Start kann der Nutzer festlegen:

- Ollama-Modell
- Verarbeitungsmodus: automatisch, GPU bevorzugen oder nur CPU
- Timeout in Sekunden
- Chunk-Größe in Zeichen
- Temperatur
- Top-K
- Top-P
- Seed
- maximale Ausgabetokens

Die Werte gelten nur für den nächsten Analyseaufruf. Das Frontend führt keine Shell-Befehle aus.

## 4. Analyse starten

Beim Klick auf "Interview analysieren" führt `analyzeInterview()` aus [templates/index.html](templates/index.html) folgende Schritte aus:

1. Status auf "Analysiere Interview..." setzen.
2. Alte Ergebnis- und Evaluationsanzeige leeren.
3. Einen JSON-Request an `POST /analyze-interview` senden:

```json
{
  "model": "qwen2.5:7b",
   "device": "auto",
   "timeout": 300,
      "chunk_size": 2000,
      "temperature": 0,
      "top_k": 1,
      "top_p": 1,
      "seed": 42,
      "output_tokens": 512
}
```

Die Werte sind Beispiele für einen robusten Analyse-Lauf. Die Standardwerte in
[app/config.py](app/config.py) sind ein Timeout von 120 Sekunden und eine Chunk-Größe von
2000 Zeichen. Bei langsamen lokalen Modellen können ein höheres Timeout und kleinere Chunks
verwendet werden.

## 5. Backend validiert die Optionen

In [app/main.py](app/main.py) wird `AnalysisRequest` aus [app/schemas.py](app/schemas.py) verwendet:

- `model` ist optional.
- `timeout` liegt zwischen 5 und 600 Sekunden.
- `chunk_size` liegt zwischen 500 und 20.000 Zeichen.

Nicht gesetzte Werte verwenden die Standardkonfiguration aus [app/config.py](app/config.py).
Im Modus `auto` entscheidet Ollama selbst über GPU- und CPU-Nutzung. `gpu` bevorzugt
GPU-Modelllayer, während `cpu` die GPU-Nutzung deaktiviert. Der angeforderte Modus wird
getrennt vom erkannten Laufzeitmodus gespeichert.

## 6. Hardware- und Device-Informationen

`GET /device-info` ermittelt CPU-Name, GPU-Name, GPU-Erkennung, VRAM, RAM und das
ausgewählte Modell. Nach einer Analyse wird zusätzlich Ollamas `GET /api/ps` geprüft.
Wenn dort keine zuverlässige Zuordnung möglich ist, wird der tatsächliche Laufzeitmodus
als `unknown` angezeigt. Das Frontend zeigt angefordert und tatsächlich genutzt getrennt.

## 7. Transkript in Chunks aufteilen

1. `read_transcript()` liest das Interview erneut.
2. `analyze_transcript()` in [app/analyzer.py](app/analyzer.py) ruft `chunk_text()` auf.
3. `split_sentences()` zerlegt das Transkript in Sätze und schützt Abkürzungen wie "Dr.".
4. `chunk_text()` bildet Abschnitte entsprechend der gewählten Chunk-Größe.

Eine größere Chunk-Größe reduziert die Anzahl der Ollama-Aufrufe, kann aber die Modellantwort verlangsamen. Eine kleinere Chunk-Größe erzeugt mehr, dafür kleinere Aufrufe.
Die Chunks werden nacheinander vollständig verarbeitet. Standardmäßig gibt es keinen Satz-Overlap
zwischen aufeinanderfolgenden Chunks.

## 8. Jeden Chunk mit Ollama analysieren

Für jeden Chunk läuft `analyze_chunk()`:

1. `build_user_prompt()` erstellt den Prompt aus den Musterdefinitionen.
2. `chat_json()` aus [app/ollama_client.py](app/ollama_client.py) sendet `POST /api/chat` an Ollama.
3. Übergeben werden:
   - System-Prompt
   - Chunk als User-Prompt
   - gewähltes Modell
   - gewähltes Timeout
   - JSON-Ausgabeformat
   - die im Frontend gesetzten Sampling-Parameter
4. Erwartete Trefferfelder sind:
   - `pattern`
   - `evidence`
   - `explanation`
   - `confidence`

Die `PatternDefinition`-Einträge in [app/patterns.py](app/patterns.py) sind fachliche
Beschreibungen, die in den Prompt übernommen werden. Sie prüfen den Text nicht selbst
regelbasiert. Die eigentliche Zuordnung eines Textausschnitts zu einem Muster übernimmt
Ollama. Die App prüft danach nur technisch und teilweise regelbasiert, ob:

- der Pattern-Name erlaubt ist,
- die Evidence im aktuellen Chunk vorkommt,
- die Evidence nicht leer oder zu lang ist,
- zusätzliche Filterregeln für Medikamente und Verneinungen erfüllt sind.

Die gültigen Treffer aus allen Chunks werden gesammelt, anschließend teilweise dedupliziert
und in `latest_analysis` gespeichert.

## 9. Modellantwort filtern

Die Antwort wird in `Match`-Objekte validiert. Danach werden nur Treffer akzeptiert, die:

- ein erlaubtes Muster verwenden,
- einen kurzen Evidence-Text enthalten,
- Evidence aus dem aktuellen Chunk enthalten,
- keine unzulässige Länge überschreiten,
- bei Medikamenten einen Einnahme-, Anwendungs-, Wirkungs- oder ausdrücklich verneinten
   Medikamentenkontext enthalten,
- bei Verneinungen einen erkennbaren medizinischen Ausschluss oder Antwortkontext enthalten.

Aktuell werden sechs Muster verwendet, darunter `frage_antwort_struktur`. Die Musterdefinitionen
stehen in [app/patterns.py](app/patterns.py). Der Prompt fordert eine systematische Prüfung aller
Muster und erlaubt mehrere Treffer pro Muster sowie die Zuordnung einer Textstelle zu mehreren
Mustern.

## 10. Treffer zusammenführen

1. Treffer aus allen Chunks werden gesammelt.
2. `remove_duplicate_matches()` normalisiert die Evidence-Texte.
3. Identische oder vollständig überlappende Evidence wird entfernt. Dadurch können sehr ähnliche
   Treffer zusammenfallen; die aktuelle Deduplizierung berücksichtigt dabei nicht den Pattern-Namen.
4. Das Ergebnis wird als `AnalysisResponse` zurückgegeben.

## 11. Analyse speichern und anzeigen

1. Das Backend speichert das Ergebnis in `latest_analysis`.
2. Die Antwort enthält:
   - Transkript
   - Trefferliste
   - verwendetes Modell
3. Während der Anfrage zeigt das Frontend Spinner, Laufzeit und Statusphase.
4. Während Analyse und Evaluation werden Eingabefelder und Startbutton deaktiviert.
5. Nach Abschluss rendert das Frontend jeden Treffer mit Muster, Evidence, Erklärung und Confidence.
4. Fehlt die Confidence in der Modellantwort, wird "nicht verfügbar" angezeigt. Es wird kein künstlicher Wert wie 50 Prozent erzeugt.

## 12. Evaluation nach abgeschlossener Analyse

Erst wenn die Analyse erfolgreich war, ruft das Frontend `GET /evaluate` auf.

1. Das Backend prüft, ob `latest_analysis` vorhanden ist.
2. Falls nicht, wird `409` mit "Bitte zuerst die Analyse ausführen" zurückgegeben.
3. Falls vorhanden, wird die Ground Truth aus `data/ground_truth.json` geladen.
4. Die gespeicherten Analyse-Treffer werden mit der Ground Truth verglichen.
5. `evaluate_matches()` berechnet:
   - True Positives
   - False Positives
   - False Negatives
   - Precision
   - Recall
   - F1
6. Während der Evaluation wird kein Ollama-Aufruf gestartet.
7. Der vollständige Bericht wird in `analysis_results/` als UTF-8-Textdatei mit Zeitstempel gespeichert.
   Er enthält Modell, Parameter, Dauer, Chunk-Metadaten, Device-Informationen, Treffer und Metriken.

## 13. Fehlerfälle

- Leeres oder fehlendes Transkript: HTTP-Fehler beim Lesen.
- Nicht erreichbares Ollama oder Timeout: HTTP `503`; es werden keine Fallback-Treffer erzeugt.
- Ungültige Einstellungen: Validierungsfehler durch `AnalysisRequest`.
- Evaluation vor Analyse: HTTP `409`.
- Nicht zuverlässig ermittelbarer Ollama-Laufzeitmodus: Anzeige und Bericht verwenden `unknown`.

## Kurz gesagt

```text
Seite laden
-> /transcript, /models und /device-info
-> Nutzer bearbeitet Transkript und wählt Modell, Device, Sampling und Chunk-Parameter
-> POST /analyze-interview
-> Spinner, Statusphase und Laufzeitzähler anzeigen
-> Optionen validieren
-> Transkript lesen und chunken
-> jeden Chunk an Ollama senden
-> Treffer validieren und filtern
-> Duplikate entfernen
-> Analyse speichern und anzeigen
-> GET /evaluate
-> gespeicherte Treffer mit Ground Truth vergleichen
-> Metriken und Bericht speichern
-> Ergebnisse, Evaluation und Device-Informationen anzeigen
```
