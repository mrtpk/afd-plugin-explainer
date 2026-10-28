# AFD Plugin Explainer — Progress

Last update: 2026-10-28
Current phase: **2 Full build** — Phase 1 done (8 sample pages fact-checked, site check clean); usage pause; next: B1 writer.

This file is the memory of the project. A new session must be able to continue from it alone.
Update it after every subagent finishes and after every user decision.

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 0a Survey | done | notes/survey/survey.md, vllm-plugin-hooks.md; 5 claims spot-checked by supervisor (all true) |
| 0b Plan approval | done | 2026-10-28: "defaults ok" |
| 1 Foundation + samples | done | 8 pages fact-checked; site check 0 problems (2026-10-28) |
| Full build (plan §13) | next | B1 first |
| F Final pass | not started | |

## Full build — batch status

| Batch | Writer | Fact check | Committed |
|---|---|---|---|
| F1 Foundation | done (186k tokens) | done in FC-S1 | yes |
| S1 Samples (home, learn/vllm-plugins, code/index, code/init-py) | done (239k tokens) | done (6 defects, 208k tokens) | yes |
| S2 Samples (tour life-of-a-request, reference/afd-config) | done (260k tokens) | done (6 defects) | yes |
| B1 Basics + boundary | done (280k) | done (6 defects, 215k) | yes |
| B2 Roles, topology, connectors | done (277k) | running | yes (pending) |
| B3 Model split + execution | – | – | – |
| B4 Graphs, DBO, patches | – | – | – |
| B5 Deploy, NPU, reference | – | – | – |
| F Final | – | – | – |

## USER INSTRUCTIONS

- USER INSTRUCTION (2026-10-28): "../afd-plugin (READ ONLY; never edit it, and never edit ../vllm)". Later: "use vllm commit that is tagged in afd plugin. You are free to change the commit" → supervisor checked out `ced6857a` in ../vllm (was `main` at `fd3469f4`, no tracked changes; `git -C ../vllm checkout main` restores it). No other change to ../vllm.
- USER INSTRUCTION (2026-10-28): "At most 2 subagents at a time. Subagents never start subagents (put this in both briefs)."
- USER INSTRUCTION (2026-10-28): "Stay under 50% of my weekly limit. You cannot read the meter, so run one subagent at a time and pause after each one for me to check /usage, unless I say otherwise."
- USER INSTRUCTION (2026-10-28): "Run the final site check as your own script, not a subagent."
- USER INSTRUCTION (2026-10-28): "Test it with one reply that uses no tools before real work. If it fails, ask me before you use another model."
- USER INSTRUCTION (2026-10-28): "Pages state what the code does in neutral words. No 'bug' or 'vulnerability' claims on pages; report suspected bugs to me."
- USER INSTRUCTION (2026-10-28): "Git: commit per stage (writer commit 'fact check pending', then 'fact-checked'), author Thomas Paul <contact@thomaspaul.dev> set repo-local. Push or publish only when I ask."
- USER INSTRUCTION (2026-10-28): "Do not build before I approve the plan. After the approval you may run unattended to the end, except for the usage pauses above."

- USER INFO (2026-10-28): "for now we have used about 10% of my weekly quota. The quota will be reset on 3rd nov" (measured after Phase 1, B1 writer running). Supervisor projection: Phase 1 ≈ 10 %; remaining B1-B5 + F ≈ 2.5-3 × Phase 1 → ≈ 35-40 % total, under the 50 % ceiling. Ceiling still applies; pauses unchanged unless the user says otherwise.

- USER INSTRUCTION (2026-10-28): "so, I think we can run B2, and B3 without my usage checking right?" → supervisor: no usage pauses from now through B3 fact-checked (incl. FC-B1); still one subagent at a time and a commit per writer and per fact check; pause after B3 fact-checked (before B4). Stop early if a batch costs much more than expected or a user decision is needed.

## RESUME NOTES

(none)

## Done

- 2026-10-28: B2 writer done: concepts roles, topology (+ topology-mapper visual, CSS in viz.css), control-plane, wire-data; code/connectors-core, code/p2p-py; 4 diagrams; b2.json (afd-world). Build 0 errors; site check 22 pages 0 problems; mapper tested (click, 40 px, aria-live, 390 px). Supervisor added core.json term `step`. No suspected bugs.
- 2026-10-28: FC-B1 done: ~120 claims; 6 defects (4 line counts; "VLLM_USE_V2_MODEL_RUNNER set/not set" → "V2 runner on/off" in 6 places; patch-guard wording). Sampled: code/config-py, code/validation-py (sections listed in the FC report: first screen, key tables, every default/number/order, ~1 in 3 prose). Supervisor verified the V2 default in vLLM (config/vllm.py:675-722), fixed core.json model-runner-v2 term and a weak citation on plugin-entry-point (line 89: cite two call sites instead of the func() loop). Lessons 15-17 added. No suspected bugs.
- FINAL-PASS TODO: FAQ "docs vs code": README.md:204 says both roles require VLLM_USE_V2_MODEL_RUNNER=1; vLLM picks V2 by default when unset (vllm:vllm/config/vllm.py:692-694 + :695-722). Also any later page that says "set/not set" for V2 on/off.
- BUDGET NOTE: sample-checked (not full): code/config-py, code/validation-py (B1). List in README.
- 2026-10-28: B1 writer done: 8 pages, 6 diagrams b1_*, b1.json (2 terms). Build 0 errors; site check 0 problems. Facts merged [W]. No suspected bugs.
- 2026-10-28: Phase 1d: supervisor site check `node tools/site_check.js` (all pages × 1280/390, deep dives open, links + anchors, JS errors, images): 8 pages, 417 internal links, 0 problems.
- 2026-10-28: FC-S2 done (full): ~110 claims, 6 defects (stop 7 subclass/replace citations + dense vs MoE wording; stop 2 narrow vLLM cites; sampling "once per step" in loop table and diagram; async_dp where-read row). Generator output fully correct. No suspected bugs. Lessons 11-14 added to brief-writer; model-page line filled in.
- FINAL-PASS TODO: "sampling once per step after the last layer" on concepts/attention-runtime, concepts/ffn-runtime, tours/one-decode-step; dense-proxy vs MoE-shell wording on concepts/model-wrappers, concepts/moe-handoff; async_dp NPU-only, run-time gated on concepts/afd-config, concepts/compat-patches (source: facts.md "Added after the S2 fact check").
- 2026-10-28: W-S2 done: tours/life-of-a-request (12 stops, 2 diagrams, request-stepper visual), reference/afd-config (generated tables + hand tables, worked example from 2a2f_eager_dbo_dp1tp2.sh), tools/gen_afd_config.py (ast, --check green), diagrams s2_*, s2.json (4 terms). Supervisor browser test: stepper works with click and keyboard at 1280 and 390, buttons >= 40 px, aria-live updates, 0 JS errors, 0 overflow; afd-config page 0 overflow. No suspected bugs. Observation: async connector accepts camelCase key `dynamicQuant` (async_cam.py ~:83, :183) → FAQ.
- FINAL-PASS TODO (supervisor): request-stepper.js injects its CSS with a <style> element; move to assets/viz/viz.css for consistency (optional). Delete unused assets/viz/example_stepper.js.
- 2026-10-28: FC-S1 done (full): ~120 claims, 6 defects fixed (call order: control plane once per step, not per layer; Qwen table; monkey-patch precision; UniProc simplification note; topology citation; diagram label). Writer notes #1, #2, #4, #6 confirmed. Supervisor fixed: tools/gen_folder_tree.py binary detection (whole-file NUL scan; repo total 164,972 → 139,046 lines; connectors/ 30,259 → 4,333); core.json full-decode-only (GPU: cuda_graph.py:20-21; NPU accepts FULL too). Accuracy lessons 7-10 added to notes/brief-writer.md. Facts merged.
- IDEA (skill): the kit's templates/tools/gen_folder_tree.py has the same first-4-KB binary sniff; tell the user (not changed: skill files are out of scope).
- FINAL-PASS TODO: concepts/control-plane, concepts/wire-data, tours/one-decode-step, tours/life-of-a-request must say control plane once per step, data plane once per layer and stage (source: facts.md "Added after the S1 fact check").
- 2026-10-28: W-S1 done: home (system map, start here, both commits), learn/vllm-plugins, code/index hand parts, code/init-py; diagrams s1_plugin_processes, s1_register_afd_order; s1.json (2 terms); CSS block `/* Home: system map (S1) */`. Build 0 errors. Screenshots 1280/390: 0 overflow, 0 JS errors on all 4 pages. Facts merged [W]. plan.md §3 corrected (78 .py files). No suspected bugs.
- FINAL-PASS TODO (supervisor CSS): home legend: the "around every step" swatch sits below the text line (assets/site.css S1 block).
- 2026-10-28: User installed Chromium system libraries (`sudo npx -y playwright@1.56.1 install-deps chromium`). Browser check works: `node tools/shot.js <file-url> <out.png> <width> <height>` (uses cached playwright-core 1.56.1 + chromium-1234). connector-contract: 0 overflow, 0 JS errors at 1280 and 390. Look OK. Diagram nit: "control plane" label touches its dashed arrow (FC-S1 may fix).
- 2026-10-28: DECISION: W-S1 may append one block `/* Home: system map (S1) */` to assets/site.css (only writer running; no clash).
- 2026-10-28: F1 done: STYLE.md adapted (§5.0 vllm: prefix, vocabulary, out-of-scope), nav with 41 pages (7 concept groups), core.json 33 terms, home stub, concepts/connector-contract + diagrams/f1_connector_contract.py, folder descriptions in tools/gen_folder_tree.py; example pages deleted. Build 0 errors, 7 expected warnings. Facts merged into notes/facts.md as [W]. Supervisor checked the reported suspected bug: gpu/p2p.py:196 stores a 1-element tuple, but nothing reads the attribute and a unit test asserts (40,) → observation for the user, not on pages.
- 2026-10-28: TOOLING: browser check: node 20 + cached playwright-core 1.56.1 (~/.npm/_npx/d537ee5ee2a13f03) + ~/.cache/ms-playwright/chromium-1234 exist, but Chromium fails: missing libnspr4.so (system libs). Needs `sudo` (user). Screenshot script: scratchpad shot.js (executablePath = chromium-1234/chrome-linux64/chrome).
- 2026-10-28: Phase 1a-0 (supervisor): starter kit copied (cp -n; plan/progress/briefs kept), git init (main), author Thomas Paul <contact@thomaspaul.dev> repo-local, `site/` in .gitignore, explainer.json filled (afd-plugin 7452d52 + extra_repos.vllm ced6857a). build.py: `extra_repos` support: `{{cite vllm:path:line}}`, `<x-code repo="vllm">`, commit check for every repo, `{{project vllm_sha}}` etc., both commits in version line, footer and `<x-version />`. Tested: vLLM links, out-of-range vLLM line = error, wrong vLLM pin = error. Example pages build with 0 errors.
- 2026-10-28: New session (user exited and resumed). No-tools re-test: agent reports "AFD Plugin Explained", the right folder, both repos read only, model claude-opus-4-8. PASS.
- 2026-10-28: USER DECISION: "defaults ok" → plan approved (plan.md §11). NPU = one overview page; budget mode all items; claude-opus-4-8 high; no separate Phase 1 stop; site/ not committed.
- 2026-10-28: Survey subagent (explainer-worker, stale definition + explicit override prompt; read-only) wrote notes/survey/. Supervisor spot-checked 5 claims: DeepseekV4 NPU/GPU wrapper choice (`__init__.py:109-113`), async CAM `control_plane = None` (`async_cam.py:283`), worker_cls rewrite only when auto (`config_validation.py:60,92-93,179-197`), vLLM `load_general_plugins` guard + 5 call sites, deepcopy identity comment (`model_utils.py:38-45`). All true.
- 2026-10-28: USER DECISION: "continue" → survey ran with the stale agent definition and explicit paths; restart before any writer.
- 2026-10-28: Agent definition `.claude/agents/explainer-worker.md` adapted (site name, folder, both repos read only). No-tools test: model `claude-opus-4-8` accepted, but the session still has the OLD definition (vLLM Explained paths). It loads at session start only.
- 2026-10-28: ../vllm checked out at `ced6857a` (v0.30.0) with user permission.

## Next step

FC-B2 RUNNING (no pause, user instruction). If cut off: resume it, do not restart. B1 writer (plan §13: learn/what-is-afd, learn/vllm-v1-map, concepts/plugin-entry-point, afd-config, worker-selection, model-registration, code/config-py, code/validation-py; no visual) → build → commit "B1 (fact check pending)" → FC-B1 (no pause, user instruction) (full for learn + concepts; sample 1 in 3 for code/config-py and code/validation-py) → commit "B1 fact-checked" → B2 → B3 with no pauses → PAUSE after B3 fact-checked. Then B4, B5 with pauses, then F.

## Questions for the user

(none open)

## Issues log

- 2026-10-28 (survey): design docs in `docs/design/module/` reference afd-plugin `36dadb4` (`index.md:38`); treat their line references as stale; cite code.
- 2026-10-28 (survey): `tools/proxy_server.py` is a prefill/decode proxy copied from vLLM-Ascend (`:1`), not part of the A/F split.
- DONE (supervisor, tooling): two-repo support in build.py (2026-10-28).
- FACT-CHECK FOCUS: worker selection only when `worker_cls == "auto"`; explicit wrong worker is rejected later (`validation.py:357-367`).
- FACT-CHECK FOCUS: "every connector has a control plane" is false (async CAM has none).
- FACT-CHECK FOCUS (FC-B2): 4A2F/3A2F derivations (pages + topology-mapper.js) from topology.py:136, :164-170; min_size == F under A >= F and control group = FFN ranks + first F attention ranks (topology.py:42-43, p2p.py:310); recv src → attention role rank f (p2p.py:902); INFERRED 32,768-byte figure.
- FACT-CHECK FOCUS (FC-B1): vllm-v1-map first box "API server process (AsyncLLM)" wording; "patches do not install on a non-matching vLLM, so AFD does not activate" (check all 4 patch gates); config_validation.py:235-248 "guard against re-patching" wording; async_dp cannot be active on GPU (validation.py:93-97 + config.py:331-334).
- FACT-CHECK FOCUS (FC-S2): tour stop 7 wording (wrapper subclasses native model; where the proxy replaces the MLP: deepseek_v2.py ~:375, ~:725); stop 2 cites a whole vLLM file with no line; async_dp "where read" (config.py:303-308 vs compat/npu/runtime.py:51-55); compute_gate_on_attention → FFN runs expert layers only (ffn_model_runner.py ~:211-215).
- FACT-CHECK FOCUS (FC-S1, learn/vllm-plugins): process of arg_utils.py:839 (EngineArgs.__post_init__) — is EngineArgs also built in EngineCore?; the "plugin cannot change already-imported references" claim (general Python, no citation); diagram s1_plugin_processes "spawns" simplification; home fact table "Qwen3.6" (README only).
- FACT-CHECK FOCUS (FC-S1, connector-contract): INFERRED DeepSeek-V2-Lite hidden_size 2048/bf16 and the 32,768-byte figure; "each FFN rank owns one attention peer" for 2A2F (check build_rank_mapping, topology.py:118); the call order in the "full call order" deep dive (writer did not read the runner loops).
- FACT-CHECK FOCUS: vLLM plugin load moments (5 call sites); which process runs each.

## Subagent log

| Date | Task | Result |
|---|---|---|
| 2026-10-28 | explainer-worker: no-tools config test | model accepted; stale definition loaded (needs session restart) |
| 2026-10-28 | explainer-worker: survey (template A) | done, 238k tokens, 62 tool calls; notes/survey/*.md |
| 2026-10-28 | explainer-worker: no-tools re-test (new session) | PASS, 28k tokens |
| 2026-10-28 | explainer-worker: F1 foundation (template B) | done, 186k tokens, 83 tool calls; 0 errors |
| 2026-10-28 | explainer-worker: W-S1 writer | done, 239k tokens, 73 tool calls; 0 errors, 44 expected link warnings |
| 2026-10-28 | explainer-worker: FC-S1 fact check (full) | done, 208k tokens, 73 tool calls; ~120 claims, 6 defects |
| 2026-10-28 | explainer-worker: W-S2 writer | done, 260k tokens, 76 tool calls; 0 errors |
| 2026-10-28 | explainer-worker: FC-S2 fact check (full) | done; ~110 claims, 6 defects |
| 2026-10-28 | explainer-worker: B1 writer | done; 8 pages, 6 diagrams, 0 errors |
| 2026-10-28 | explainer-worker: FC-B1 (full + sample for 2 module pages) | done; ~120 claims, 6 defects, 215k tokens |
| 2026-10-28 | explainer-worker: B2 writer | done; 6 pages, 4 diagrams, topology-mapper, 277k |
| 2026-10-28 | explainer-worker: FC-B2 | running |
