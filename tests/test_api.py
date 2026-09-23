import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import app

import csv
import io

class TestPredictionAPI(unittest.TestCase):
    def setUp(self):
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "example_record.json"
        )
        self.record = json.loads(
            fixture_path.read_text(encoding="utf-8")
        )

    def test_valid_request_matches_predictor(self):
        # Starting the test client also runs our model-loading code.
        with TestClient(app) as client:
            expected = app.state.detector.predict(self.record)
            response = client.post(
                "/predict", json={"record": self.record}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_missing_feature_returns_422(self):
        del self.record["sbytes"]

        with TestClient(app) as client:
            response = client.post(
                "/predict", json={"record": self.record}
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("sbytes", response.json()["detail"])

    @staticmethod
    def _make_csv(records):
        buffer = io.StringIO(newline="")

        # Reverse columns to verify that names, not positions, are used.
        writer = csv.DictWriter(
            buffer,
            fieldnames=list(reversed(records[0])),
        )
        writer.writeheader()
        writer.writerows(records)
        return buffer.getvalue().encode("utf-8")

    def test_batch_matches_individual_predictions(self):
        samples_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "demo_samples.json"
        )
        samples = json.loads(samples_path.read_text(encoding="utf-8"))
        records = [sample["record"] for sample in samples]

        with TestClient(app) as client:
            expected = [
                app.state.detector.predict(record)
                for record in records
            ]
            response = client.post(
                "/predict-batch",
                files={
                    "file": (
                        "flows.csv",
                        self._make_csv(records),
                        "text/csv",
                    )
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["results"]), len(records))

        for row_number, (actual, reference) in enumerate(
            zip(body["results"], expected), start=1
        ):
            self.assertEqual(actual["row"], row_number)
            self.assertEqual(
                actual["prediction"], reference["prediction"]
            )
            self.assertAlmostEqual(
                actual["attack_probability"],
                reference["attack_probability"],
                places=6,
            )
            self.assertEqual(actual["threshold"], reference["threshold"])

        attack_count = sum(
            item["prediction"] == "attack" for item in expected
        )
        self.assertEqual(
            body["summary"],
            {
                "total": len(records),
                "normal": len(records) - attack_count,
                "attack": attack_count,
            },
        )

    def test_invalid_batch_record_returns_422(self):
        invalid_record = self.record.copy()
        invalid_record["sbytes"] = "not-a-number"

        with TestClient(app) as client:
            response = client.post(
                "/predict-batch",
                files={
                    "file": (
                        "invalid.csv",
                        self._make_csv([self.record, invalid_record]),
                        "text/csv",
                    )
                },
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Record 2", response.json()["detail"])
        self.assertIn("sbytes", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()