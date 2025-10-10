from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from readmegen.assessor.assessor import assess_files

# ---- import your package modules (adjust if you renamed files) ----
from readmegen.collector.collector import collect
from readmegen.generator.readme_generator import generate_readme_from

# If your generator lives at readmegen/readme_generator.py, use that import instead:


load_dotenv()

app = Flask(__name__)
CORS(app)  # allow requests from your React dev server

OUTFILE_NAME = "README.generated.md"


def build_selected(docs: List[Dict[str, Any]], relevance: int, logs: List[str]):
    assessments = assess_files(docs)
    selected: List[Dict[str, Any]] = []
    for a, src in zip(assessments, docs):
        try:
            ok = (
                bool(getattr(a, "include", False))
                and int(getattr(a, "score", 0)) >= relevance
            )
            if ok:
                row = a.model_dump() if hasattr(a, "model_dump") else dict(a)
                row.pop("summary", None)
                row["content"] = src["content"]
                row["path"] = row.get("path") or src.get("source", "UNKNOWN_PATH")
                selected.append(row)
        except Exception as e:
            logs.append(f"⚠️ Skipped one file due to error: {e}")
            continue
    return selected, assessments


@app.post("/api/generate")
def api_generate():
    """
    JSON body:
    {
      "path": "C:/path/to/project",
      "relevance": 3   # optional (default 3). files with score >= relevance & include=True are used
    }
    """
    data = request.get_json(silent=True) or {}
    raw_path = data.get("path", "")
    relevance = int(data.get("relevance", 3))

    logs: List[str] = []
    if not raw_path:
        return jsonify({"ok": False, "error": "Missing 'path'"}), 400

    project_path = Path(raw_path).expanduser().resolve()
    if not project_path.is_dir():
        return (
            jsonify({"ok": False, "error": f"Path is not a directory: {project_path}"}),
            400,
        )

    logs.append(f"📁 Project: {project_path}")

    # 1) Collect
    collected = collect(root=str(project_path), include_readme=False)
    docs = collected.get("docs", [])
    logs.append(f"🗂️  Collected {len(docs)} files")
    if not docs:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "No documents collected (check ignore rules / path).",
                    "logs": logs,
                }
            ),
            400,
        )

    # 2) Assess
    selected, assessments = build_selected(docs, relevance, logs)
    logs.append(
        f"🧮 Assessed {len(assessments)} files → selected {len(selected)} for README"
    )
    if selected:
        logs.append("📄 Selected files:")
        for d in selected:
            logs.append(f"   • {d['path']}")
    else:
        logs.append(
            f"⚠️  No files selected with score>={relevance} & include=True; using all files instead."
        )
        selected = [{"path": d["source"], "content": d["content"]} for d in docs]

    # 3) Generate README text
    readme_md = generate_readme_from(selected)

    # 4) Write output
    out_path = project_path / OUTFILE_NAME
    out_path.write_text(readme_md, encoding="utf-8", newline="\n")
    logs.append(f"✅ README written: {out_path}")

    return jsonify(
        {
            "ok": True,
            "out_path": str(out_path),
            "logs": logs,
            "readme": readme_md,
            "selected_paths": [d["path"] for d in selected],
            "count_collected": len(docs),
            "count_selected": len(selected),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
