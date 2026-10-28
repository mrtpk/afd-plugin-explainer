# AFD Plugin Explainer — Plan

Status: **APPROVED 2026-10-28 ("defaults ok"). Run unattended to the end, with a usage pause after each subagent.**
Date: 2026-10-28
Source repo: `../afd-plugin` at commit `7452d52` (https://github.com/vllm-project/afd-plugin)
Second pinned repo (cited, read only): `../vllm` at commit `ced6857a` (v0.30.0, https://github.com/vllm-project/vllm)

---

## 1. Goal

Make a static study site, "AFD Plugin Explained", that teaches what Attention-FFN Disaggregation (AFD) is
and how afd-plugin adds it to vLLM v0.30.0 without changes to the vLLM source.
After the site, the reader understands the plugin boundary (entry point, `--additional-config`, role
workers, model runners, model wrappers, connectors, compat shims), how one request and one step run across
attention and FFN workers, and how to deploy and tune AFD with the recipes.
Every claim cites `file:line` at the two pinned commits.

## 2. Decisions

Decisions marked **(user)** come from the task text; the rest were proposed defaults, approved 2026-10-28 (§11).

| Topic | Decision |
|---|---|
| Reader | **(user)** Knows Python and LLM-serving basics (prefill/decode, KV cache, batching, TP/PP/EP, MoE, CUDA graphs, vLLM as a server). The site does not teach these; at most one line of recap per page. |
| Depth of detail | Proposed: a short start + a full "Deep dive" on every page. Module pages get shorter deep dives (concept pages carry the detail). |
| Hosting | **(user)** Local first (`site/` opens from disk). CDN OK (cdnjs, jsDelivr, unpkg, Google Fonts). |
| Structure | Proposed: home + 5 parts, **41 pages** (§4). Not one page per file. |
| Location | Proposed: `test-harness/afd-plugin-explainer/` (this folder). `../afd-plugin` and `../vllm` stay unchanged. |
| Site language | **(user)** ASD-STE100 (`language_style: ste`). |
| Scope | **(user)** `afd_plugin/`, `recipe/`, `docs/`, `tools/` in scope. `csrc/` out of scope: only how the Python code selects, builds/loads and calls kernels. Tests: source of facts only. **NPU: GPU in full depth + one overview page (approved 2026-10-28).** |
| Name | **(user)** "AFD Plugin Explained". |
| Sibling site | **(user)** None. No links to other explainer sites; no `basics-covered.md`. |
| Look | **(user)** Light article look (light always; dark only by toggle). Diagrams per `instructions-svg.md` + STYLE.md §10. |
| Code version | **(user)** afd-plugin `7452d52748fec2a858b63e4cb22941dadd7a3ee3` (2026-10-27, "Provide a skill for benchmarking AFD recipes (#465)"); vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607` (v0.30.0, 2026-09-21). Both in `explainer.json`, the home page `#code-version` and the README. vLLM cited only at that commit. |
| Checkpoint | Proposed: no separate Phase 1 stop (user: "after the approval you may run unattended"). The usage pause after the Phase 1 fact check shows the sample pages; the user can comment there. |
| Git | **(user)** Commit per stage: writer commit "(fact check pending)", then "fact-checked". Author `Thomas Paul <contact@thomaspaul.dev>`, repo-local. Push or publish only on request. Proposed: `site/` not committed (generated; `.gitignore`). |
| Bug claims | **(user)** Pages state what the code does, in neutral words. Suspected bugs go to the user, not to pages. |
| Budget | **(user)** Subagents of type `explainer-worker`; at most 2 at a time; subagents never start subagents; stay under 50 % of the weekly limit → **one subagent at a time, pause after each for `/usage`**. Final site check = supervisor script. Budget mode: proposal in §8. |

## 3. Facts about the codebase (from the survey, spot-checked)

- afd-plugin: 595 tracked files, 651 commits, no submodules, Git LFS for binaries. `afd_plugin/` = 78 Python
  files (82 files in total), 20,195 lines: NPU-specific about 9.3k, GPU-specific about 1.4k, shared about 9.5k (the "shared"
  runners and model wrappers are CUDA paths in practice). `csrc/` = 45.6k lines C/C++ (out of scope).
  `tests/` = 40.9k lines. `docs/` = 4.7k lines Markdown. `tools/proxy_server.py` = 1,351 lines (copied from
  vLLM-Ascend; a prefill/decode proxy, not the A/F split).
- Entry point: `[project.entry-points."vllm.general_plugins"] afd = "afd_plugin:register_afd"`
  (`pyproject.toml:45-46`). `register_afd()` applies 4 patch modules, registers a routing strategy, a DBO
  custom op, the Ascend config patch (NPU only) and `AFD<arch>` model wrappers (`afd_plugin/__init__.py:142-216`).
- vLLM plugin loader: `vllm/plugins/__init__.py` (5 groups, `load_general_plugins` with the `plugins_loaded`
  guard, `VLLM_PLUGINS` filter); 5 call sites (`arg_utils.py:839`, `:3009`, `v1/engine/core.py:119`,
  `v1/worker/worker_base.py:271`, `model_executor/models/registry.py:1570`). Checked by the supervisor.
- Role workers are not registered through a vLLM API: a patched `EngineArgs.create_engine_config` rewrites
  `parallel_config.worker_cls` when it is `"auto"` (`compat/patches/config_validation.py:58-62,92-93,179-197`).
- The FFN side has no scheduler and no KV cache: its EngineCore returns after the executor is built; its
  worker runs a connector-driven loop. Requests go only to the attention API server.
- Model split: on the attention role, the FFN stage of each decoder layer is a parameter-free
  `RemoteFFNProxy` that sends hidden states and receives the FFN output through the connector.
- 3 connectors: `P2pNcclAFDConnector` (CUDA, with control plane), `CAMP2pAFDConnector` (NPU, sync, control
  plane), `CAMAsyncAFDConnector` (NPU, async, `control_plane = None`).
- Both roles need `VLLM_USE_V2_MODEL_RUNNER=1`. CUDA graphs: only `FULL_DECODE_ONLY`. DBO: exactly 2 ubatches.
- Models: DeepSeek V2/V3/V3.2/V4, GLM-MoE-DSA, Qwen3-MoE, Qwen3.5/3.6-MoE (CUDA text only).
- Good docs: `docs/design/module/*.md` (9 files, 2.9k lines; written against an older commit `36dadb4`:
  use as hints only), GPU/NPU connector user guides, recipe READMEs. Reusable images:
  `docs/assets/vllm-afd-plugin-architecture.svg`, `docs/npu/dbo.png`, recipe result PNGs.
- No comments in other languages. `AGENTS.md` + `.agents/skills/` (10 contributor skills) exist.
- Survey files: `notes/survey/survey.md`, `notes/survey/vllm-plugin-hooks.md` (a guide, not a source).

## 4. Site structure (41 pages + generated glossary)

```
afd-plugin-explainer/site/
  index.html     Home: what AFD is, system map, "Start here", code version (both commits)
  learn/         PART 1 — Basics (3)
  concepts/      PART 2 — Concepts (19, in 7 groups)
  tours/         PART 3 — Guided tours (4)
  code/          PART 4 — Folder tree + 8 module pages (9)
  reference/     PART 5 — Generated tables, patch table, FAQ (5) + glossary
```

### Home (1)
- `index`: what AFD and afd-plugin are; fact table; system map (attention server | connector | FFN server,
  with the plugin parts on each side); Start here; how to use; code version for both repos.

### Part 1 — Learn the basics (3)
1. `learn/what-is-afd`: why split attention and FFN (memory-bound attention with KV vs. compute-bound
   FFN/MoE weights), xAyF ratios, how AFD differs from prefill/decode disaggregation and from EP. Short "In
   afd-plugin" pointers.
2. `learn/vllm-plugins`: **How vLLM plugins work** (user request). Entry-point groups, `load_general_plugins`,
   when and in which processes it runs, the `plugins_loaded` guard, `VLLM_PLUGINS`, how a plugin registers
   models (`ModelRegistry.register_model`), workers (`worker_cls`) and config (`additional_config`); what a
   plugin can and cannot change. Brief; cites vLLM at `ced6857a`.
3. `learn/vllm-v1-map`: the vLLM v1 process and class map that AFD hooks into (API server → EngineCore →
   executor → worker → Model Runner V2 → model), one line per box, with the AFD hook point on each.

### Part 2 — Concepts (19)
- **Plugin boundary:** `plugin-entry-point` (register_afd, idempotence, import safety, spawn override) ·
  `afd-config` (`--additional-config["afd"]` schema, aliases, normalization, validation) ·
  `worker-selection` (auto `worker_cls` rewrite, runner swap in `init_device`, `assert_compatible_afd_stack`) ·
  `model-registration` (`AFD<arch>` names, lazy registration, `get_afd_model_config`) ·
  `compat-patches` (patch discipline, version gate, what each patch replaces and when it is active).
- **Roles and topology:** `roles` (attention vs. FFN: what each side owns; FFN = daemon, no scheduler, no
  KV) · `topology` (`[F0..A0..]` world, role rank from DP/PCP/TP, `build_rank_mapping`, A ≥ F rule,
  plugin-owned process groups, timeouts).
- **Connectors:** `connector-contract` (ABC, lifecycle, the 4 send/recv calls, factory) · `control-plane`
  (DP metadata, JSON control payloads, buffer pre-allocation) · `wire-data` (what tensors cross per layer
  and stage; transfer metadata; per-peer split and concat).
- **Model split:** `model-wrappers` (role-aware decoder layer, `RemoteFFNProxy`; DeepSeek, Qwen3-MoE,
  Qwen3.5, DeepSeek-V4 differences) · `moe-handoff` (gate placement, `compute_gate_on_attention`, remote
  experts, `router_logits` and `input_ids`).
- **Execution:** `attention-runtime` (AFD seam over native Model Runner V2, execution context, metadata
  provider) · `ffn-runtime` (FFN runner, server loop, layers × stages forward) · `cuda-graphs`
  (`FULL_DECODE_ONLY`, attention capture/replay hook, FFN graph keys, warm-up handshake) · `dbo` (2 ubatches,
  `manual_dbo_yield` op, DP1 DBO scoped patches).
- **Deploy and tune:** `deployment-topologies` (2a2f, 4a4f, 2p1a1f with proxy, multipod; DP/TP choices) ·
  `tuning` (rank ratio, DBO thresholds, capture sizes, timeouts, profiler, routing simulator, benchmarks).
- **Ascend NPU** (size depends on Q1; default = overview): `npu-overview` (same contract, different
  transport: CAM P2P vs. CAM async; prebuilt operators and how they load; async DP patches; pointer table).

### Part 3 — Guided tours (4)
1. `tours/start-up` — `vllm serve` on both roles → plugin load → config patch → worker selection → FFN
   EngineCore early return → connector handshake → graph warm-up → FFN server loop (~12 stops).
2. `tours/life-of-a-request` — HTTP request → attention API server → scheduler → attention runner → per-layer
   send/receive → FFN → back → sampling → response (~12 stops). Always written.
3. `tours/one-decode-step` — one step on a 2a2f topology, layer by layer, 2 DBO ubatches, control metadata,
   graph replay on both sides (~10 stops).
4. `tours/run-a-recipe` — `2a2f_graph_dbo_dp1tp2.sh` line by line: what each flag does inside the plugin (~8 stops).

### Part 4 — Code map (9)
- `code/index`: folder tree (`tools/gen_folder_tree.py`), line counts, GPU/NPU/shared marking, dependencies.
- Module pages: `code/init-py` (`afd_plugin/__init__.py`) · `code/config-py` (`config.py`, `config_utils.py`,
  `envs.py`) · `code/validation-py` · `code/connectors-core` (`base.py`, `factory.py`, `metadata.py`) ·
  `code/p2p-py` (`connectors/gpu/p2p.py`) · `code/attention-worker` (`attention_worker.py`,
  `attention_model_runner_v2.py`, `attention_metadata.py`) · `code/ffn-worker` (`ffn_worker.py`,
  `ffn_model_runner.py`, `ffn_metadata.py`) · `code/deepseek-v2-py`.
- Other files: in the tree with one line each, explained on concept pages.

### Part 5 — Reference (5 + glossary)
- `reference/afd-config`: all `afd` keys and `connector_extra_config` keys per connector; generated by
  `tools/gen_afd_config.py` from `config.py` and the connector `parse_extra_config` code.
- `reference/env-vars`: generated by `tools/gen_env_vars.py` (grep of `os.environ`/`envs.*` in `afd_plugin/`, `setup.py`).
- `reference/recipes`: generated by `tools/gen_recipes.py` from `recipe/**/*.sh` (topology, roles, ranks,
  DBO and graph flags).
- `reference/compat-patches`: patch module → vLLM target (`file:line` at `ced6857a`) → when active. Hand
  table with citations (fact-checked).
- `reference/faq`: short answers; "Where do docs and code disagree?"; "Known open questions".
- Glossary: generated by `build.py`.

## 5. Page design

Templates: STYLE.md §4 (basics, concept, tour, module, reference). Every concept and tour page: diagram,
code excerpts, deep dive, "Check yourself". Module pages: shorter deep dive, level, quiz.

### Interactive visuals (vanilla JS, 3)
- `request-stepper` (tour life-of-a-request): Next/Back through the stops; shows which process and side is active.
- `topology-mapper` (concept topology): set attention DP/TP and FFN DP/TP; see the `[F0..A0..]` world, role
  ranks and P2P subgroups (rules copied from `topology.py`).
- `dbo-timeline` (concept dbo / tour one-decode-step): 2 ubatches × N layers on attention and FFN lanes; step
  through send, yield, receive.

## 6. Technology

Starter kit of the skill: static HTML, `build.py` (standard library only), `explainer.json`, SVG diagrams from
Python scripts with `svglib.py`, Prism from cdnjs, Inter from Google Fonts. `site/` opens from disk.

**Tooling change (supervisor, Phase 1a):** `build.py` supports one repo. I add a second pinned repo:
`explainer.json` key `extra_repos: {"vllm": {path, url, sha, label}}`; citation syntax
`{{cite vllm:vllm/plugins/__init__.py:77-90}}` and `<x-code repo="vllm" file=... lines=...>`; the same
commit check (the build fails if `../vllm` is not at `ced6857a`); both commits in the footer and
`#code-version`.

## 7. Writing rules

STYLE.md §6-7 and `skills/codebase-explainer/references/writing-and-accuracy.md`. Every claim about the code
cites `file:line` at the pinned commit of its repo. Fixed vocabulary (STYLE.md): attention role / FFN role
(not "A node"/"E node" in prose; xAyF only in topology names), connector, control plane, stage (= DBO
ubatch index on the wire), step, rank.

## 8. How the supervisor works

- Supervisor + `explainer-worker` subagents (`.claude/agents/explainer-worker.md`; model `claude-opus-4-8`,
  effort high — Q4). **One subagent at a time; pause after each one for the user to check `/usage`.**
  Subagents never start subagents (in both briefs and the agent definition).
- Writer → build 0 errors → commit "(fact check pending)" → separate fact checker → build → supervisor
  review (bug claims verified, facts merged) → commit "fact-checked".
- Shared briefs: `notes/brief-writer.md`, `notes/brief-factcheck.md`.
- **Budget mode (proposal, Q3):**
  1. Shared briefs: yes.
  2. Full fact check for basics, concepts, tours, the home page and every page with defaults, numbers or
     call order (reference/afd-config, env-vars, compat-patches). **Sample check (1 claim in 3) for module
     pages and the generated recipes table.** Skipped items are listed in `progress.md` and the README.
  3. Shorter deep dives on module pages (the concept pages carry the detail).
  4. Site check as a supervisor script (Playwright), not a subagent.
  5. Final consistency pass limited to the FINAL-PASS TODO list + a `notes/facts.md` sweep.
- Session note: the edited agent definition loads only in a new session. After approval: the user runs
  `/exit` then `claude --continue`; I re-run the no-tools test before Phase 1a.

## 9. Definition of done

- All 41 planned pages exist (or the user deferred them) and `python3 build.py` has 0 errors.
- Every concept and tour page has a diagram, code excerpts, a deep dive and "Check yourself".
- Every batch is fact-checked (sample checks where §8 allows, listed); the FINAL-PASS TODO list is empty.
- Site check at 1280 and 390 px: no overflow, no JS errors, no broken links; every visual works.
- A reader can follow Home → Basics → Tour "Life of a request" with no dead end.
- Both pinned commits on the home page, in `explainer.json` and in the README.
- Skipped checks are listed in `progress.md` and the README.

## 10. Risks

| Risk | What we do |
|---|---|
| Wrong explanations | Writers read the code; separate fact check per batch; citations always |
| Design docs older than the code (`36dadb4`) | Write from the code; docs as hints; differences go to the FAQ |
| vLLM citations at the wrong commit | Second-repo commit check in `build.py` |
| Patches are subtle (scoped monkey-patches, `worker_cls` rewrite) | Hard fact-check focus; supervisor re-reads every "bug" claim |
| NPU code is 46 % of the plugin | Scope decision Q1; out-of-scope parts are named on the home page |
| Budget | One subagent at a time with pauses; budget mode §8; priority Basics → Tour 2 → core concepts → code → reference |
| Stale agent definition in this session | Restart before Phase 1a; re-test |

## 11. Answers from the user (2026-10-28)

User: "defaults ok". So:
1. NPU scope: GPU in full depth + one overview page `concepts/npu-overview`. NPU runners, NPU model files and
   NPU patches get no own pages; they appear in the code tree and on the overview page.
2. Structure: 41 pages as in §4.
3. Budget mode: all items of §8 (sample check 1 in 3 for module pages and the generated recipes table).
4. Subagents: `explainer-worker`, model `claude-opus-4-8`, effort high.
5. No separate Phase 1 stop (samples shown at the usage pause after the Phase 1 fact check); `site/` not committed.
6. Short start + full deep dive on every page (shorter on module pages); folder `test-harness/afd-plugin-explainer/`.

## 12. Phase 1 in detail

| Step | Work | Who |
|---|---|---|
| 1a-0 | Copy starter kit, `git init`, author, `explainer.json`, two-repo support in `build.py`, build 0 errors | supervisor |
| 1a | STYLE.md for this project, nav files with all 41 pages, core glossary, sample concept page `concepts/connector-contract` + diagram | subagent F1 |
| 1b-1 | Samples S1: home (system map, `#code-version`), `learn/vllm-plugins`, `code/index` (tree), `code/init-py` | subagent W-S1 |
| 1c-1 | Fact check S1 + F1 sample page | subagent FC-S1 |
| 1b-2 | Samples S2: `tours/life-of-a-request` + `request-stepper` visual, `reference/afd-config` + `tools/gen_afd_config.py` | subagent W-S2 |
| 1c-2 | Fact check S2 | subagent FC-S2 |
| 1d | Site check script; usage pause; the user can look at the samples | supervisor |

## 13. Full build (after Phase 1)

One subagent at a time. Pipeline per batch: writer → build → commit "(fact check pending)" → fact checker → commit "fact-checked".

| Batch | Pages | Visual |
|---|---|---|
| B1 Basics + boundary | learn/what-is-afd, learn/vllm-v1-map, concepts/plugin-entry-point, afd-config, worker-selection, model-registration, code/config-py, code/validation-py | – |
| B2 Roles, topology, connectors | concepts/roles, topology, control-plane, wire-data, code/connectors-core, code/p2p-py | topology-mapper |
| B3 Model split + execution | concepts/model-wrappers, moe-handoff, attention-runtime, ffn-runtime, code/attention-worker, code/ffn-worker, code/deepseek-v2-py | – |
| B4 Graphs, DBO, patches | concepts/cuda-graphs, dbo, compat-patches, reference/compat-patches, tours/start-up, tours/one-decode-step | dbo-timeline |
| B5 Deploy, NPU, reference | concepts/deployment-topologies, tuning, npu-overview, tours/run-a-recipe, reference/env-vars (+ generator), reference/recipes (+ generator), reference/faq | – |
| F Final | consistency pass (FINAL-PASS TODO), site check script, README | subagent + supervisor |

Subagent runs, estimate: Phase 1 = 5; full build = 10; final = 1. Total about 16, each followed by a usage pause.

## 14. Deferred pages

(none)
