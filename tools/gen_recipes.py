#!/usr/bin/env python3
"""Generate the recipe table of src/reference/recipes.html.

Reads the afd-plugin recipe scripts at the pinned commit and writes one table
row for every ``vllm serve`` invocation that carries an ``"afd"`` block (one
AFD process). For each row it records the recipe path, hardware, connector,
model, a topology label, the role, DP/TP, expert parallelism, eager/graph mode,
the DBO thresholds, the attention/FFN rank counts, the AFD connector port and
the HTTP port.

It never imports afd_plugin or vLLM, and it never runs the shell scripts: it
parses the ``.sh`` text with the standard library only, so it is safe to run on
any machine.

Usage:
  python3 tools/gen_recipes.py           # write the page
  python3 tools/gen_recipes.py --check    # exit 1 if the page is out of date
  python3 tools/gen_recipes.py --report   # print the extracted facts
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "explainer.json").read_text(encoding="utf-8"))
REPO = (ROOT / CFG["repo_path"]).resolve()
SHA = CFG["sha"]
PAGE = ROOT / "src" / "reference" / "recipes.html"
BEGIN = "<!-- BEGIN GENERATED recipes -->"
END = "<!-- END GENERATED recipes -->"

RECIPE_DIR = REPO / "recipe"
TOPO_LINK = "concepts/deployment-topologies"


def _clean(token: str) -> str:
    """Normalize a shell token: strip quotes, backslashes and ``${...}``."""
    token = token.strip().strip(",").strip()
    token = token.strip("\\").strip()
    token = token.strip("'\"")
    # '"${AFD_CONNECTOR_PORT}"' and "${VAR:-default}" forms.
    m = re.fullmatch(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}?", token)
    if m:
        var, default = m.group(1), m.group(2)
        return f"${var}" if default is None else f"${var} (def {default})"
    return token


def _find(pattern: str, block: str) -> str | None:
    m = re.search(pattern, block)
    return _clean(m.group(1)) if m else None


def _topology(stem: str, attn: str | None, ffn: str | None) -> str:
    low = stem.lower()
    if "multipod" in low:
        m = re.search(r"multipod_([0-9a-z_]+?)_(?:graph|eager|dbo)", low)
        tag = m.group(1).replace("_", " ") if m else "multipod"
        return f"multipod {tag}".strip()
    m = re.match(r"(\d+)p(\d+)a(\d+)f", low)
    if m:
        return f"{m.group(1)}P{m.group(2)}A{m.group(3)}F"
    m = re.match(r"(\d+)a(\d+)f", low)
    if m:
        return f"{m.group(1)}A{m.group(2)}F"
    if attn and ffn and attn.isdigit() and ffn.isdigit():
        return f"{attn}A{ffn}F"
    return stem


def _iter_serve_blocks(text: str):
    """Yield ``(start_line_1based, block_text)`` for each ``vllm serve`` call."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if "vllm serve" in ln]
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        yield start + 1, "\n".join(lines[start:end])


def extract_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(RECIPE_DIR.rglob("*.sh")):
        rel = path.relative_to(REPO).as_posix()
        parts = path.relative_to(RECIPE_DIR).parts
        hardware = parts[0] if parts else ""
        connector_dir = parts[1] if len(parts) > 1 else ""
        model = parts[2] if len(parts) > 2 else ""
        stem = path.stem
        text = path.read_text(encoding="utf-8")
        blocks = list(_iter_serve_blocks(text))
        for start_line, block in blocks:
            # NPU recipes assemble the "afd" block in a heredoc above the serve
            # call, so fall back to the whole file when the file has one serve.
            search = block
            if '"role"' not in block and '\\"role\\"' not in block and len(blocks) == 1:
                search = text
            # Some recipes embed the JSON in a double-quoted heredoc, so the
            # quotes arrive escaped (\"role\"). Normalize them before matching.
            search = search.replace('\\"', '"')
            role = _find(r'"role"\s*:\s*"([^"]+)"', search)
            if role is None:
                continue  # not an AFD process (prefiller, baseline, proxy)
            block = search
            connector = _find(r'"connector"\s*:\s*"([^"]+)"', block) or connector_dir
            attn = _find(r'"num_attention_ranks"\s*:\s*([^\s,}]+)', block)
            ffn = _find(r'"num_ffn_ranks"\s*:\s*([^\s,}]+)', block)
            afd_port = _find(r'"port"\s*:\s*([^\s,}]+)', block)
            dp = _find(r"--data-parallel-size\s+(\S+)", block)
            tp = _find(r"--tensor-parallel-size\s+(\S+)", block)
            ep = "yes" if "--enable-expert-parallel" in block else "no"
            graph_mode = _find(r'"cudagraph_mode"\s*:\s*"([^"]+)"', block)
            if "--enforce-eager" in block:
                mode = "eager"
            elif graph_mode:
                mode = f"graph ({graph_mode})"
            else:
                mode = "default"
            if "--enable-dbo" in block:
                dec = _find(r"--dbo-decode-token-threshold\s+(\S+)", block)
                pre = _find(r"--dbo-prefill-token-threshold\s+(\S+)", block)
                dbo = f"{dec or 'default'}/{pre or 'default'}"
            else:
                dbo = "off"
            http_port = _find(r"--port\s+(\S+)", block)
            rows.append({
                "path": rel,
                "hardware": hardware,
                "connector": connector,
                "model": model,
                "topology": _topology(stem, attn, ffn),
                "role": role,
                "dp": dp or "",
                "tp": tp or "",
                "ep": ep,
                "mode": mode,
                "dbo": dbo,
                "ranks": f"{attn or '?'} / {ffn or '?'}",
                "afd_port": afd_port or "",
                "http_port": http_port or "",
                "line": start_line,
            })
    return rows


def esc(s: str) -> str:
    return html.escape(s)


def cite(path: str, lineno: int) -> str:
    return "{{cite " + f"{path}:{lineno}" + "}}"


def render_table(rows: list[dict]) -> str:
    head = (
        "<thead><tr>"
        "<th>Recipe</th><th>HW</th><th>Connector</th><th>Model</th>"
        "<th>Topology</th><th>Role</th><th>DP</th><th>TP</th><th>EP</th>"
        "<th>Mode</th><th>DBO dec/pre</th><th>A/F ranks</th>"
        "<th>AFD port</th><th>HTTP port</th><th>Source</th>"
        "</tr></thead>"
    )
    body = []
    for r in rows:
        topo = "{{link " + TOPO_LINK + " | " + esc(r["topology"]) + "}}"
        body.append(
            "<tr>"
            f"<td><code>{esc(Path(r['path']).name)}</code></td>"
            f"<td>{esc(r['hardware'])}</td>"
            f"<td><code>{esc(r['connector'])}</code></td>"
            f"<td><code>{esc(r['model'])}</code></td>"
            f"<td>{topo}</td>"
            f"<td><code>{esc(r['role'])}</code></td>"
            f"<td><code>{esc(r['dp'])}</code></td>"
            f"<td><code>{esc(r['tp'])}</code></td>"
            f"<td>{esc(r['ep'])}</td>"
            f"<td>{esc(r['mode'])}</td>"
            f"<td><code>{esc(r['dbo'])}</code></td>"
            f"<td><code>{esc(r['ranks'])}</code></td>"
            f"<td><code>{esc(r['afd_port'])}</code></td>"
            f"<td><code>{esc(r['http_port'])}</code></td>"
            f"<td>{cite(r['path'], r['line'])}</td>"
            "</tr>"
        )
    return f"<table>{head}<tbody>" + "".join(body) + "</tbody></table>"


def build_body() -> str:
    rows = extract_rows()
    parts = [
        "<p><em>Generated by <code>tools/gen_recipes.py</code> from the "
        "<code>recipe/</code> shell scripts. One row per <code>vllm serve</code> "
        "call that carries an <code>&quot;afd&quot;</code> block. Do not edit "
        "between the markers.</em></p>",
        f"<p>{len(rows)} AFD serve blocks across the recipe scripts.</p>",
        render_table(rows),
    ]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    head = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    if head != SHA:
        sys.exit(f"{REPO} is at {head[:12]}, but explainer.json pins {SHA[:12]}")

    if args.report:
        for r in extract_rows():
            print(f"{r['path']}:{r['line']}  role={r['role']} topo={r['topology']} "
                  f"DP={r['dp']} TP={r['tp']} EP={r['ep']} mode={r['mode']} "
                  f"dbo={r['dbo']} ranks={r['ranks']} afd_port={r['afd_port']} "
                  f"http_port={r['http_port']} connector={r['connector']}")
        return 0

    body = build_body()
    page = PAGE.read_text(encoding="utf-8")
    if BEGIN not in page or END not in page:
        sys.exit(f"{PAGE}: markers {BEGIN} / {END} not found")
    start = page.index(BEGIN) + len(BEGIN)
    new = page[:start] + "\n" + body + "\n" + page[page.index(END):]
    if args.check:
        if new != page:
            print(f"{PAGE.relative_to(ROOT)} is out of date: "
                  "run python3 tools/gen_recipes.py")
            return 1
        print("recipes page is up to date")
        return 0
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
