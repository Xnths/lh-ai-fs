import json
import sys
from pathlib import Path

from agents import run_pipeline
from llm import get_provider

GROUND_TRUTH = [
    {
        "id": "f1",
        "description": (
            "MSJ states incident on March 14, 2021; "
            "documents state March 12, 2021"
        ),
        "category": "factual_consistency",
        "matcher": lambda report: any(
            "march 14" in f.get("fact_in_msj", "").lower()
            for f in report.get("factual_consistency", [])
        ),
    },
    {
        "id": "f2",
        "description": (
            "MSJ claims Rivera was not wearing PPE; "
            "police report and witness confirm he was"
        ),
        "category": "factual_consistency",
        "matcher": lambda report: any(
            "personal protective equipment" in f.get("fact_in_msj", "").lower()
            and f.get("contradicting_document")
            in ("police_report", "witness_statement")
            for f in report.get("factual_consistency", [])
        ),
    },
    {
        "id": "f3",
        "description": (
            "Quote attributed to Privette is fabricated — "
            "'never liable' does not appear in the case"
        ),
        "category": "quote_accuracy",
        "matcher": lambda report: any(
            "privette" in q.get("citation", "").lower()
            and q.get("verdict") == "inaccurate"
            for q in report.get("quote_accuracy", [])
        ),
    },
    {
        "id": "f4",
        "description": (
            "MSJ claims Harmon did not control operations; "
            "Donner directed crew and dismissed safety concern"
        ),
        "category": "factual_consistency",
        "matcher": lambda report: any(
            "direct" in f.get("fact_in_msj", "").lower()
            or "control" in f.get("fact_in_msj", "").lower()
            or "safety concern" in f.get("fact_in_msj", "").lower()
            for f in report.get("factual_consistency", [])
        ),
    },
]


def evaluate(report: dict) -> dict:
    detected = []
    missed = []
    for flag in GROUND_TRUTH:
        if flag["matcher"](report):
            detected.append(flag["id"])
        else:
            missed.append(flag["id"])

    all_flags = (
        report.get("factual_consistency", [])
        + report.get("quote_accuracy", [])
        + [
            c
            for c in report.get("citation_verification", [])
            if c.get("verdict") == "not_supported"
        ]
    )

    true_positive = len(detected)
    false_negative = len(missed)
    total_returned = len(all_flags)
    false_positive = max(0, total_returned - true_positive)

    precision = true_positive / total_returned if total_returned > 0 else 0.0
    recall = true_positive / len(GROUND_TRUTH)
    hallucination_rate = (
        false_positive / total_returned if total_returned > 0 else 0.0
    )

    return {
        "true_positives": true_positive,
        "false_negatives": false_negative,
        "false_positives": false_positive,
        "total_flags_returned": total_returned,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "detected": detected,
        "missed": missed,
    }


def main():
    docs = {}
    documents_dir = Path(__file__).parent / "documents"
    for f in documents_dir.glob("*.txt"):
        docs[f.stem] = f.read_text()

    print("Running pipeline...", flush=True)
    llm = get_provider()
    report = run_pipeline(docs, llm)

    print("Evaluating...", flush=True)
    results = evaluate(report)

    print(json.dumps(results, indent=2))

    print(f"\nPrecision:         {results['precision']:.2%}")
    print(f"Recall:            {results['recall']:.2%}")
    print(f"Hallucination:     {results['hallucination_rate']:.2%}")
    print(f"Detected:          {results['detected']}")
    print(f"Missed:            {results['missed']}")

    if results["recall"] < 0.5:
        print("\nWARNING: Recall below 0.50. Consider upgrading model.")
        sys.exit(1)


if __name__ == "__main__":
    main()
