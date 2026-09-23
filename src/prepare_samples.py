import json
from pathlib import Path

import pandas as pd

from src.predict import IntrusionDetector


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    # Read the benchmark data used for our completed test evaluation.
    test_df = pd.read_csv(
        PROJECT_ROOT / "data" / "raw" / "UNSW_NB15_testing-set.csv"
    )

    # Use the saved model's exact input-column list.
    detector = IntrusionDetector()
    samples = []

    for category in ["Normal", "Fuzzers", "Exploits"]:
        # A fixed seed makes the example selection repeatable.
        selected = test_df.loc[
            test_df["attack_cat"].eq(category)
        ].sample(n=2, random_state=42)

        for row in selected.to_dict(orient="records"):
            samples.append({
                "id": int(row["id"]),
                "name": f"{category} example — flow {row['id']}",
                "actual_label": (
                    "attack" if row["label"] == 1 else "normal"
                ),
                "attack_category": category,
                # Only these features will be sent to /predict.
                "record": {
                    column: row[column]
                    for column in detector.feature_columns
                },
            })

    output_path = PROJECT_ROOT / "data" / "demo_samples.json"
    output_path.write_text(
        json.dumps(samples, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    # Export the same six examples with input features only.
    csv_path = PROJECT_ROOT / "data" / "demo_flows.csv"
    pd.DataFrame(
        [sample["record"] for sample in samples],
        columns=detector.feature_columns,
    ).to_csv(csv_path, index=False)

    print(f"Saved example CSV to {csv_path}")

    print(f"Saved {len(samples)} demo samples to {output_path}")


if __name__ == "__main__":
    main()