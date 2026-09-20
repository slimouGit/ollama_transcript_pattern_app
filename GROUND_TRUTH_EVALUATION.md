# Ground Truth, Vergleich und Metriken für die Mustererkennung

Dieses Dokument erklärt die drei zentralen Bausteine der Qualitätsbewertung für diese App:

1. Ground Truth
2. Vergleich zwischen erwarteten und gemeldeten Treffern
3. Precision, Recall und F1

---

## 1) Ground Truth

Ground Truth bedeutet die „wahre, erwartete Antwort“.

In diesem Projekt ist die Ground Truth eine manuell festgelegte Liste der Treffer, die im Interview-Transkript tatsächlich erwartet werden.

Beispiel:

```json
[
  {
    "pattern": "beschwerden_symptome",
    "evidence": "Ich habe seit zwei Wochen starke Schmerzen im Rücken."
  },
  {
    "pattern": "medikamente_behandlung",
    "evidence": "Ich nehme täglich Ibuprofen."
  }
]
```

Das ist wichtig, weil die App ohne eine solche Referenz keine objektive Bewertung machen kann. Der Modelloutput kann zwar plausibel aussehen, aber ohne Ground Truth weiß man nicht, ob er wirklich richtig ist.

### Warum ist Ground Truth wichtig?

- Sie ist der Vergleichsmaßstab.
- Sie definiert, was korrekt ist.
- Sie erlaubt die Bewertung der Modellqualität.

Ohne Ground Truth ist das Ergebnis nur subjektiv und nicht reproduzierbar.

---

## 2) Ergebnisse gegen Ground Truth vergleichen

Nachdem das Modell die Treffer erkannt hat, werden diese mit der Ground Truth verglichen.

Dazu werden die Treffer typischerweise als Paare betrachtet:

- Mustername
- Textbeleg / evidence
- ggf. auch Position oder Abschnitt im Transkript

Dann prüft man, welche Treffer:

- korrekt erkannt wurden
- fälschlich erkannt wurden
- erwartet, aber nicht erkannt wurden

### Drei Grundfälle

#### a) True Positive (TP)
Ein Treffer wurde erwartet und wurde auch korrekt erkannt.

Beispiel:
- Ground Truth: `beschwerden_symptome`
- Modell: `beschwerden_symptome`
- evidence stimmt überein

#### b) False Positive (FP)
Ein Treffer wurde vom Modell erkannt, aber in der Ground Truth nicht erwartet.

Beispiel:
- Modell meldet `verneinung_ausschluss`
- in der Ground Truth gibt es diesen Treffer nicht

#### c) False Negative (FN)
Ein Treffer war in der Ground Truth vorhanden, aber das Modell hat ihn nicht erkannt.

Beispiel:
- Ground Truth enthält ein Symptom
- Modell findet es nicht

### Warum wichtig?

Nur durch diese Klassifikation kann man die Qualität der Mustererkennung objektiv messen.

---

## 3) Precision, Recall und F1

Diese drei Kennzahlen sind Standardmetriken für Evaluierung in Informationsretrieval und Klassifikation.

### 3.1 Precision

Precision beschreibt, wie viele der vom Modell gemeldeten Treffer wirklich korrekt sind.

Formel:

$$
Precision = \frac{TP}{TP + FP}
$$

#### Interpretation

- Precision hoch = das Modell macht wenige falsche Treffer
- Precision niedrig = das Modell meldet viele falsch-positive Ergebnisse

#### Beispiel

- TP = 8
- FP = 2

Dann:

$$
Precision = \frac{8}{8 + 2} = \frac{8}{10} = 0.8
$$

Das bedeutet: 80 % der vom Modell gefundenen Treffer sind korrekt.

---

### 3.2 Recall

Recall beschreibt, wie viele der tatsächlich erwarteten Treffer das Modell auch gefunden hat.

Formel:

$$
Recall = \frac{TP}{TP + FN}
$$

#### Interpretation

- Recall hoch = das Modell findet viele der erwarteten Treffer
- Recall niedrig = das Modell lässt viele erwartete Treffer aus

#### Beispiel

- TP = 8
- FN = 3

Dann:

$$
Recall = \frac{8}{8 + 3} = \frac{8}{11} \approx 0.73
$$

Das bedeutet: Das Modell hat ungefähr 73 % der erwarteten Treffer gefunden.

---

### 3.3 F1

F1 kombiniert Precision und Recall in einer einzigen Zahl.

Formel:

$$
F1 = 2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}
$$

#### Interpretation

- F1 ist ein Gesamtmaß
- hoher F1-Wert bedeutet: gute Trefferqualität und gute Trefferabdeckung
- F1 ist besonders wichtig, wenn Precision und Recall gegeneinander ausbalanciert werden müssen

#### Beispiel

Wenn:
- Precision = 0.8
- Recall = 0.73

Dann:

$$
F1 = 2 \cdot \frac{0.8 \cdot 0.73}{0.8 + 0.73}
$$

$$
F1 \approx 0.76
$$

Das heißt: Die Gesamtleistung ist relativ gut, aber nicht perfekt.

---

## Wie das in dieser App angewendet wird

Für dieses Projekt würde man typischerweise so vorgehen:

1. Eine Ground Truth-Datei anlegen
2. Die App analysiert das Transkript
3. Die Modelltreffer werden mit der Ground Truth verglichen
4. Für alle Treffer werden TP, FP und FN bestimmt
5. Precision, Recall und F1 werden berechnet
6. Das Ergebnis wird als Gesamtwert und optional pro Muster ausgegeben

### Beispiel für pro Muster-Auswertung

```json
{
  "beschwerden_symptome": {
    "precision": 1.0,
    "recall": 0.8,
    "f1": 0.89
  },
  "medikamente_behandlung": {
    "precision": 0.75,
    "recall": 1.0,
    "f1": 0.86
  }
}
```

Das ist sehr nützlich, weil man dann erkennen kann, welche Muster gut funktionieren und welche problematisch sind.

---

## Kurzfazit

- Ground Truth = die erwartete, korrekte Antwort
- Vergleich = Modelltreffer gegen diese erwartete Antwort
- Precision = wie korrekt die Treffer sind
- Recall = wie vollständig die Treffer sind
- F1 = gemeinsames Maß für Qualität und Vollständigkeit

Diese Metriken sind der Standard, wenn man die Qualität einer Mustererkennungs-App objektiv bewerten will.
