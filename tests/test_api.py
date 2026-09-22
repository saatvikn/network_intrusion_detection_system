import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import app


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


if __name__ == "__main__":
    unittest.main()