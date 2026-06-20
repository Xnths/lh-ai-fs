from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import run_pipeline
from llm import get_provider

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCUMENTS_DIR = Path(__file__).parent / "documents"


def load_documents() -> dict[str, str]:
    documents = {}
    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        documents[file_path.stem] = file_path.read_text()
    return documents


@app.post("/analyze")
async def analyze():
    try:
        documents = load_documents()
        llm = get_provider()
        report = run_pipeline(documents, llm)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
