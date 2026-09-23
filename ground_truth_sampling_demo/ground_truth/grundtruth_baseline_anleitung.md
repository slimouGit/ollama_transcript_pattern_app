# Ground-Truth-Baseline-Anleitung

## Ziel

Diese Anleitung beschreibt den richtigen Weg, um die erste belastbare Ground-Truth-Baseline für dieses Projekt aufzubauen. Das Ziel ist nicht, das Modell sofort zu trainieren, sondern zuerst eine saubere Referenzbasis zu schaffen, gegen die alle späteren Verbesserungen gemessen werden.

Die zentrale Idee ist einfach:

- Das Modell muss im Text exakt erkennen, welche Stelle zu welchem Muster gehört.
- Dafür braucht man belastbare Referenzdaten.
- Erst wenn diese Referenzen sauber sind, lassen sich Regeln, Filter, Prompting und spätere Modellverbesserungen sinnvoll bewerten.

---

## Grundprinzip

Dieses Projekt ist kein reines Fine-Tuning-Problem. Es ist vor allem ein Pattern-Extraction- und Evidence-Problem.

Das heißt:

- Ein Treffer ist nur dann gut, wenn er exakt im Text belegt ist.
- Die Annotation muss semantisch sauber und inhaltlich passend sein.
- Die Ground Truth ist die Messlatte für spätere Qualität.

Der richtige Ablauf ist:

1. Relevante Transkripte auswählen
2. Manuell annotieren
3. Ground Truth validieren
4. Modell gegen diese Referenz bewerten
5. Danach Regeln, Prompting und Fine-Tuning verbessern

---

## 1. Relevante Interviews auswählen

Die Auswahl soll nicht zufällig erfolgen, sondern aus einer gezielten Stichprobe stammen.

Dafür nutzt man den Bericht:

- `ground_truth_sampling_demo/output/selection_report.json`

Dieser Bericht enthält typischerweise:

- repräsentative Clustervertreter
- auffällige Sonderfälle
- seltene Ausreißer
- Empfehlungen für manuelle Ground-Truth-Erstellung

Empfohlen ist ein kleiner, sauberer Startsatz, zum Beispiel 5 bis 10 Interviews.

Wichtige Mischung:

- typische Alltagssituationen
- seltene, aber relevante Fälle
- auffällige Abweichungen

Ziel: nicht "viele Dokumente", sondern "eine gute, ausgewogene, prüfbare Auswahl".

---

## 2. Doku- und Datenstruktur festlegen

Für jedes ausgewählte Interview wird eine eigene JSON-Datei im Ground-Truth-Verzeichnis angelegt.

Als Grundlage dient die Vorlage:

- `ground_truth_sampling_demo/ground_truth/ground_truth_template.json`

Die Muster sollten mit den bereits definierten Patternnamen konsistent sein, zum Beispiel:

- `beschwerden_symptome`
- `frage_antwort_struktur`
- `zeitangabe_verlauf`
- `medikamente_behandlung`
- `vorgeschichte_risikofaktoren`
- `verneinung_ausschluss`

Jede Datei sollte sauber benannt sein, etwa:

- `interview_003.json`
- `interview_008.json`
- `interview_012_rare.json`

---

## 3. Nur echte Textstellen akzeptieren

Ein Eintrag ist nur dann gültig, wenn er streng den Regeln der Evidence-Extraktion folgt.

Ein Eintrag muss erfüllt sein:

- Die Information steht tatsächlich im Interview.
- Die Evidence stammt exakt aus dem Text.
- Die Kategorie passt sauber zur Information.
- Es gibt keine Vermutung, keine Interpretation und keinen Interpretationsspielraum.

Wichtige Ausschlüsse:

- keine "nahezu passenden" Sätze
- keine generischen Aussagen ohne direkte Textstelle
- keine breit gefassten Interpretationen
- keine Annahmen, die im Text nicht explizit vorkommen

Nur so entsteht belastbare Ground Truth.

---

## 4. Schema für jeden Ground-Truth-Eintrag

Jeder annotierte Treffer sollte im gleichen Schema vorliegen:

```json
{
  "pattern": "beschwerden_symptome",
  "evidence": "Ich habe starke Schmerzen im Rücken.",
  "explanation": "Die Patientin beschreibt konkrete Schmerzen im Rücken.",
  "confidence": 1.0
}
```

Wichtige Regeln:

- `pattern` muss ein gültiger Mustername sein
- `evidence` muss exakt aus dem Transkript stammen
- `explanation` darf nur die Begründung beschreiben, nicht interpretieren
- `confidence` kann bei menschlicher Annotation in der Regel `1.0` sein

Wenn ein Satz nur indirekt oder ungenau zugeordnet werden kann, ist er für die erste Baseline wahrscheinlich nicht geeignet.

---

## 5. Qualität vor Quantität

Am Anfang ist eine kleine, sehr saubere Ground-Truth-Baseline wertvoller als 100 fehlerhaft annotierte Beispiele.

Der Grund:

- saubere kleine Baseline ist besser messbar
- fehlerhafte Ground Truth führt zu falschen Modellentscheidungen
- spätere Verbesserungen hängen von der Qualität der Referenzdaten ab

Empfohlener Start:

- 5 bis 10 sauber annotierte Interviews
- Repräsentative Mischung aus Standard- und Sonderfällen
- vorläufige Validierung, bevor der Datensatz vergrößert wird

---

## 6. Peer-Review oder zweite Sichtprüfung

Vor der Verwendung als Ground Truth sollten die Annotationen einer zweiten Prüfung unterzogen werden.

Prüffragen:

- Passt die Evidence wirklich zum Muster?
- Ist die Textstelle exakt und nicht zu breit gewählt?
- Gibt es eine präzisere Formulierung?
- Ist ein anderer Mustername sinnvoller?
- Ist der Eintrag wirklich textbasiert und nicht interpretativ?

Dieses Review reduziert Messfehler und verhindert, dass die Baseline von inkonsistenten Annotationen dominiert wird.

---

## 7. Evaluierung gegen die Baseline

Sobald die ersten validierten JSON-Dateien vorliegen, kann das Modell gegen diese Baseline bewertet werden.

Ziel ist:

- Precision und Recall pro Muster zu berechnen
- Fehlerfälle systematisch zu analysieren
- Muster mit schlechten Ergebnissen gezielt zu verbessern

Die Baseline wird dabei nicht als Endpunkt, sondern als Referenzmaßstab verwendet.

---

## 8. Erst danach verbessern

Nach der ersten Ground-Truth-Baseline geht es in die nächste Stufe:

- Pattern-Regeln verfeinern
- Filterbedingungen präzisieren
- Prompting und Evidence-Extraktion verbessern
- bei Bedarf das Modell gezielt weiterentwickeln
- erst danach Fine-Tuning oder andere modellseitige Optimierungen in Betracht ziehen

Wichtig: Verbesserungen sollten immer anhand der bestehenden Ground Truth bewertet werden, nicht nach Bauchgefühl.

---

## Wichtigster Satz

Bessere Ergebnisse kommen nicht durch "mehr Modelltraining" zustande, sondern durch bessere Referenzdaten, sauberere Regeln und präzisere Evidence.

---

## Nächster sinnvoller Schritt

Als Nächstes sollten 3 bis 5 Interviews aus dem Sampling-Bericht ausgewählt, sauber annotiert und anschließend gegen die erste Baseline evaluiert werden.

Damit entsteht die erste belastbare Grundlage für alle späteren Iterationen und Verbesserungen.
