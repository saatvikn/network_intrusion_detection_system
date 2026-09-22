from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier


def build_pipeline(numerical_columns, categorical_columns):
    """Create an unfitted pipeline using our selected configuration."""

    # Keep numerical values unchanged and encode categorical values.
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", numerical_columns),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_columns,
            ),
        ],
        # Keep zeros explicitly stored for XGBoost.
        sparse_threshold=0,
    )

    # Use the settings selected during our notebook experiments.
    classifier = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        objective="binary:logistic",
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )