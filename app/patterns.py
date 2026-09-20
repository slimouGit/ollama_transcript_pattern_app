from .schemas import PatternDefinition


DEFAULT_PATTERNS = [
    PatternDefinition(
        name="beschwerden_symptome",
        description="Konkrete aktuelle Beschwerden oder Symptome der Patientin, zum Beispiel Schmerzen, Atemnot, Übelkeit oder Ausstrahlung. Keine bloßen Fragen oder allgemeinen Aussagen.",
    ),
    PatternDefinition(
        name="frage_antwort_struktur",
        description="Eine explizite oder sprachlich eindeutig erkennbare Frage mit der direkt anschließenden inhaltlichen Antwort der Patientin. Die Frage und Antwort müssen im Text vorkommen.",
    ),
    PatternDefinition(
        name="zeitangabe_verlauf",
        description="Konkrete Angaben zu Beginn, Dauer, Häufigkeit oder Veränderung eines Symptoms, einer Behandlung oder eines früheren Ereignisses. Dazu gehören auch Zeitpunkte wie 'vor einer halben Stunde', Zeiträume wie 'vor sieben Jahren', Häufigkeiten wie 'ab und zu' sowie Verbesserungen oder Verschlechterungen. Keine isolierten Wörter ohne zeitlichen oder verlaufsbezogenen Zusammenhang.",
    ),
    PatternDefinition(
        name="medikamente_behandlung",
        description="Konkrete Einnahme, Anwendung oder Wirkung eines Medikaments sowie eine konkrete Therapie oder Behandlung der Patientin. Auch die ausdrückliche Verneinung regelmäßiger oder sonstiger Medikamenteneinnahme zählt, wenn sie eine Medikamentenfrage beantwortet. Medikamentennamen wie Ibuprofen, Lysara oder Johanniskraut sowie Aussagen über das Wirken einer Tablette sind relevante Treffer. Ein Arztname, eine allgemeine Frage oder eine reine Drogenaussage ohne Medikamentenbezug zählt nicht.",
    ),
    PatternDefinition(
        name="vorgeschichte_risikofaktoren",
        description="Relevante eigene Vorerkrankungen, eigene Operationen, persönliche Risikofaktoren oder ausdrücklich genannte familiäre Vorerkrankungen mit möglicher medizinischer Bedeutung, zum Beispiel Schlaganfall, Hirnblutung, Herzinfarkt oder Krebs in der Familie. Irrelevante Familieninformationen nicht markieren.",
    ),
    PatternDefinition(
        name="verneinung_ausschluss",
        description="Eine ausdrücklich verneinte oder ausgeschlossene medizinische Aussage, zum Beispiel keine Vorerkrankungen, keine Medikamente, keine Medikamentenallergie, keine Drogen oder kein eigenes relevantes Leiden. Auch Aussagen wie 'das nicht', 'gesund' oder 'es geht ihm gut' zählen, wenn sie im medizinischen Frage-Antwort-Kontext einen Ausschluss beantworten. Soziale Angaben wie 'nicht verheiratet' sind niemals Treffer. Ein isoliertes allgemeines 'nein' ohne erkennbaren Bezug reicht nicht.",
    ),
]
