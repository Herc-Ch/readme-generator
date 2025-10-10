import os
from pathlib import Path

from readmegen.collector.import_filenames import *

MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 5 * 1024 * 1024
LOCK_MAX_LINES = 200
CONFIG_MAX_LINES = 800


def should_include(path: Path) -> bool:
    return (
        path.suffix in INCLUDE_EXTS
        or path.name in KEY_FILENAMES
        or path.name.startswith(".env")
    )


def sanitize_env(text: str) -> str:
    out = []
    for line in text.splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k = line.split("=", 1)[0].strip()
            out.append(f"{k}=<YOUR_VALUE>" if k else line)
        else:
            out.append(line)
    return "\n".join(out)


def is_lock_like(p: Path) -> bool:
    return p.name in LOCK_BASENAMES or p.suffix == ".lock"


def read_bytes_as_text(path: Path, max_bytes: int) -> str:
    try:
        with open(path, "rb") as f:
            return f.read(max_bytes).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def head_lines(text: str, n: int) -> str:
    lines = text.splitlines()
    return text if len(lines) <= n else "\n".join(lines[:n]) + "\n\n# ...truncated...\n"


def read_with_rules(p: Path) -> str:
    raw = read_bytes_as_text(p, MAX_FILE_BYTES)
    if p.name.startswith(".env"):
        raw = sanitize_env(raw)
    if is_lock_like(p):
        return head_lines(raw, LOCK_MAX_LINES)
    if p.suffix in {".json", ".yaml", ".yml"}:
        return head_lines(raw, CONFIG_MAX_LINES)
    return raw


def collect(root: str = ".", include_readme: bool = False):
    rootp = Path(root).resolve()
    docs, seen, total = [], set(), 0

    for dirpath, dirnames, filenames in os.walk(rootp):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        dp = Path(dirpath)

        for fn in sorted(filenames):  # deterministic order
            p = dp / fn
            if not p.is_file():
                continue
            rel = str(p.relative_to(rootp)).replace("\\", "/")

            name = Path(rel).name.lower()
            if not include_readme:
                if name in {"readme", "readme.md", "readme.rst", "readme.txt"}:
                    continue

            if not should_include(p) or rel in seen:
                continue

            text = read_with_rules(p)
            docs.append({"source": rel, "content": text})
            seen.add(rel)
            total += len(text)
            if total >= MAX_TOTAL_BYTES:
                return {"docs": docs}
    return {"docs": docs}


# --- only run when executed directly ---
if __name__ == "__main__":
    # if inside readme_generator/, default to parent repo
    project_root = Path(__file__).resolve().parents[1]
    data = collect(root=str(project_root), include_readme=False)
    print(data["docs"][0]["content"][:300])
    print(
        f"\nLoaded {len(data['docs'])} docs "
        "(lock files truncated, env values sanitized)."
    )
    for d in data["docs"]:
        print(" -", d["source"])
