# BS Detector — AI pipeline that verifies legal briefs for fabricated quotes, unsupported citations, and factual contradictions.

---

## Setup (Docker)

```bash
cp .env.example .env
# Edit .env if needed (default uses Ollama with llama3.2)
docker compose up --build
```

- Frontend: http://localhost:5175
- API: http://localhost:8002

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| LLM_PROVIDER | ollama | `ollama` or `openai` |
| OLLAMA_MODEL | llama3.2 | Model name for Ollama |
| OLLAMA_BASE_URL | http://host.docker.internal:11434 | Ollama host (use host.docker.internal in Docker on Linux) |
| OPENAI_API_KEY | (empty) | Required only if LLM_PROVIDER=openai |
| OPENAI_MODEL | gpt-4o | Model name for OpenAI |

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
    ├── DateCrossChecker      Deterministic (no LLM call)
    │     Extracts dates via regex, flags mismatches across documents
    │
    ├── FactCrossChecker      LLM (one claim × one document per call)
    │     Verifies explicit factual claims against supporting documents
    │
    └── JudicialMemo          LLM
          Synthesizes top findings into one paragraph for a judge
```

Agents pass structured JSON between steps — never raw text blobs.

---

## Running Evals

```bash
docker compose exec backend python run_evals.py
```

### Ground Truth

| ID | Finding | Category |
|---|---|---|
| f1 | MSJ states incident on March 14, 2021; all supporting documents state March 12, 2021 | factual_consistency |
| f2 | MSJ claims Rivera was not wearing PPE; police report and witness confirm he was | factual_consistency |
| f3 | Quote attributed to _Privette v. Superior Court_ is fabricated — "never liable" does not appear in the case | quote_accuracy |
| f4 | MSJ claims Harmon did not direct operations; police report and witness statement confirm Donner directed the crew and dismissed a safety warning | factual_consistency |

### Metrics

$$\text{Precision} = \frac{|\text{TP}|}{|\text{TP}| + |\text{FP}|}$$

$$\text{Recall} = \frac{|\text{TP}|}{|F^*|}$$

$$\text{Hallucination Rate} = \frac{|\text{FP}|}{|\text{TP}| + |\text{FP}|}$$

where $F^*$ is the ground truth set.

### Current Results (`llama3.2`)

| Metric | Value |
|---|---|
| Recall | 0.75 |
| Precision | ~0.75 |
| Hallucination Rate | ~0.25 |

### Model Upgrade Criterion

Accept upgrade only if $\Delta\text{Recall} > 0$ with $p < 0.05$ under bootstrap resampling ($B = 1000$).

---

## API

```
POST /analyze
```

No request body. Returns:

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

## Design Decisions

See [reflection.md](./reflection.md) for full tradeoff analysis.
