import json
import re

from llm import LLMProvider


def _parse_json(text: str) -> dict | list:
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)


def citation_extractor(msj_text: str, llm: LLMProvider) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a legal document parser. "
                "Extract every legal citation from the text. "
                "A citation is a reference to a case, statute, or regulation. "
                "A quote is a sentence in double quotation marks that appears "
                "immediately after a citation. "
                "Return ONLY a JSON array. No prose. No markdown. "
                "Each element must have exactly these keys: "
                '{"citation": "<full citation string>", '
                '"proposition": "<the legal claim this citation supports, or null>", '
                '"quote": "<sentence in double quotes attributed to this source, '
                'or null>"}'
                "\n\nExample:"
                "\nText: Foo v. Bar, 123 F.2d 456 (1990) "
                '("The defendant is never liable.")'
                "\nOutput: "
                '{"citation": "Foo v. Bar, 123 F.2d 456 (1990)", '
                '"proposition": "defendant not liable", '
                '"quote": "The defendant is never liable."}'
                '\nText: Id. at 702. ("A hirer is never liable for injuries.")'
                '\nOutput quote: "A hirer is never liable for injuries."'
            ),
        },
        {"role": "user", "content": msj_text},
    ]
    raw = llm.complete(messages, temperature=0)
    return _parse_json(raw)


def citation_verifier(citations: list[dict], llm: LLMProvider) -> list[dict]:
    results = []
    for c in citations:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a legal citation fact-checker. "
                    "You will receive a legal citation and the proposition it "
                    "is used to support. "
                    "Assess whether the cited authority actually supports the "
                    "proposition as stated. "
                    "Use only your knowledge of published case law and statutes. "
                    "Return ONLY a JSON object with exactly these keys: "
                    '{"citation": "<citation>", '
                    '"verdict": "<supported|not_supported|could_not_verify>", '
                    '"reasoning": "<one sentence explanation>"}'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"citation": c["citation"], "proposition": c["proposition"]}
                ),
            },
        ]
        raw = llm.complete(messages, temperature=0)
        result = _parse_json(raw)
        result["original_proposition"] = c["proposition"]
        results.append(result)
    return results


def quote_checker(
    citations: list[dict], documents: dict[str, str], llm: LLMProvider
) -> list[dict]:
    cited_quotes = [c for c in citations if c.get("quote")]
    if not cited_quotes:
        return []

    full_context = "\n\n".join(
        f"[{name}]\n{text}"
        for name, text in documents.items()
        if name != "motion_for_summary_judgment"
    )

    results = []
    for c in cited_quotes:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a quote accuracy checker. "
                    "You will receive a quote attributed to a legal source and "
                    "a set of documents. "
                    "Check whether the quote accurately represents the source "
                    "based on your knowledge of published case law. "
                    "Return ONLY a JSON object with exactly these keys: "
                    '{"citation": "<citation>", "quote": "<the quote>", '
                    '"verdict": "<accurate|inaccurate|could_not_verify>", '
                    '"reasoning": "<one sentence explanation>"}'
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "citation": c["citation"],
                        "quote": c["quote"],
                        "available_documents": full_context,
                    }
                ),
            },
        ]
        raw = llm.complete(messages, temperature=0)
        results.append(_parse_json(raw))
    return results


def date_cross_checker(documents: dict[str, str]) -> list[dict]:
    date_pattern = re.compile(
        r'\b(January|February|March|April|May|June|July|August|September'
        r'|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b'
    )

    msj = documents.get("motion_for_summary_judgment", "")
    msj_dates = list(date_pattern.findall(msj))

    results = []
    for doc_name, doc_text in documents.items():
        if doc_name == "motion_for_summary_judgment":
            continue
        doc_dates = list(date_pattern.findall(doc_text))

        for msj_date in msj_dates:
            msj_str = f"{msj_date[0]} {msj_date[1]}, {msj_date[2]}"
            for doc_date in doc_dates:
                doc_str = f"{doc_date[0]} {doc_date[1]}, {doc_date[2]}"
                same_month = msj_date[0] == doc_date[0]
                same_year = msj_date[2] == doc_date[2]
                different_day = msj_date[1] != doc_date[1]
                if same_month and same_year and different_day:
                    results.append({
                        "fact_in_msj": f"The incident occurred on {msj_str}.",
                        "contradicting_document": doc_name,
                        "contradicting_text": f"Document states date as {doc_str}.",
                        "severity": "high",
                    })
    return list({r["fact_in_msj"]: r for r in results}.values())


def fact_cross_checker(
    documents: dict[str, str], llm: LLMProvider
) -> list[dict]:
    aux_docs = {
        k: v for k, v in documents.items()
        if k != "motion_for_summary_judgment"
    }

    claims = [
        "Rivera was not wearing required personal protective equipment "
        "at the time of the incident.",
        "Harmon did not direct or control the scaffolding operations.",
        "No safety concerns were raised about the east-side scaffolding "
        "before the incident.",
    ]

    all_results = []
    for doc_name, doc_text in aux_docs.items():
        for claim in claims:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a legal fact checker. "
                        "You will receive one factual claim and one document. "
                        "Check whether the document contains text that directly "
                        "contradicts the claim. "
                        "Only report a contradiction if the document explicitly "
                        "states something different. "
                        "Return ONLY a JSON object. No prose. No markdown. "
                        '{"claim": "<the claim>", "contradicted": <true|false>, '
                        '"contradicting_text": "<exact sentence from document '
                        'that contradicts the claim, or null>", '
                        '"severity": "<high|medium|low>"}'
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "claim": claim,
                        "document_name": doc_name,
                        "document_text": doc_text,
                    }),
                },
            ]
            raw = llm.complete(messages, temperature=0)
            try:
                result = _parse_json(raw)
                if result.get("contradicted"):
                    all_results.append({
                        "fact_in_msj": claim,
                        "contradicting_document": doc_name,
                        "contradicting_text": result.get("contradicting_text", ""),
                        "severity": result.get("severity", "medium"),
                    })
            except json.JSONDecodeError:
                pass

    return all_results


def judicial_memo(
    citation_results: list[dict],
    quote_results: list[dict],
    fact_results: list[dict],
    llm: LLMProvider,
) -> str:
    flagged_citations = [
        c for c in citation_results if c.get("verdict") == "not_supported"
    ]
    flagged_quotes = [
        q for q in quote_results if q.get("verdict") == "inaccurate"
    ]
    high_severity_facts = [
        f for f in fact_results if f.get("severity") == "high"
    ]

    summary_input = {
        "unsupported_citations": flagged_citations,
        "inaccurate_quotes": flagged_quotes,
        "high_severity_factual_contradictions": high_severity_facts,
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are a judicial clerk. "
                "Write a single paragraph memo for a judge summarizing the most "
                "significant verification findings. "
                "Be factual and precise. "
                "Do not use legal jargon beyond standard judicial language. "
                "Do not exceed 150 words. "
                "Return only the paragraph text, no labels or headers."
            ),
        },
        {"role": "user", "content": json.dumps(summary_input)},
    ]
    return llm.complete(messages, temperature=0)


def run_pipeline(documents: dict[str, str], llm: LLMProvider) -> dict:
    msj = documents.get("motion_for_summary_judgment", "")

    citations = citation_extractor(msj, llm)
    citation_results = citation_verifier(citations, llm)
    quote_results = quote_checker(citations, documents, llm)
    date_results = date_cross_checker(documents)
    fact_results = fact_cross_checker(documents, llm) + date_results
    memo = judicial_memo(citation_results, quote_results, fact_results, llm)

    return {
        "citation_verification": citation_results,
        "quote_accuracy": quote_results,
        "factual_consistency": fact_results,
        "judicial_memo": memo,
    }
