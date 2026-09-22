import unittest

from app.analyzer import remove_duplicate_matches
from app.schemas import Match


class RemoveDuplicateMatchesTests(unittest.TestCase):
    def test_keeps_same_evidence_across_different_patterns(self):
        matches = [
            Match(
                pattern="beschwerden_symptome",
                evidence="Schmerzen im Rücken",
                explanation="symptom",
                confidence=0.9,
            ),
            Match(
                pattern="medikamente_behandlung",
                evidence="Schmerzen im Rücken",
                explanation="treatment",
                confidence=0.8,
            ),
        ]

        result = remove_duplicate_matches(matches)

        self.assertEqual(len(result), 2)
        self.assertEqual({m.pattern for m in result}, {"beschwerden_symptome", "medikamente_behandlung"})

    def test_removes_duplicates_for_same_pattern_and_same_evidence(self):
        matches = [
            Match(
                pattern="beschwerden_symptome",
                evidence="Schmerzen im Rücken",
                explanation="first",
                confidence=0.9,
            ),
            Match(
                pattern="beschwerden_symptome",
                evidence="Schmerzen im Rücken",
                explanation="second",
                confidence=0.8,
            ),
        ]

        result = remove_duplicate_matches(matches)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pattern, "beschwerden_symptome")


if __name__ == "__main__":
    unittest.main()
