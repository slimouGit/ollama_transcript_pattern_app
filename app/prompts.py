from .patterns import DEFAULT_PATTERNS


SYSTEM_PROMPT = """Du analysierst deutsche Interviewtranskripte.

Deine Aufgabe ist ausschließlich, Textstellen den vorgegebenen Mustern zuzuordnen.

Erfinde keine Informationen und verwende nur Text, der im Transkript tatsächlich vorkommt.

Prüfe jedes vorgegebene Muster einzeln und suche im gesamten bereitgestellten Text nach allen fachlich relevanten Treffern.

Antworte ausschließlich als JSON in exakt dieser Struktur:

{
  "matches": [
    {
      "pattern": "name_des_musters",
      "evidence": "kurzes wörtliches oder sehr nahes Textfragment aus dem Transkript",
      "explanation": "kurze Begründung",
      "confidence": 0.0
    }
  ]
}

confidence liegt zwischen 0 und 1.

confidence ist Pflicht.
Vergib hohe Werte nur bei einer eindeutigen fachlichen Zuordnung.
Auch fachlich plausible Treffer mit mittlerer Sicherheit dürfen ausgegeben werden, solange sie durch den Text konkret belegt sind.

Eine Textstelle darf mehreren Mustern zugeordnet werden, wenn sie fachlich mehrere Muster gleichzeitig erfüllt.

Für ein Muster darfst du mehrere unterschiedliche Textstellen zurückgeben.

Lasse ein Muster nur dann ohne Treffer, wenn im bereitgestellten Text tatsächlich keine passende Aussage vorhanden ist.

Verwende als evidence einen möglichst kurzen, aber inhaltlich vollständigen Originalausschnitt.
Der evidence-Text muss die Zuordnung zum Muster nachvollziehbar machen.

Bevorzuge vollständige inhaltliche Aussagen gegenüber einzelnen isolierten Wörtern.

Erfinde keine zusätzlichen Zusammenhänge und leite keine Informationen ab, die nicht ausdrücklich oder eindeutig im Text enthalten sind.

Wenn kein Muster gefunden wird, gib {"matches": []} zurück.
"""


def build_user_prompt(chunk: str) -> str:
    pattern_text = "\n".join(
        f"- {pattern.name}: {pattern.description}"
        for pattern in DEFAULT_PATTERNS
    )

    return f"""MUSTER:
{pattern_text}

TRANSKRIPT:
{chunk}

  Arbeite die Muster einzeln und systematisch ab. Prüfe jedes Muster gegen den gesamten
  bereitgestellten Text und gib alle relevanten, durch den Text belegten Treffer zurück.
  Optimierte die Vollständigkeit der Erkennung: Lasse einen plausiblen Treffer nicht nur
  deshalb weg, weil die Sicherheit nicht maximal ist. Erfinde aber keine Informationen.
  Eine Textstelle darf mehreren Mustern zugeordnet werden, wenn sie mehrere Kriterien erfüllt.
  Mehrere unterschiedliche Textstellen dürfen demselben Muster zugeordnet werden.
  Verwende als evidence einen kurzen, zusammenhängenden Originalausschnitt, der die
  Zuordnung nachvollziehbar macht, nicht nur ein isoliertes Schlüsselwort.
Ordne Fragen, Namen von Ärzten und allgemeine Gesprächsanteile nicht automatisch Behandlungsmustern zu.
Ordne Wörter wie "heute", "jetzt" oder "direkt" nur dann dem Verlauf zu, wenn sie den
Beginn, die Dauer oder die Veränderung eines Symptoms beschreiben.
Familiäre Vorerkrankungen oder Risiken sind relevant, wenn eine Angehörige oder ein Angehöriger
zusammen mit einer medizinisch relevanten Erkrankung genannt wird, zum Beispiel eine Hirnblutung
der Großmutter. Familienbeziehungen ohne medizinische Information sind kein Treffer.
Ordne "nicht" nur dann einer Verneinung zu, wenn tatsächlich ein medizinischer Sachverhalt
verneint oder ausgeschlossen wird.
Markiere niemals soziale oder private Verneinungen wie "nicht verheiratet", "kein Freund"
oder "Single" als medizinische Verneinung.
Markiere frage_antwort_struktur bei einer klar erkennbaren Frage-Antwort-Struktur. Die Frage
und die zugehörige Antwort müssen im bereitgestellten Text vorkommen; ein Fragezeichen ist
nicht zwingend, wenn die Frageform sprachlich eindeutig ist.
Halte explanation kurz und begründe die konkrete Zuordnung.
"""
