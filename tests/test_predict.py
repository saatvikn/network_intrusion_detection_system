import json
import unittest
from pathlib import Path

from src.predict import IntrusionDetector


class TestIntrusionDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the saved model and example once for this test class.
        cls.detector = IntrusionDetector()

        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "example_record.json"
        )
        cls.record = json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_valid_record_returns_prediction(self):
        result = self.detector.predict(self.record)

        self.assertEqual(
            set(result),
            {"prediction", "attack_probability", "threshold"},
        )
        self.assertIn(result["prediction"], {"normal", "attack"})
        self.assertGreaterEqual(result["attack_probability"], 0.0)
        self.assertLessEqual(result["attack_probability"], 1.0)

    def test_missing_field_is_rejected(self):
        record = self.record.copy()
        del record["sbytes"]

        with self.assertRaisesRegex(ValueError, "Missing fields"):
            self.detector.predict(record)

    def test_nonfinite_number_is_rejected(self):
        record = self.record.copy()
        record["sbytes"] = float("nan")

        with self.assertRaisesRegex(ValueError, "finite number"):
            self.detector.predict(record)

    def test_unseen_category_is_accepted(self):
        record = self.record.copy()
        record["proto"] = "__unseen_protocol__"

        result = self.detector.predict(record)
        self.assertIn(result["prediction"], {"normal", "attack"})

    def test_field_order_does_not_change_prediction(self):
        reordered = dict(reversed(list(self.record.items())))

        self.assertEqual(
            self.detector.predict(self.record),
            self.detector.predict(reordered),
        )


if __name__ == "__main__":
    unittest.main()