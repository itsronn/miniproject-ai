"""
Backend for AI Learning Screening.
Serves prediction endpoints. Replace stub logic with real model inference when ready.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
import subprocess
import sys
import re
import ast

app = FastAPI(title="AI Learning Screening API")

# Allow frontend (Vite dev server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/response models ---

class CognitiveInput(BaseModel):
    reactionTimes: list[float]
    averageMs: float


class FinalInput(BaseModel):
    handwriting: float | None
    speech: float | None
    eye: float | None
    cognitive: float | None


# --- Model inference (calls your friend's scripts under ../models) ---

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_ROOT = Path(
    # Allow override if you ever move the models folder
    sys.environ.get("MODELS_ROOT", str(REPO_ROOT / "models"))
)

SPEECH_DIR = MODELS_ROOT / "audio-test-1"
SPEECH_SCRIPT = SPEECH_DIR / "speech_module.py"
SPEECH_WEIGHTS = SPEECH_DIR / "speech_cnn.pt"

HW_DIR = MODELS_ROOT / "handwriting-test-1"
HW_SCRIPT = HW_DIR / "score_handwriting.py"
HW_WEIGHTS = HW_DIR / "runs" / "detect" / "train" / "weights" / "best.pt"


def _parse_last_dict(stdout: str) -> dict:
    """
    The scripts print Python dicts (not strict JSON). Extract the last {...} and literal-eval it.
    """
    matches = re.findall(r"\{.*\}", stdout, flags=re.DOTALL)
    if not matches:
        raise RuntimeError(f"Could not parse model output. Raw stdout:\n{stdout}")
    try:
        return ast.literal_eval(matches[-1])
    except Exception as e:
        raise RuntimeError(f"Failed to parse model output dict: {e}\nRaw:\n{matches[-1]}")


def predict_speech_script(wav_path: Path) -> float:
    """
    Runs: python speech_module.py --mode infer ... --out speech_cnn.pt --infer_wav <wav>
    Expects WAV input. Returns speech_risk in [0,1].
    """
    if not SPEECH_SCRIPT.exists():
        raise FileNotFoundError(f"Missing speech script: {SPEECH_SCRIPT}")
    if not SPEECH_WEIGHTS.exists():
        raise FileNotFoundError(f"Missing speech weights: {SPEECH_WEIGHTS}")

    cmd = [
        sys.executable,
        str(SPEECH_SCRIPT),
        "--mode",
        "infer",
        "--root",
        ".",
        "--audio_root",
        ".",
        "--out",
        str(SPEECH_WEIGHTS.name),
        "--infer_wav",
        str(wav_path),
    ]
    res = subprocess.run(cmd, cwd=str(SPEECH_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Speech inference failed:\n{res.stderr}\n{res.stdout}")
    out = _parse_last_dict(res.stdout)
    risk = out.get("speech_risk", None)
    if risk is None:
        raise RuntimeError(f"Speech output missing speech_risk. Raw: {out}")
    return float(risk)


def predict_handwriting_script(image_path: Path) -> float:
    """
    Runs: python score_handwriting.py --model ...best.pt --source <image>
    Returns risk in [0,1] based on detections (Reversal + Corrected)/total.
    """
    if not HW_SCRIPT.exists():
        raise FileNotFoundError(f"Missing handwriting script: {HW_SCRIPT}")
    if not HW_WEIGHTS.exists():
        raise FileNotFoundError(f"Missing handwriting weights: {HW_WEIGHTS}")

    cmd = [
        sys.executable,
        str(HW_SCRIPT),
        "--model",
        str(HW_WEIGHTS),
        "--source",
        str(image_path),
        "--conf",
        "0.05",
        "--imgsz",
        "1280",
    ]
    res = subprocess.run(cmd, cwd=str(HW_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Handwriting inference failed:\n{res.stderr}\n{res.stdout}")
    out = _parse_last_dict(res.stdout)
    risk = out.get("risk", None)
    if risk is None:
        raise RuntimeError(f"Handwriting output missing risk. Raw: {out}")
    return float(risk)


def predict_cognitive_stub(metrics: CognitiveInput) -> float:
    """Placeholder: return a dummy risk score from reaction metrics."""
    # TODO: use metrics.reactionTimes / metrics.averageMs with your model
    return 0.28


def predict_final_stub(scores: FinalInput) -> tuple[float, list[str]]:
    """Placeholder: combine scores into final risk and explanations."""
    # TODO: use your fusion model or rule-based logic
    s = [scores.handwriting, scores.speech, scores.eye, scores.cognitive]
    valid = [x for x in s if x is not None]
    final = sum(valid) / len(valid) if valid else 0.0
    explanations = [
        "Handwriting score considered." if scores.handwriting is not None else "Handwriting not available.",
        "Speech score considered." if scores.speech is not None else "Speech not available.",
        "Eye tracking not yet available.",
        "Cognitive (reaction time) score considered." if scores.cognitive is not None else "Cognitive not available.",
    ]
    return final, explanations


# --- Endpoints (match frontend api.js) ---

@app.post("/predict/handwriting")
async def predict_handwriting(file: UploadFile = File(...)):
    """Accept image file, return risk_score."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Expected an image file")
    try:
        suffix = Path(file.filename or "upload").suffix or ".jpg"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / f"handwriting{suffix}"
            p.write_bytes(await file.read())
            risk_score = predict_handwriting_script(p)
        return {"risk_score": risk_score}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/predict/speech")
async def predict_speech(file: UploadFile = File(...)):
    """Accept audio file, return risk_score."""
    # Accept common audio types
    allowed = ("audio/", "application/octet-stream")
    if not file.content_type or not any(file.content_type.startswith(t) for t in allowed):
        # Still try to process; frontend may send webm
        pass
    try:
        # Your friend's inference expects a WAV file path.
        suffix = Path(file.filename or "upload").suffix or ".webm"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / f"speech{suffix}"
            p.write_bytes(await file.read())
            if p.suffix.lower() != ".wav":
                raise HTTPException(400, "Speech model expects WAV input. Please upload/record as .wav.")
            risk_score = predict_speech_script(p)
        return {"risk_score": risk_score}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/predict/cognitive")
async def predict_cognitive(data: CognitiveInput):
    """Accept reaction time metrics, return risk_score."""
    try:
        risk_score = predict_cognitive_stub(data)
        return {"risk_score": risk_score}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/predict/final")
async def predict_final(data: FinalInput):
    """Accept all module scores, return final_risk and explanations."""
    try:
        final_risk, explanations = predict_final_stub(data)
        return {"final_risk": round(final_risk, 4), "explanations": explanations}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/")
async def root():
    """Health check."""
    return {"status": "ok", "message": "AI Learning Screening API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
