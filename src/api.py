from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from src.predict import IntrusionDetector

import json
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

import csv
import io

from fastapi import UploadFile


# Describe the JSON body accepted by our endpoint.
class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record: dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the saved pipeline once when this server process starts.
    app.state.detector = IntrusionDetector()
    yield

    # Release the reference when the server shuts down.
    del app.state.detector


app = FastAPI(
    title="Network Intrusion Detection API",
    lifespan=lifespan,
)

# Allow our local frontend to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    # Startup must finish successfully before requests are served.
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictionRequest, request: Request):
    try:
        # Reuse our existing feature validation and prediction code.
        return request.app.state.detector.predict(payload.record)
    except ValueError as exc:
        # Invalid input should receive a useful client-error response.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/samples")
def get_samples():
    # Return the demo records and their display information.
    samples_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "demo_samples.json"
    )
    return json.loads(samples_path.read_text(encoding="utf-8"))

# Keep batches small enough for our interactive demo.
MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_BATCH_ROWS = 1000


@app.post("/predict-batch")
def predict_batch(request: Request, file: UploadFile):
    detector = request.app.state.detector

    # Read one extra byte so we can detect oversized files.
    content = file.file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=413,
            detail="The CSV must be no larger than 2 MiB.",
        )

    try:
        # utf-8-sig also handles the UTF-8 marker some editors add.
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="Save the CSV using UTF-8 encoding.",
        ) from exc

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)

        if not header:
            raise ValueError("The CSV needs a header row.")

        if len(header) != len(set(header)):
            raise ValueError("The CSV contains duplicate column names.")

        # Require exactly the model's input features.
        missing = set(detector.feature_columns) - set(header)
        extra = set(header) - set(detector.feature_columns)
        if missing or extra:
            raise ValueError(
                f"Missing columns: {sorted(missing)}; "
                f"unexpected columns: {sorted(extra)}"
            )

        records = []

        for row_number, values in enumerate(reader, start=1):
            if row_number > MAX_BATCH_ROWS:
                raise ValueError("A batch can contain at most 1,000 records.")

            if len(values) != len(header):
                raise ValueError(
                    f"Record {row_number}: wrong number of fields."
                )

            record = dict(zip(header, values))

            # CSV values arrive as text; convert numeric features.
            for column in detector.numeric_columns:
                try:
                    record[column] = float(record[column])
                except ValueError as exc:
                    raise ValueError(
                        f"Record {row_number}: {column} must be a number."
                    ) from exc

            records.append(record)

        # This also rejects empty batches and invalid feature values.
        predictions = detector.predict_many(records)

    except (ValueError, csv.Error) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    attack_count = sum(
        prediction["prediction"] == "attack"
        for prediction in predictions
    )

    return {
        "summary": {
            "total": len(predictions),
            "normal": len(predictions) - attack_count,
            "attack": attack_count,
        },
        "results": [
            {"row": row_number, **prediction}
            for row_number, prediction in enumerate(predictions, start=1)
        ],
    }