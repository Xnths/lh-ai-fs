# BS Detector

A multi-agent AI pipeline that verifies legal briefs against supporting documents — catching fabricated quotes, unsupported citations, and factual contradictions.

---

## Setup

### Requirements

- Python 3.11+
- [Ollama](https://ollama.com) with `llama3.2` pulled locally
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8002
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5175`.  
API runs at `http://localhost:8002`.

### Docker (alternative)

```bash
cp .env.example .env
docker compose up --build
```

---

## Configuration

Edit `backend/.env`:

```env
LLM_PROVIDER=ollama          # or: openai
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=              # required only if LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o
```

The pipeline is LLM-agnostic. Switching providers requires only a `.env` change — no code changes.

---

## Architecture

### Strategy Pattern — LLM Provider

```
LLMProvider (ABC)
├── OllamaProvider   ← default
└── OpenAIProvider   ← requires OPENAI_API_KEY
```

`get_provider()` reads `LLM_PROVIDER` at runtime and returns the correct implementation.

### Agent Pipeline

```
POST /analyze
    │
    ├── CitationExtractor     LLM + few-shot prompting
    │     Extracts citations and attributed quotes from MSJ
    │
    ├── CitationVerifier      LLM (one call per citation)
    │     Verifies each citation supports its stated proposition
    │
    ├── QuoteChecker          LLM
    │     Verifies accuracy of quoted text attributed to cited sources
    │
    ├── DateCrossChecker      Deterministic regex
    │     Extracts dates from all documents, flags mismatches
    │
    ├── FactCrossChecker      LLM (one claim × one document per call)
    │     Verifies explicit factual claims against supporting documents
    │
    └── JudicialMemo          LLM
          Synthesizes top findings into one paragraph for a judge
```

Agents pass structured JSON between steps — never raw text.

### Documents

Located in `backend/documents/`:

```
motion_for_summary_judgment.txt   ← primary document (MSJ)
police_report.txt
medical_records_excerpt.txt
witness_statement.txt
```

### API

```
POST /analyze
```

No request body required. Loads documents from `backend/documents/` automatically.

Response:

```json
{
  "report": {
    "citation_verification": [...],
    "quote_accuracy": [...],
    "factual_consistency": [...],
    "judicial_memo": "..."
  }
}
```

---

## Running Evals

```bash
cd backend
python run_evals.py
```

### Ground Truth

The eval harness measures against 4 known findings in _Rivera v. Harmon Construction Group_:

| ID  | Finding                                                                                                                                          | Category |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| f1  | MSJ states incident on March 14, 2021; all supporting documents state March 12, 2021                                                             | factual  |
| f2  | MSJ claims Rivera was not wearing PPE; police report and witness confirm he was                                                                  | factual  |
| f3  | Quote attributed to _Privette v. Superior Court_ is fabricated — "never liable" does not appear in the case                                      | quote    |
| f4  | MSJ claims Harmon did not direct operations; police report and witness statement confirm Donner directed the crew and dismissed a safety warning | factual  |

### Metrics

$$\text{Precision} = \frac{|F \cap F^*|}{|F|}$$

$$\text{Recall} = \frac{|F \cap F^*|}{|F^*|}$$

$$\text{Hallucination Rate} = \frac{|F \setminus F^*|}{|F|}$$

where $F$ is the set of flags returned by the pipeline and $F^*$ is the ground truth set.

### Current Results (`llama3.2`)

| Metric             | Value |
| ------------------ | ----- |
| Recall             | 0.75  |
| Precision          | ~0.75 |
| Hallucination Rate | ~0.25 |

f2 (PPE) is not detected by `llama3.2`. The date mismatch (f1) is detected deterministically via regex, independent of model capability.

### Model Upgrade Criterion

Run evals on candidate model $M_{\theta'}$. Accept upgrade only if:

$$\Delta\text{Recall} = \text{Recall}_{\theta'} - \text{Recall}_{\theta} > 0$$

with $p < 0.05$ under bootstrap resampling ($B = 1000$).

---

## Design Decisions

See [`reflection.md`](./reflection.md).
