from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from src.predict import IntrusionDetector

import json
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware


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