# Writer brief (shared by every batch writer of "AFD Plugin Explained")

The supervisor's prompt gives you: the batch name, your pages and their scope, the visual (if any), and the
glossary terms you own. This file gives everything else. It is binding.

## Paths
- Explainer folder: /mnt/c/Users/tpesc/Downloads/test-harness/afd-plugin-explainer (git repo; do not commit: the supervisor commits).
- Target repo (READ ONLY, pinned): /mnt/c/Users/tpesc/Downloads/test-harness/afd-plugin at
  7452d52748fec2a858b63e4cb22941dadd7a3ee3. Never change it.
- Second repo (READ ONLY, pinned): /mnt/c/Users/tpesc/Downloads/test-harness/vllm at
  ced6857afa0ea7b2e3f0846a62e1394e90f15607 (vLLM v0.30.0). Never change it; never check out another commit.
  Cite it as {{cite vllm:path:line}} and <x-code repo="vllm" ...> (STYLE.md §5).
- Sibling site: none. Do not link to other explainer sites.

## Read first, in this order
1. STYLE.md (all of it).
2. plan.md §1-2 (goal and decisions) and §13 (your batch).
3. instructions-svg.md (STYLE.md §10 overrides it: canvas 1100, min text 11).
4. notes/facts.md: [FC] and [S] entries are verified; [W] entries are not. Still open the code and cite it yourself.
5. The model page of your page type (finished and fact-checked): concept src/concepts/connector-contract.html ·
   tour src/tours/life-of-a-request.html · module src/code/init-py.html · basics src/learn/vllm-plugins.html ·
   reference src/reference/afd-config.html (+ tools/gen_afd_config.py for generated tables) · visual assets/viz/request-stepper.js.
6. skills/codebase-explainer/references/writing-and-accuracy.md and page-templates.md.
7. notes/survey/*.md: a guide with file:line hints. NOT a source.

## Content rules
- Reader: knows Python and LLM-serving basics (prefill/decode, KV cache, batching, TP/PP/EP, MoE, CUDA
  graphs, vLLM as a server). Do NOT teach these; at most one line of recap where a page needs it. Start
  simple (one sentence, the idea, a diagram); then a full Deep dive (types and shapes, data layouts,
  algorithm steps, edge cases, env vars and flags, a worked example with real numbers, line-by-line reading).
- Every claim about the code: {{cite path:line}} or <x-code>. Open every cited line yourself. Narrowest range.
- No guesses. If the code does not answer a question, write it on the page as an open question and list it in your report.
- Scope: afd_plugin/, recipe/, docs/ (hints only), tools/. csrc/ is OUT of scope: explain only how the
  Python code selects, builds, loads and calls kernels and the prebuilt NPU binaries. Tests: source of facts
  only. NPU (Ascend): only the overview page concepts/npu-overview covers NPU code; other pages may name the NPU variant in one line with a citation.
- Design docs (docs/design/module/*.md) were written against an older commit (36dadb4). Write from the code.
  Report each docs-vs-code difference.
- <x-simplified> for simplifications. Site text in ASD-STE100 (STYLE.md §6). Captions start with "Figure: ".
- Diagrams: one script per diagram, Diagram(width=1100), max 3 boxes across, max 3 panels, no text below 11.
  Prefix = your batch (diagrams/<batch>_*.py).
- Literal tag syntax that is text ({{cite}}, <x-code>) must be escaped (&#123;&#123;cite&#125;&#125;).

## Accuracy lessons
(The supervisor adds each repeated defect type from the fact checks here.)
1. DEFAULTS: trace each default to where it is finally set (AFDConfig field → _normalize_mapping →
   validate_afd_config → recipe/CLI value; vLLM: arg_utils.py and config post-init). Do not cite only a field.
2. CONDITIONS: write "only when ..." where the code has a condition (example: the worker_cls rewrite runs only
   when worker_cls is "auto"; the async CAM connector has no control plane). No "always", "every", "all"
   unless you checked every path.
3. LINE RANGES: off-by-one is the most common defect. Open each cited range again after you finish the page.
4. COUNTS AND ORDER: "runs N times" or "before X" needs a check of every call site (example: vLLM calls
   load_general_plugins from 5 call sites).
5. DOCS: docs are often older than the code. Cite the code. Report each docs-vs-code difference (FAQ material).
6. PROCESSES: say which process runs a line (API server, EngineCore, worker; attention or FFN side). Check it.
7. FREQUENCY (after S1): say how often a call runs: once per step, once per layer, once per stage (ubatch).
   The control plane runs once per step before the layer loop; the data plane once per layer and stage. Do
   not fold a per-step call into a per-layer sequence.
8. DRIVERS, NOT DOCSTRINGS (after S1): an ABC docstring proves the contract, not the run-time order. Cite the
   concrete caller (model runner, server loop, model wrapper) for every "runs like this" sequence.
9. README vs. REGISTERED CODE (after S1): when the README names a family loosely (Qwen3.5/3.6), say exactly
   which architecture string the code registers.
10. GENERAL PYTHON (after S1): be precise about patches: from-imports bind the original object; a module
   attribute patch affects only later lookups.
11. SUBCLASS / REPLACE (after S2): cite the class line AND the construction branch that installs a stand-in.
   Name the class built on each role, and separate dense from MoE layers (dense mlp → RemoteFFNProxy; MoE →
   AFDDeepseekV2RemoteExpertsMoE shell with remote experts).
12. SAMPLING (after S2, B3): logits and sampling run once per step, every step, attention side, in the native
   sample_tokens call (vllm:vllm/v1/worker/gpu/model_runner.py:2048-2050), NOT inside execute_model.
13. NATIVE vLLM SEQUENCES (after S2): cite the narrowest line (vllm:vllm/v1/engine/core.py:600-601), never a bare file.
14. DEVICE SCOPE (after S2): say when a key or patch is GPU-only or NPU-only and when it takes effect (async_dp:
   NPU only, gated at run time, false on GPU).
15. ENV DEFAULTS (after B1): "env unset" is not "feature off". Trace the getter (VLLM_USE_V2_MODEL_RUNNER unset →
   vLLM picks V2 by default, vllm:vllm/config/vllm.py:675-722). State the feature state; cite the env read apart.
16. LINE COUNTS (after B1): "at a glance" file line counts must equal `wc -l` (four were off by one in B1).
17. GUARD WORDING (after B1): say exactly what a guard protects (a hasattr guard that saves the original once
   is not a re-patch guard).

## Ownership
- You own only: your page files, src/glossary/<batch>.json, diagrams/<batch>_*.py, and your visual
  assets/viz/<name>.js (shared visual styles only appended to assets/viz/viz.css).
- Search src/glossary/*.json before you add a term. Do not redefine; reuse with {{term id}}.
- Do NOT edit: build.py, assets/site.css, assets/site.js, nav files, other glossary files, notes/*,
  STYLE.md, plan.md, progress.md, other pages, explainer.json.
- Use `python3 build.py --preview` when another page is broken. Your pages must have 0 errors and no
  template or language warnings.

## No subagents
Do NOT start subagents or forks. The user allows 2 running agents and the supervisor runs one at a time; you
are that one. Do all the work yourself.

## Claims that the code has a bug
Do NOT write "bug", "vulnerability" or "this looks wrong" on a page. Pages say what the code does, in neutral
words. Re-read the control flow twice (is the line inside or after the loop or if? check the caller and the
callee) and report it to the supervisor with exact lines.

## Report (final message only, no report files)
1. Pages written, diagrams, visual, glossary ids added.
2. Build result (errors and warnings for your pages).
3. NEW FACTS for notes/facts.md (each with file:line).
4. FACTS IN facts.md THAT ARE WRONG (with proof).
5. Claims you are less sure of (for the fact checker to check hard).
6. Open questions, docs-vs-code differences, cross-page problems, suspected bugs (exact lines).
