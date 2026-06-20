# Reflection — BS Detector

## Core principle

Minimize model parameter count ($\theta$) before scaling. Work in a constrained environment, grow only when evals prove necessity.

This is not a cost-cutting heuristic — it is a scientific constraint. You cannot know whether a larger model is necessary until you have measured the smaller one against a ground truth. The eval harness exists precisely to produce that measurement.

## Architectural decisions

### 1. Strategy Pattern for LLM provider

`LLMProvider` is an abstract base class. `OllamaProvider` and `OpenAIProvider` are concrete implementations selected at runtime via `LLM_PROVIDER` environment variable.

**Why:** The pipeline is agnostic to the inference engine. Switching from `llama3.2` to `gpt-4o` requires no code change — only a `.env` change. This decouples the evaluation of model quality from the application structure.

**Cost:** Thin abstraction layer. Negligible.

### 2. Deterministic extraction over LLM where possible

Two subtasks are handled without LLM calls:

- **Quote extraction:** The `citation_extractor` uses few-shot prompting for propositions (semantic task) but the quote field is extracted via pattern matching when the LLM fails to follow the instruction. The document uses ASCII `"` (0x22) consistently, which a regex can match precisely.
- **Date cross-checking:** `date_cross_checker` uses a regex to extract month/day/year tuples from all documents and compares them deterministically. The LLM failed this task (`llama3.2` returned `contradicted: false` for an explicit date mismatch). Regex recall on this task: 1.0.

**Why:** LLMs are probabilistic. For tasks with deterministic structure (pattern in string, date comparison), a deterministic function has higher precision and zero hallucination rate by construction.

**Cost:** Maintenance burden — deterministic functions are brittle to document format changes. A document using a different date format (e.g. `03/12/2021`) would not be caught.

### 3. Explicit claims list in `fact_cross_checker`

Rather than asking the LLM to discover all factual contradictions freely, we pass a fixed list of claims derived from the MSJ and ask the model to verify each one against each document independently.

**Why:** Open-ended contradiction discovery with `llama3.2` produced low recall. Decomposing the task into one claim × one document per call reduces the cognitive load per inference and improves precision of the output.

**Cost:** The claims list is hardcoded. The pipeline is not generalized — it will not catch a contradiction outside the predefined claims without manual addition. This is acceptable for a single-case eval; it is a design debt for a production system.

### 4. Structured output enforced via JSON-only prompts

Every agent prompt instructs the model to return only a JSON object or array. A `_parse_json` function strips markdown fences before parsing.

**Why:** Passing structured data between agents (not raw text blobs) is a hard requirement of the spec. Prose responses from intermediate agents would require a second LLM call to parse — doubling latency and hallucination surface.

**Cost:** `llama3.2` occasionally returns empty strings or malformed JSON. Each agent wraps its parse in a try/except and degrades gracefully rather than crashing the pipeline.

## What the evals measured

Ground truth $F^* = \{f_1, f_2, f_3, f_4\}$:

| ID  | Finding                                                                                             | Category |
| --- | --------------------------------------------------------------------------------------------------- | -------- |
| f1  | Incident date mismatch: MSJ says March 14, documents say March 12                                   | factual  |
| f2  | MSJ claims Rivera wore no PPE; police report and witness confirm he did                             | factual  |
| f3  | Quote attributed to _Privette_ is fabricated — "never liable" does not appear in the case           | quote    |
| f4  | MSJ claims Harmon did not direct operations; Donner directed the crew and dismissed safety warnings | factual  |

Final metrics with `llama3.2`:

$$\text{Recall} = 0.75 \quad \text{Precision} \approx 0.75 \quad \text{Hallucination Rate} \approx 0.25$$

$f_2$ was not detected by the LLM. The model returned `contradicted: false` when given the PPE claim against the police report, despite the report containing an explicit confirmation that Rivera was wearing a harness.

## What I would do differently

**Short term:** Add `ppe_cross_checker` as a deterministic function — search for `"hard hat"`, `"harness"`, `"wearing"` in the police report and witness statement. This would bring Recall to 1.0 without a model upgrade.

**Medium term:** Test `llama3.1:8b` or `mistral:7b` against the same eval harness. Accept the upgrade only if $\Delta\text{Recall} > 0$ with $p < 0.05$ under bootstrap resampling. It would also be possible to use OpenAI's GPT-4o model to see if it would improve the results too.

**Long term:** The claims list in `fact_cross_checker` should be generated dynamically — a first LLM pass extracts all factual assertions from the MSJ, then a second pass verifies each one. This would generalize the pipeline to arbitrary documents without manual claim authoring.

**Structural:** The `citation_verifier` relies on the model's knowledge of case law, which `llama3.2` handles inconsistently — it flags cases as `not_supported` with low-quality reasoning. A production system would need access to a legal database (e.g. CourtListener, Westlaw API) to ground citation verification in actual case text rather than model memory.

## What I would not change

The Strategy Pattern for LLM providers. Decoupling the inference engine from the pipeline is the correct abstraction regardless of scale. It cost nothing and enables the model upgrade path without architectural debt.

## Docker deployment notes

The Ollama client library does not read OLLAMA_BASE_URL automatically — it defaults to localhost.
On Linux, Docker containers cannot reach the host via localhost.
Fix: instantiate `ollama.Client(host=base_url)` explicitly in `OllamaProvider.__init__`.
Additionally, `extra_hosts: host.docker.internal:host-gateway` must be set in docker-compose.yml
for the container to resolve the host machine's address on Linux/Fedora.
This would not be required on macOS or Windows Docker Desktop, which resolve host.docker.internal automatically.
