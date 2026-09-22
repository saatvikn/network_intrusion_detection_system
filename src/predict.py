import argparse
import json
import math
from numbers import Real
from pathlib import Path

import joblib
import pandas as pd


# Resolve the model path relative to this file, not the terminal location.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "intrusion_detector.joblib"


class IntrusionDetector:
    def __init__(self, model_path=MODEL_PATH):
        # Load our trusted, locally created artifact once.
        bundle = joblib.load(model_path)

        self.pipeline = bundle["pipeline"]
        self.threshold = bundle["threshold"]
        self.feature_columns = bundle["feature_columns"]
        self.numeric_columns = bundle["numerical_columns"]
        self.categorical_columns = bundle["categorical_columns"]

        self.attack_column = list(self.pipeline.classes_).index(
            bundle["positive_label"]
        )

    def predict(self, record):
        # Require one record containing exactly the expected input fields.
        if not isinstance(record, dict):
            raise ValueError("The input must be a JSON object.")

        missing = set(self.feature_columns) - set(record)
        extra = set(record) - set(self.feature_columns)

        if missing or extra:
            raise ValueError(
                f"Missing fields: {sorted(missing)}; "
                f"unexpected fields: {sorted(extra)}"
            )

        # Reject invalid numbers rather than silently treating them as missing.
        for column in self.numeric_columns:
            value = record[column]
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
            ):
                raise ValueError(f"{column} must be a finite number.")

        # Categories must be nonempty strings; unseen categories are allowed.
        for column in self.categorical_columns:
            value = record[column]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{column} must be a nonempty string.")

        # Restore training column order and apply the fitted pipeline.
        frame = pd.DataFrame([record], columns=self.feature_columns)
        probability = float(
            self.pipeline.predict_proba(frame)[0, self.attack_column]
        )

        return {
            "prediction": (
                "attack" if probability > self.threshold else "normal"
            ),
            "attack_probability": probability,
            "threshold": float(self.threshold),
        }


if __name__ == "__main__":
    # This block runs when invoked with: python -m src.predict
    parser = argparse.ArgumentParser(
        description="Predict intrusion from one network-feature record."
    )
    parser.add_argument("record_path", type=Path)
    args = parser.parse_args()

    record = json.loads(args.record_path.read_text(encoding="utf-8"))
    detector = IntrusionDetector()

    print(json.dumps(detector.predict(record), indent=2))