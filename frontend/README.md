# AI Learning Screening Frontend

A simple multi-step assessment web app for AI-based early learning disability screening. Built with React (Vite), React Router, and Context API.

## Setup

```bash
npm install
npm run dev
```

Backend should run at `http://localhost:8000` with endpoints:

- `POST /predict/handwriting` (FormData: file)
- `POST /predict/speech` (FormData: file)
- `POST /predict/cognitive` (JSON: { reactionTimes, averageMs })
- `POST /predict/final` (JSON: { handwriting, speech, eye, cognitive })

## Flow

Home → User Info → Handwriting → Speech → Eye Tracking (placeholder) → Cognitive → Report

## Tech

- React 18, Vite, React Router DOM
- Context API for global state
- Plain CSS (no UI libraries)
