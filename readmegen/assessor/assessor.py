# assessor.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from readmegen.collector.collector import collect  # no automatic 'data' at import

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Pydantic structured output
# ---------------------------------------------------------------------------

class FileAssessment(BaseModel):
    path: str = Field(..., description="Relative file path within the repo")
    score: int = Field(..., ge=0, le=5, description="0–5 relevance for README")
    include: bool = Field(..., description="True if this file should influence the README")
    reason: str = Field(..., description="1–2 sentence rationale")
    summary: str = Field(..., description="1–3 sentence README-ready summary, no code dumps")


# ---------------------------------------------------------------------------
# 2. System prompt (rubric)
# ---------------------------------------------------------------------------

ASSESS_SYSTEM = """You are an expert technical writer generating an accurate, concise README.
Rate how useful a file is for onboarding (run/build/deploy), configuration (env/API keys), architecture,
key modules, and testing.

Scoring rubric:
5 = Critical entrypoint/config/architecture (main app, routing, app factory, Docker, docker-compose, package.json scripts, pyproject, env schema)
4 = Important integration (DB models, API handlers, routers, main pages, providers; CI that runs build/test)
3 = Helpful config/utilities (lint/format configs, Makefile targets, test config, core utils used across app)
2 = Minor helpers or generic UI atoms (buttons, card styles) — usually summarize only
1–0 = Not helpful for README onboarding

NEVER paste large code. Summaries must explain *purpose and how it affects run/config/deploy*.
"""


# ---------------------------------------------------------------------------
# 3. Helper functions
# ---------------------------------------------------------------------------

def _clip(s: str, limit: int = 4000) -> str:
    """Truncate long file content for prompt safety."""
    return s if len(s) <= limit else s[:limit] + "\n\n# ...truncated...\n"


# ---------------------------------------------------------------------------
# 4. LLM + prompt + chain
# ---------------------------------------------------------------------------

llm = ChatOpenAI(model="gpt-5")  # adjust if needed

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", ASSESS_SYSTEM + "\nReturn a JSON object that matches the schema exactly."),
        (
            "user",
            "Assess this repository file for README relevance.\n"
            "Path: {path}\n"
            "Ext: {ext}\n"
            "Size: {size} bytes\n\n"
            "Sample:\n---\n{sample}\n---",
        ),
    ]
)

chain: Runnable = prompt | llm.with_structured_output(FileAssessment)


# ---------------------------------------------------------------------------
# 5. Main assess_files() function — this is what the backend will call
# ---------------------------------------------------------------------------

def assess_files(files: List[Dict[str, Any]]) -> List[FileAssessment]:
    """
    Takes collected file dictionaries ({source, content}) and returns structured assessments.
    """
    inputs = [
        {
            "path": f["source"],
            "ext": Path(f["source"]).suffix.lower(),
            "size": len(f["content"].encode("utf-8")),
            "sample": _clip(f["content"]),
        }
        for f in files
    ]

    results = chain.batch(inputs, {"max_concurrency": 8})
    return results


# ---------------------------------------------------------------------------
# 6. Optional direct run (for testing only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
    data = collect(root=PROJECT_ROOT, include_readme=False)

    assessments = assess_files(data["docs"])
    selected: List[Dict[str, Any]] = []

    for a, src in zip(assessments, data["docs"]):
        if a.include and a.score > 3:  # type: ignore[attr-defined]
            item = a.model_dump()
            item.pop("summary", None)
            item["content"] = src["content"]
            selected.append(item)
            print(f"-- {a.path}")

    print(f"\nSelected {len(selected)} / {len(assessments)} files.")
    print("End of assessing the sources.")
