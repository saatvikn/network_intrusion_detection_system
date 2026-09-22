import platform
from importlib.metadata import version
from pathlib import Path

import joblib
import pandas as pd

from src.model import build_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    # Load development data and the split chosen during experimentation.
    source_df = pd.read_csv(
        PROJECT_ROOT / "data" / "raw" / "UNSW_NB15_training-set.csv"
    )
    assignments = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "train_validation_split.csv"
    )

    # Ensure the saved assignments match the source records.
    if not source_df["id"].is_unique or not assignments["id"].is_unique:
        raise ValueError("Source and split IDs must be unique.")

    if set(source_df["id"]) != set(assignments["id"]):
        raise ValueError("Split assignments do not match the source IDs.")

    if set(assignments["partition"]) != {"training", "validation"}:
        raise ValueError("Expected training and validation partitions.")

    # Preserve source-row order while selecting only training records.
    training_ids = assignments.loc[
        assignments["partition"].eq("training"), "id"
    ]
    training_df = source_df.loc[
        source_df["id"].isin(training_ids)
    ].copy()

    # Apply the same feature exclusions used in the notebook.
    X_train = training_df.drop(
        columns=["id", "attack_cat", "label", "is_ftp_login"]
    )
    y_train = training_df["label"].copy()

    categorical_columns = ["proto", "service", "state"]
    numerical_columns = X_train.select_dtypes(
        include="number"
    ).columns.tolist()

    if set(categorical_columns + numerical_columns) != set(X_train.columns):
        raise ValueError("Some input columns have unexpected data types.")

    # Build a fresh pipeline and learn its settings from training data.
    pipeline = build_pipeline(numerical_columns, categorical_columns)

    print(
        f"Training on {len(X_train):,} records "
        f"with {X_train.shape[1]} input features..."
    )
    pipeline.fit(X_train, y_train)

    # Use the same artifact structure expected by IntrusionDetector.
    bundle = {
        "pipeline": pipeline,
        "threshold": 0.5,
        "positive_label": 1,
        "feature_columns": X_train.columns.tolist(),
        "categorical_columns": categorical_columns,
        "numerical_columns": numerical_columns,
        "versions": {
            "python": platform.python_version(),
            **{
                package: version(package)
                for package in [
                    "scikit-learn", "xgboost", "pandas",
                    "numpy", "scipy", "joblib",
                ]
            },
        },
    }

    # Save the artifact used by the prediction code.
    output_path = PROJECT_ROOT / "models" / "intrusion_detector.joblib"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output_path, compress=3)

    print("Saved:", output_path)


if __name__ == "__main__":
    main()