# AFD Plugin Explained

A static website that teaches the [afd-plugin](https://github.com/vllm-project/afd-plugin) codebase step by
step. afd-plugin is a vLLM external plugin for Attention-FFN Disaggregation (AFD): the attention part and
the feed-forward (FFN/MoE) part of a model run in separate server processes and exchange hidden states
through a connector.

The site is for a reader who knows Python and the basics of LLM serving (prefill and decode, the KV cache,
batching, TP/PP/EP, MoE, CUDA graphs, vLLM as a server). It does not teach those basics. Each page starts
with a simple explanation. Then a "Deep dive" gives the full detail for study.

> **Status:** complete (2026-10-29). The site has 42 pages, and every page in the menu exists.
> See [`progress.md`](progress.md) for how each batch was written and checked.

## Code version

The site explains two exact versions. All code excerpts and `file:line` links point to these commits.
Line numbers can be different in newer versions.

| Repository | Commit | Date |
|---|---|---|
| afd-plugin | [`7452d52748fec2a858b63e4cb22941dadd7a3ee3`](https://github.com/vllm-project/afd-plugin/tree/7452d52748fec2a858b63e4cb22941dadd7a3ee3) | 2026-10-27 |
| vLLM v0.30.0 | [`ced6857afa0ea7b2e3f0846a62e1394e90f15607`](https://github.com/vllm-project/vllm/tree/ced6857afa0ea7b2e3f0846a62e1394e90f15607) | 2026-09-21 |

The site cites vLLM because afd-plugin is a plugin: it changes no vLLM source file, but it registers
models, selects worker classes and replaces some vLLM functions at load time. A citation with the prefix
`vllm:` points to the vLLM commit. afd-plugin targets this exact vLLM version
(`pyproject.toml:37`, `README.md:21`).

```bash
git clone https://github.com/vllm-project/afd-plugin.git
cd afd-plugin
git checkout 7452d52748fec2a858b63e4cb22941dadd7a3ee3

git clone https://github.com/vllm-project/vllm.git
cd vllm
git checkout ced6857afa0ea7b2e3f0846a62e1394e90f15607
```

Neither repository has submodules at these commits.

## Read the site

Open `site/index.html` in a browser. The site works from disk (`file://`), with no server.
It needs an internet connection only for the Inter font and for code colours (Prism from cdnjs).
Without it, the site uses a system font and plain code.

| Part | Folder | What it contains |
|---|---|---|
| Learn the basics | `learn/` | What AFD is, how vLLM plugins work, a map of the vLLM v1 processes |
| Concepts | `concepts/` | 19 pages in 7 groups: the plugin boundary, roles and topology, connectors, the model split, execution, deployment and tuning, Ascend NPU |
| Guided tours | `tours/` | Life of a request, start-up, one decode step, run a recipe |
| Code map | `code/` | A folder tree and one page for each important module |
| Reference | `reference/` | Generated tables for the AFD config keys, environment variables and recipes; a table of the compat patches; the glossary; the FAQ |

Press `/` to search. Point to a dotted word to see its glossary definition.
Three interactive visuals need JavaScript: a request stepper, a topology mapper and a DBO timeline.

## Build the site

Requirements: Python 3.11 or newer (standard library only), and checkouts of both repositories at the
commits above, at the paths in `explainer.json` (by default, folders next to this one).

```
parent/
  afd-plugin/            # git checkout at 7452d52 (read only)
  vllm/                  # git checkout at ced6857a (read only)
  afd-plugin-explainer/  # this repository
```

```bash
python3 tools/gen_folder_tree.py   # update the code-map folder tree
python3 tools/gen_afd_config.py    # update the AFD config tables
python3 tools/gen_env_vars.py      # update the environment-variable table
python3 tools/gen_recipes.py       # update the recipe table
python3 build.py                   # build site/ from src/
python3 build.py --strict          # also stop on warnings
python3 build.py --preview         # write site/ even when a page has errors
python3 build.py --force-diagrams  # run all diagram scripts again
```

Each generator also takes `--check`, which fails if its page is out of date.

The build reads code excerpts directly from the checkouts, so each excerpt is exact. It stops with an error
if either checkout is at a different commit, or if a link, a code citation or a glossary term is wrong.

To check the built site in a browser (needs Node and a Playwright Chromium):

```bash
node tools/site_check.js     # every page at 1280 and 390 px: overflow, JS errors, links, anchors
```

## Repository layout

| Path | Contents |
|---|---|
| `explainer.json` | Site name, both repository paths and URLs, both pinned commits, language style |
| `src/` | Page sources, navigation (`src/nav/`) and glossary (`src/glossary/`) |
| `diagrams/` | One Python script for each SVG diagram, and the shared helper `svglib.py` |
| `assets/` | Site CSS and JavaScript, and the interactive visuals (`assets/viz/`) |
| `tools/` | Generators for the reference tables and the folder tree, and the site-check script |
| `notes/facts.md` | Facts that were checked in the code and that all pages share |
| `notes/brief-writer.md`, `notes/brief-factcheck.md` | The shared briefs for the writer and fact-checker agents |
| `notes/survey/` | The first survey of the codebase. A guide, not a source |
| `build.py` | The site generator |
| `site/` | The built site. Do not edit it; it is not in git |
| `STYLE.md`, `instructions-svg.md` | The writer's guide and the diagram style guide |
| `plan.md`, `progress.md` | The project plan and the progress log |

## How the content is made

- The pages are written in ASD-STE100 Simplified Technical English.
- Each claim about the code has a citation to a file and line at the pinned commit of its repository.
- Each batch of pages was written by one agent. A different agent then compared each claim with the code
  and corrected the errors it found. Across the batches, the fact checks examined about 960 claims and
  corrected about 40. A final consistency pass then compared all pages with each other and with the shared
  facts, and corrected the rest. The most common faults were wrong line ranges, a citation that pointed at
  a comment instead of the code, and a call described at the wrong frequency (once per step against once
  per layer).
- Pages say what the code does, in neutral words. They make no claim that the code has a fault.
- Reference tables are generated from the source, not copied by hand.

### What is out of scope

- `csrc/` (about 46,000 lines of C and C++ kernel sources). The site explains only how the Python code
  selects, builds, loads and calls those kernels.
- The vendored Ascend binaries in `afd_plugin/connectors/npu/bin/`. The plugin's Python does not import
  them. The site explains how the plugin builds and loads its own Ascend extension (`afd_plugin._C_ascend`).
- Ascend NPU code in detail. One page, "Ascend NPU overview", covers the whole NPU surface (about 46 % of
  the plugin's Python) and points to the repository's own NPU documents.
- `tests/`, used as a source of facts only.

### Checks that were reduced to save budget

A full fact check examines every claim. For these module and reference pages, the checker instead examined
the first screen, every default, number, line count and call order, and about one claim in three:

- `code/config-py`, `code/validation-py`
- `code/connectors-core`, `code/p2p-py`
- `code/attention-worker`, `code/ffn-worker`, `code/deepseek-v2-py`
- `reference/env-vars`, `reference/recipes`

All basics pages, concept pages, tours, the home page, the glossary and the other reference pages had a
full fact check.

The pages were written with Claude Code and reviewed against the source code.
This site is not an official project of the afd-plugin or vLLM authors.
