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

    def _validate_record(self, record):
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

    def predict_many(self, records):
        # Require at least one network-flow record.
        if not isinstance(records, list) or not records:
            raise ValueError("Provide a nonempty list of records.")

        # Validate every record before running the model.
        for row_number, record in enumerate(records, start=1):
            try:
                self._validate_record(record)
            except ValueError as exc:
                raise ValueError(
                    f"Record {row_number}: {exc}"
                ) from exc

        # Each dictionary becomes one row, in the supplied order.
        frame = pd.DataFrame(records, columns=self.feature_columns)

        # Run preprocessing and prediction once for the entire batch.
        probabilities = self.pipeline.predict_proba(frame)[:, self.attack_column]

        # Return one result per input record, preserving its position.
        return [
            {
                "prediction": (
                    "attack"
                    if float(probability) > self.threshold
                    else "normal"
                ),
                "attack_probability": float(probability),
                "threshold": float(self.threshold),
            }
            for probability in probabilities
        ]
    
    def predict(self, record):
        # Treat a single prediction as a batch containing one record.
        return self.predict_many([record])[0]


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