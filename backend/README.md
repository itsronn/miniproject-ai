# AI Learning Screening Backend

Python API for the learning screening frontend. Provides stub endpoints so the app works end-to-end; replace stubs with your real models when ready.

## Setup

```bash
cd ai-learning-screening-backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or: `python main.py`

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

## Endpoints (used by frontend)

| Method | Path | Input | Response |
|--------|------|--------|----------|
| POST | `/predict/handwriting` | FormData: `file` (image) | `{ "risk_score": number }` |
| POST | `/predict/speech` | FormData: `file` (audio) | `{ "risk_score": number }` |
| POST | `/predict/cognitive` | JSON: `{ "reactionTimes", "averageMs" }` | `{ "risk_score": number }` |
| POST | `/predict/final` | JSON: `{ "handwriting", "speech", "eye", "cognitive" }` | `{ "final_risk", "explanations" }` |

## Adding real models

1. Put model files in the `models/` folder.
2. In `main.py`, replace the `predict_*_stub` functions:
   - Load your model (e.g. at startup or on first request).
   - Run inference on the uploaded file or JSON input.
   - Return `risk_score` (and for final: `final_risk`, `explanations`).

Frontend runs at http://localhost:5173; CORS is enabled for that origin.
