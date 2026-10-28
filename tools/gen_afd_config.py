#!/usr/bin/env python3
"""Generate the AFD config tables of src/reference/afd-config.html.

Reads the afd-plugin source at the pinned commit and writes three tables
between the markers in the page:
  1. the ``AFDConfig`` dataclass fields (the ``afd`` keys): name, alias, type,
     default, the field comment, and a {{cite}} from the AST line number;
  2. the P2P connector's ``connector_extra_config`` (none accepted);
  3. the two NPU connectors' ``connector_extra_config`` keys and defaults.

It never imports afd_plugin or vLLM: it parses the source with ``ast`` only, so
it is safe to run on any machine. Python 3 standard library only.

Usage:
  python3 tools/gen_afd_config.py           # write the page
  python3 tools/gen_afd_config.py --check    # exit 1 if the page is out of date
  python3 tools/gen_afd_config.py --report   # print the extracted facts
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "explainer.json").read_text(encoding="utf-8"))
REPO = (ROOT / CFG["repo_path"]).resolve()
SHA = CFG["sha"]
PAGE = ROOT / "src" / "reference" / "afd-config.html"
BEGIN = "<!-- BEGIN GENERATED afd-config -->"
END = "<!-- END GENERATED afd-config -->"

CONFIG_PY = "afd_plugin/config.py"
P2P_PY = "afd_plugin/connectors/gpu/p2p.py"
CAMP2P_PY = "afd_plugin/connectors/npu/camp2p.py"
ASYNC_PY = "afd_plugin/connectors/npu/async_cam.py"

# coerce helper -> the type shown in the table
COERCE_TYPE = {
    "coerce_extra_int": "int",
    "coerce_extra_positive_int": "int &gt; 0",
    "coerce_optional_extra_positive_int": "int &gt; 0, or null",
    "coerce_extra_bool": "bool",
    "coerce_extra_str": "str",
}


def read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def cite(path: str, lineno: int) -> str:
    """An inline {{cite}} tag the build turns into a link. Not HTML-escaped."""
    return "{{cite " + f"{path}:{lineno}" + "}}"


# ---- AFDConfig fields ------------------------------------------------------
def _field_comment(lines: list[str], lineno: int) -> str:
    """Join the contiguous ``#`` comment lines directly above a field."""
    out: list[str] = []
    i = lineno - 2  # 0-based index of the line above the field
    while i >= 0:
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            out.append(stripped.lstrip("#").strip())
            i -= 1
        else:
            break
    return " ".join(reversed(out))


def _default_str(node: ast.expr | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "field":
        return "{} (empty mapping)"
    return ast.unparse(node)


def extract_afd_fields() -> list[dict]:
    src = read(CONFIG_PY)
    lines = src.splitlines()
    tree = ast.parse(src)

    # alias map: alias -> canonical field. The source annotates it
    # (``_ALIASES: Final[...] = {...}``), so it is an AnnAssign, not an Assign.
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        target_name = ""
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target_name = getattr(node.targets[0], "id", "")
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target_name = getattr(node.target, "id", "")
            value = node.value
        if target_name == "_ALIASES" and isinstance(value, ast.Dict):
            for k, v in zip(value.keys, value.values):
                aliases[ast.literal_eval(k)] = ast.literal_eval(v)
    canonical_to_alias = {v: k for k, v in aliases.items()}

    cls = next(
        n for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "AFDConfig"
    )
    fields: list[dict] = []
    for stmt in cls.body:
        if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
            continue
        name = stmt.target.id
        fields.append({
            "name": name,
            "alias": canonical_to_alias.get(name, ""),
            "type": ast.unparse(stmt.annotation),
            "default": _default_str(stmt.value),
            "comment": _field_comment(lines, stmt.lineno),
            "lineno": stmt.lineno,
        })
    return fields


# ---- connector extra-config (from each from_mapping) -----------------------
def extract_extra_fields(path: str, class_name: str) -> list[dict]:
    """Read ``cls(key=coerce_x(raw.get("K", DEFAULT), ...))`` from from_mapping."""
    src = read(path)
    tree = ast.parse(src)
    cls = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == class_name
    )
    func = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "from_mapping"
    )
    rows: list[dict] = []
    for node in ast.walk(func):
        # a coerce_*() call whose first argument is raw.get("KEY", DEFAULT)
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") in COERCE_TYPE):
            continue
        if not node.args:
            continue
        getcall = node.args[0]
        if not (
            isinstance(getcall, ast.Call)
            and isinstance(getcall.func, ast.Attribute)
            and getcall.func.attr == "get"
            and getcall.args
            and isinstance(getcall.args[0], ast.Constant)
        ):
            continue
        key = getcall.args[0].value
        default = ast.unparse(getcall.args[1]) if len(getcall.args) > 1 else "None"
        rows.append({
            "key": key,
            "type": COERCE_TYPE[node.func.id],
            "default": default,
            "lineno": getcall.lineno,
        })
    rows.sort(key=lambda r: r["lineno"])
    return rows


def extract_p2p_reject_line() -> int:
    src = read(P2P_PY)
    tree = ast.parse(src)
    cls = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == "P2pNcclAFDConnector"
    )
    func = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "parse_extra_config"
    )
    # the ValueError raise inside parse_extra_config
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call)
            and getattr(node.exc.func, "id", "") == "ValueError"
        ):
            return node.lineno
    return func.lineno


# ---- rendering -------------------------------------------------------------
def esc(s: str) -> str:
    return html.escape(s)


def render_afd_table(fields: list[dict]) -> str:
    head = ("<thead><tr><th>Key</th><th>Alias</th><th>Type</th><th>Default</th>"
            "<th>What it is</th><th>Source</th></tr></thead>")
    rows = []
    for f in fields:
        alias = f"<code>{esc(f['alias'])}</code>" if f["alias"] else "&mdash;"
        default = f"<code>{esc(f['default'])}</code>" if f["default"] else "&mdash;"
        rows.append(
            f"<tr><td><code>{esc(f['name'])}</code></td><td>{alias}</td>"
            f"<td><code>{esc(f['type'])}</code></td><td>{default}</td>"
            f"<td>{esc(f['comment'])}</td>"
            f"<td>{cite(CONFIG_PY, f['lineno'])}</td></tr>"
        )
    return f"<table>{head}<tbody>" + "".join(rows) + "</tbody></table>"


def render_extra_table(path: str, rows: list[dict]) -> str:
    head = ("<thead><tr><th>Key</th><th>Type</th><th>Default</th>"
            "<th>Source</th></tr></thead>")
    body = []
    for r in rows:
        default = f"<code>{esc(r['default'])}</code>"
        body.append(
            f"<tr><td><code>{esc(r['key'])}</code></td>"
            f"<td><code>{r['type']}</code></td><td>{default}</td>"
            f"<td>{cite(path, r['lineno'])}</td></tr>"
        )
    return f"<table>{head}<tbody>" + "".join(body) + "</tbody></table>"


def build_body() -> str:
    fields = extract_afd_fields()
    p2p_line = extract_p2p_reject_line()
    camp2p = extract_extra_fields(CAMP2P_PY, "CAMP2PExtraInfo")
    async_fields = extract_extra_fields(ASYNC_PY, "AFDAsyncExtraInfo")

    parts = [
        "<p><em>Generated by <code>tools/gen_afd_config.py</code> from "
        f"<code>{CONFIG_PY}</code> and the connector source. Do not edit between "
        "the markers.</em></p>",
        f"<h3>The <code>afd</code> keys</h3>",
        render_afd_table(fields),
        "<h3><code>connector_extra_config</code> by connector</h3>",
        "<p><strong><code>P2pNcclAFDConnector</code> (GPU):</strong> no keys. "
        "A non-empty <code>connector_extra_config</code> raises "
        f"<code>ValueError</code> ({cite(P2P_PY, p2p_line)}).</p>",
        "<h4><code>CAMP2pAFDConnector</code> (NPU)</h4>",
        render_extra_table(CAMP2P_PY, camp2p),
        "<h4><code>CAMAsyncAFDConnector</code> (NPU)</h4>",
        "<p>The async connector accepts the wire key <code>dynamicQuant</code> "
        "for its typed field <code>dynamic_quant</code>.</p>",
        render_extra_table(ASYNC_PY, async_fields),
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
        for f in extract_afd_fields():
            print(f"afd.{f['name']} = {f['default']}  ({CONFIG_PY}:{f['lineno']})")
        for r in extract_extra_fields(CAMP2P_PY, "CAMP2PExtraInfo"):
            print(f"CAMP2p.{r['key']} = {r['default']}  ({CAMP2P_PY}:{r['lineno']})")
        for r in extract_extra_fields(ASYNC_PY, "AFDAsyncExtraInfo"):
            print(f"CAMAsync.{r['key']} = {r['default']}  ({ASYNC_PY}:{r['lineno']})")
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
                  "run python3 tools/gen_afd_config.py")
            return 1
        print("afd-config page is up to date")
        return 0
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
