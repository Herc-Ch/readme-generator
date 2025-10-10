# readme_generator.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI

load_dotenv()

# -----------------------------------------------------------------------------
# README generation (pure function) — used by backend/app.py
# -----------------------------------------------------------------------------

README_TEMPLATE = """You are an expert software documentation writer.

You are given the following project context:

{context}

---

Your task:

{question}

Guidelines:
- Title: Use the project/folder name or package.json "name".
- Description: Summarize purpose (from context or inferred).
- Features: Bullet-point list of main capabilities.
- Installation: Include backend (pip/Poetry) and frontend (npm/yarn/pnpm) steps if relevant.
- Usage: Show commands to run (python main.py, npm run dev, docker-compose up, etc.).
- Environment Variables: List keys only (no secret values).
- Deployment: Mention Docker if Dockerfile/compose is present, else skip.
- Architecture: Include a simple Mermaid diagram if services are present.
- Project Structure: Show a tree up to depth 2–3.
- License: Include if LICENSE is present.
- Keep it clear, professional, and concise.
- Include the usage of emoticons when proper.
- Code blocks: Always wrap commands, code samples, and diagrams in fenced code blocks 
    using triple backticks with the correct language identifier (e.g., ```bash```, ```python```, ```mermaid```).
- Never omit or truncate closing triple backticks.
- All installation and usage commands must appear in **copyable** fenced blocks (not inline).
- When showing folder trees or command-line examples, wrap them in ```bash``` or ```plaintext``` blocks.
- For Mermaid diagrams, always use the syntax ```mermaid\n{diagram}\n```.


Mermaid Diagram Rules (Strict):
1. Always start with `flowchart LR` or `flowchart TD`.
2. Node IDs must be simple alphanumeric tokens (A, B, API, DB).
3. Every node label must be wrapped in double quotes, no exceptions.
   Example: A["Frontend (React + Vite)"], B(("\"SQLite DB\""))
4. Edge labels must be quoted too: A -- "HTTP /api/*" --> B
5. Shapes:
   - Rectangle: A["My Label"]
   - Circle: A(("\"My Label\""))
   - Subgraph: subgraph FE["Frontend: React + Vite"] ... end
6. Never output [Label] without quotes if it contains spaces, punctuation, parentheses, slashes, or plus signs.
7. If in doubt, always quote the label.
8. Never forget to wrap the final Mermaid diagram inside fenced code blocks:
{{code}}
Example:
```mermaid
flowchart LR
  A["Frontend"] --> B["Backend"]


Format the output as a valid Markdown README.md file.
"""

custom_rag_prompt: PromptTemplate = PromptTemplate.from_template(README_TEMPLATE)


def _format_one(d: Dict[str, Any]) -> str:
    """
    Each item should have {'path': ..., 'content': ...}.
    If 'path' missing, try 'source'. If 'content' missing, try 'summary'.
    """
    path = d.get("path") or d.get("source") or "UNKNOWN_PATH"
    content = d.get("content") or d.get("summary") or ""
    return f"---\nSource: {path}\n\nContent:\n{content}\n"


def _format_docs(selected: Iterable[Dict[str, Any]]) -> str:
    return "\n\n".join(_format_one(d) for d in selected)


def generate_readme_from(
    selected: List[Dict[str, Any]],
    *,
    model: str = "gpt-5",
    question: str = "Generate a professional README.md for this project.",
) -> str:
    """
    Build a README.md as Markdown using the LLM, given `selected` docs.
    Returns the README text (string). Does NOT write to disk.
    """
    llm = ChatOpenAI(model=model)

    doc_const = RunnableLambda(lambda _: selected)
    fmt_docs = RunnableLambda(lambda docs: _format_docs(docs))  # type: ignore

    readme_chain: Runnable = (
        {
            "context": doc_const | fmt_docs,
            "question": RunnablePassthrough(),
        }
        | custom_rag_prompt
        | llm
    )

    res = readme_chain.invoke(question)
    return getattr(res, "content", str(res))


# -----------------------------------------------------------------------------
# OPTIONAL: Original REPL agent that writes the README to disk (Mermaid rules kept)
# -----------------------------------------------------------------------------

REPL_SYSTEM_PROMPT = """
You are an autonomous Python coding agent with access to a live Python REPL.

Goal:
- Generate a professional README.md for the current project folder.

General Rules:
- Do not reuse or paraphrase any existing README.md file. Ignore it completely.
- Infer everything from the provided project files and context.
- Do all reasoning and README content generation internally as plain text.
- Do NOT use the Python REPL until the README text is fully complete.
- At the very end, use the Python REPL exactly once to:
  1. Write the README.md file with UTF-8 encoding and Unix newlines.
  2. Print ONLY the absolute path to the file.
- After printing the path, stop. No further REPL calls or messages.

Mermaid Diagram Rules (Strict):
1. Always start with `flowchart LR` or `flowchart TD`.
2. Node IDs must be simple alphanumeric tokens (A, B, API, DB).
3. Every node label must be wrapped in double quotes, no exceptions.
   Example: A["Frontend (React + Vite)"], B(("\"SQLite DB\""))
4. Edge labels must be quoted too: A -- "HTTP /api/*" --> B
5. Shapes:
   - Rectangle: A["My Label"]
   - Circle: A(("\"My Label\""))
   - Subgraph: subgraph FE["Frontend: React + Vite"] ... end
6. Never output [Label] without quotes if it contains spaces, punctuation, parentheses, slashes, or plus signs.
7. If in doubt, always quote the label.

Termination Rule:
- Your final output to the user must be ONLY the absolute path printed by the REPL.

"""


def write_readme_via_repl(readme_text: str, *, model: str = "gpt-5") -> str:
    """
    Optional: uses the Python REPL tool to write README.md to disk and
    prints the absolute path (returned as string).
    """
    repl_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", REPL_SYSTEM_PROMPT),
            ("user", "{readme_text}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    llm = ChatOpenAI(model=model)
    repl_tools = [PythonREPLTool()]

    agent = create_openai_tools_agent(llm, tools=repl_tools, prompt=repl_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=repl_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )

    result = executor.invoke({"input": "Begin!", "readme_text": readme_text})
    # Agent prints the absolute path; LangChain returns a dict with 'output' (varies by version)
    # Return a best-effort string for caller convenience.
    return str(result)
