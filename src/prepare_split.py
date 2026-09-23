from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    source_path = (PROJECT_ROOT / "data" / "raw" / "UNSW_NB15_training-set.csv")
    output_path = (PROJECT_ROOT / "data" / "processed" / "train_validation_split.csv")

    source_df = pd.read_csv(source_path)

    if not source_df["id"].is_unique:
        raise ValueError("Training records must have unique IDs.")

    # Reproduce the notebook's original 42-feature grouping.
    candidate_inputs = source_df.drop(
        columns=["id", "attack_cat", "label"]
    )
    groups = source_df.groupby(
        candidate_inputs.columns.tolist(),
        dropna=False,
        sort=False,
    ).ngroup()

    # Keep identical input patterns together, as in the notebook.
    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )
    training_indices, validation_indices = next(
        splitter.split(
            X=candidate_inputs,
            y=source_df["label"],
            groups=groups,
        )
    )

    # Ensure no input group appears in both partitions.
    training_groups = set(groups.iloc[training_indices])
    validation_groups = set(groups.iloc[validation_indices])

    if training_groups.intersection(validation_groups):
        raise ValueError("An input group appears in both partitions.")

    assignments = source_df[["id"]].copy()
    assignments["partition"] = "training"
    assignments.loc[validation_indices, "partition"] = "validation"

    if output_path.exists():
        # Verify against the original split before changing anything.
        existing = pd.read_csv(output_path)

        try:
            pd.testing.assert_frame_equal(existing, assignments)
        except AssertionError as exc:
            raise ValueError(
                "The recreated split differs from the saved split. "
                "The existing file has been preserved."
            ) from exc

        print("Recreated split matches the existing file exactly.")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        assignments.to_csv(output_path, index=False)
        print("Saved:", output_path)

    print(assignments["partition"].value_counts())


if __name__ == "__main__":
    main()