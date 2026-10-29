#!/usr/bin/env python3
"""Generate the environment-variable table of src/reference/env-vars.html.

Parses the afd-plugin Python source at the pinned commit and lists every
environment variable the plugin reads or sets. It never imports afd_plugin or
vLLM: it walks the source with ``ast`` only, so it is safe to run on any
machine. Python 3 standard library only.

It resolves the key of each env access through these forms:
  * a string literal: ``os.environ.get("NAME")``;
  * a module-level string constant: ``os.getenv(_SOME_ENV)``;
  * a comprehension variable bound to a module-level tuple/list of strings
    (``os.environ.get(name) for name in _ASCEND_ENV_VARS``);
  * an f-string ``f"{prefix}_SUFFIX"`` where ``prefix`` is a local bound to a
    module-level dict of strings (the profiler families).

Access is found at ``os.environ.get`` / ``os.getenv`` / ``os.environ[...]`` /
``X in os.environ`` and at the plugin's own env helpers (``_env_bool``,
``_env_int``, ``_env_dir``, ``_prepend_env_path``).

Usage:
  python3 tools/gen_env_vars.py           # write the page
  python3 tools/gen_env_vars.py --check    # exit 1 if the page is out of date
  python3 tools/gen_env_vars.py --report   # print the extracted facts
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
PAGE = ROOT / "src" / "reference" / "env-vars.html"
BEGIN = "<!-- BEGIN GENERATED env-vars -->"
END = "<!-- END GENERATED env-vars -->"

HELPERS = {"_env_bool", "_env_int", "_env_dir", "_prepend_env_path"}
SET_HELPERS = {"_prepend_env_path"}


def source_files() -> list[Path]:
    files = sorted((REPO / "afd_plugin").rglob("*.py"))
    files.append(REPO / "setup.py")
    return files


class ModuleScope:
    """Resolvable module-level names for one source file."""

    def __init__(self, tree: ast.Module):
        self.str_const: dict[str, str] = {}
        self.dict_const: dict[str, dict[str, ast.expr]] = {}
        self.seq_const: dict[str, list[str]] = {}
        self.const: dict[str, ast.expr] = {}  # any simple module-level constant
        for node in tree.body:
            targets = []
            value = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(
                node.targets[0], ast.Name
            ):
                targets = [node.targets[0].id]
                value = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
                value = node.value
            if not targets or value is None:
                continue
            name = targets[0]
            if isinstance(value, ast.Constant):
                self.const[name] = value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                self.str_const[name] = value.value
            elif isinstance(value, ast.Dict) and all(
                isinstance(k, ast.Constant) and isinstance(k.value, str)
                for k in value.keys
            ):
                self.dict_const[name] = {
                    k.value: v for k, v in zip(value.keys, value.values)
                }
            elif isinstance(value, (ast.Tuple, ast.List)) and all(
                isinstance(e, ast.Constant) and isinstance(e.value, str)
                for e in value.elts
            ):
                self.seq_const[name] = [e.value for e in value.elts]


def _slice_name(node: ast.Subscript) -> str | None:
    s = node.slice
    if isinstance(s, ast.Name):
        return s.id
    if isinstance(s, ast.Index) and isinstance(s.value, ast.Name):  # py<3.9
        return s.value.id
    return None


def _collect_bindings(tree: ast.Module, scope: ModuleScope):
    """Return prefix-locals and comprehension variables.

    prefix-local: ``x = DICT[role]`` -> x maps to (DICT name, role var name).
    comp var: ``for v in SEQ`` over a module seq -> v maps to [values].
    """
    prefix_local: dict[str, tuple[str, str]] = {}
    comp_var: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(
            node.targets[0], ast.Name
        ):
            val = node.value
            if (
                isinstance(val, ast.Subscript)
                and isinstance(val.value, ast.Name)
                and val.value.id in scope.dict_const
            ):
                rolevar = _slice_name(val)
                if rolevar:
                    prefix_local[node.targets[0].id] = (val.value.id, rolevar)
        if isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name):
            if isinstance(node.iter, ast.Name) and node.iter.id in scope.seq_const:
                comp_var[node.target.id] = scope.seq_const[node.iter.id]
    return prefix_local, comp_var


def _resolve_key(node: ast.expr, scope, prefix_local, comp_var):
    """Return a list of (name, role_or_None); empty if unresolved."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [(node.value, None)]
    if isinstance(node, ast.Name):
        if node.id in scope.str_const:
            return [(scope.str_const[node.id], None)]
        if node.id in comp_var:
            return [(v, None) for v in comp_var[node.id]]
        if node.id in prefix_local:
            dname, _ = prefix_local[node.id]
            return [(v.value, k) for k, v in scope.dict_const[dname].items()
                    if isinstance(v, ast.Constant)]
        return []
    if isinstance(node, ast.JoinedStr):
        combos: list[tuple[str, str | None]] = [("", None)]
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                combos = [(s + part.value, r) for s, r in combos]
            elif isinstance(part, ast.FormattedValue):
                sub = _resolve_key(part.value, scope, prefix_local, comp_var)
                if not sub:
                    return []
                combos = [
                    (s + add, role or r) for s, r in combos for add, role in sub
                ]
            else:
                return []
        return combos
    return []


def _resolve_default(node, scope, prefix_local, role):
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return ast.unparse(node)
    if isinstance(node, ast.Name) and node.id in scope.const:
        return ast.unparse(scope.const[node.id])
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in scope.dict_const
        and role is not None
    ):
        dic = scope.dict_const[node.value.id]
        if role in dic:
            return ast.unparse(dic[role])
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _is_os_env_get(func: ast.expr) -> bool:
    # os.environ.get(...)
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "get"
        and isinstance(func.value, ast.Attribute)
        and func.value.attr == "environ"
        and isinstance(func.value.value, ast.Name)
        and func.value.value.id == "os"
    )


def _is_os_getenv(func: ast.expr) -> bool:
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "getenv"
        and isinstance(func.value, ast.Name)
        and func.value.id == "os"
    )


def _is_os_environ_subscript(node: ast.expr) -> bool:
    # os.environ[...]
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "environ"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "os"
    )


def extract_from_file(path: Path) -> list[dict]:
    rel = path.relative_to(REPO).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    scope = ModuleScope(tree)
    prefix_local, comp_var = _collect_bindings(tree, scope)
    hits: list[dict] = []

    def add(key_node, default_node, lineno, kind):
        for name, role in _resolve_key(key_node, scope, prefix_local, comp_var):
            hits.append({
                "name": name,
                "default": _resolve_default(default_node, scope, prefix_local, role),
                "path": rel,
                "line": lineno,
                "kind": kind,
            })

    # Collect os.environ[...] subscripts that are assignment targets, so the
    # generic read branch does not count them again.
    set_targets: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target])
            for t in targets:
                if _is_os_environ_subscript(t):
                    set_targets.add(id(t))

    # os.environ[KEY] = ... (sets)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if _is_os_environ_subscript(t):
                    add(t.slice if not isinstance(t.slice, ast.Index) else t.slice.value,
                        None, node.lineno, "sets")
        # KEY in os.environ (reads, presence)
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.In, ast.NotIn)) and (
                    (isinstance(comp, ast.Attribute) and comp.attr == "environ"
                     and isinstance(comp.value, ast.Name) and comp.value.id == "os")
                ):
                    add(node.left, None, node.lineno, "reads")
        # reads from os.environ[KEY] used as a value (not an assignment target)
        if _is_os_environ_subscript(node) and id(node) not in set_targets:
            key = node.slice if not isinstance(node.slice, ast.Index) else node.slice.value
            add(key, None, node.lineno, "reads")
        # calls
        if isinstance(node, ast.Call):
            func = node.func
            if _is_os_env_get(func) or _is_os_getenv(func):
                key = node.args[0] if node.args else None
                default = node.args[1] if len(node.args) > 1 else None
                if key is not None:
                    add(key, default, node.lineno, "reads")
            elif isinstance(func, ast.Name) and func.id in HELPERS:
                key = node.args[0] if node.args else None
                default = None
                for kw in node.keywords:
                    if kw.arg == "default":
                        default = kw.value
                if key is not None:
                    kind = "prepends" if func.id in SET_HELPERS else "reads"
                    add(key, default, node.lineno, kind)
    return hits


def aggregate() -> list[dict]:
    by_name: dict[str, dict] = {}
    for path in source_files():
        for h in extract_from_file(path):
            agg = by_name.setdefault(h["name"], {
                "name": h["name"], "defaults": [], "sites": [], "kinds": set(),
            })
            if h["default"] is not None and h["default"] not in agg["defaults"]:
                agg["defaults"].append(h["default"])
            site = (h["path"], h["line"])
            if site not in agg["sites"]:
                agg["sites"].append(site)
            agg["kinds"].add(h["kind"])
    rows = []
    for name in sorted(by_name):
        agg = by_name[name]
        agg["sites"].sort()
        rows.append(agg)
    return rows


def esc(s: str) -> str:
    return html.escape(s)


def cite(path: str, lineno: int) -> str:
    return "{{cite " + f"{path}:{lineno}" + "}}"


def render_table(rows: list[dict]) -> str:
    head = ("<thead><tr><th>Variable</th><th>Default</th><th>Kind</th>"
            "<th>Read at</th></tr></thead>")
    body = []
    for r in rows:
        default = " / ".join(f"<code>{esc(d)}</code>" for d in r["defaults"]) or "&mdash;"
        kinds = ", ".join(sorted(r["kinds"]))
        sites = " ".join(cite(p, ln) for p, ln in r["sites"])
        body.append(
            f"<tr><td><code>{esc(r['name'])}</code></td>"
            f"<td>{default}</td><td>{esc(kinds)}</td><td>{sites}</td></tr>"
        )
    return f"<table>{head}<tbody>" + "".join(body) + "</tbody></table>"


def build_body() -> str:
    rows = aggregate()
    parts = [
        "<p><em>Generated by <code>tools/gen_env_vars.py</code> from "
        "<code>afd_plugin/**</code> and <code>setup.py</code>. Each variable is "
        "listed with its default (when the read site gives one), whether the "
        "plugin reads, sets or prepends it, and every source line. Do not edit "
        "between the markers.</em></p>",
        f"<p>{len(rows)} environment variables.</p>",
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
        for r in aggregate():
            sites = ", ".join(f"{p}:{ln}" for p, ln in r["sites"])
            print(f"{r['name']}  default={r['defaults']}  "
                  f"kind={sorted(r['kinds'])}  [{sites}]")
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
                  "run python3 tools/gen_env_vars.py")
            return 1
        print("env-vars page is up to date")
        return 0
    PAGE.write_text(new, encoding="utf-8")
    print(f"wrote {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
