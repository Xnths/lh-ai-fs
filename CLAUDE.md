# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BS Detector** — a take-home challenge to build a multi-agent AI pipeline that verifies legal briefs for citation accuracy, quote fidelity, and cross-document consistency. The case file is *Rivera v. Harmon Construction Group*, a personal injury lawsuit.

The deliverable is a `POST /analyze` endpoint that returns a structured JSON verification report.

## Running the Project

### Docker (recommended)

```bash
cp .env.example .env   # add OPENAI_API_KEY
docker compose up --build
```

- Backend: `http://localhost:8002`
- Frontend: `http://localhost:5175`

Both services hot-reload from host file edits.

### Manual

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
uvicorn main:app --reload --port 8002

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Architecture

```
backend/
  main.py        — FastAPI app; POST /analyze is the only endpoint (currently a stub)
  llm.py         — thin OpenAI wrapper: call_llm(messages, model, temperature) → str
  documents/     — 4 source documents: MSJ, police report, medical records, witness statement

frontend/
  src/App.jsx    — single-page React UI; calls POST /analyze and renders the JSON report
```

### Key design constraints

- The pipeline must pass **structured data between agents**, not raw text blobs.
- Output must be **JSON**, not prose.
- The LLM helper (`llm.py`) defaults to `gpt-4o` at `temperature=0`; import and extend it for agent calls.
- No test framework is pre-installed — the eval suite (`run_evals.py`) should be added and runnable via `python run_evals.py`.

### Documents

All four `.txt` files in `backend/documents/` are loaded at request time via `load_documents()` in `main.py`. The Motion for Summary Judgment (`motion_for_summary_judgment.txt`) is the primary target; the other three are ground-truth references for cross-document consistency checks.

## Implementation Spec Summary

**Tier 1 (core):** Extract citations from the MSJ → assess whether each cited authority supports the stated proposition → flag quote accuracy → return structured JSON.

**Tier 2:** Eval harness (`python run_evals.py`) measuring precision, recall, and hallucination rate; cross-document fact consistency; uncertainty expressed as "could not verify".

**Tier 3:** ≥4 distinct agents with non-overlapping roles, confidence scoring, judicial memo agent, graceful failure handling, UI that renders structured output beyond raw JSON.
