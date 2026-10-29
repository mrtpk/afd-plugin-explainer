# AFD Plugin Explainer — Progress

Last update: 2026-10-29
Current phase: **DONE (2026-10-29).** All phases written, fact-checked, final-passed and committed. Not pushed or published (user instruction). Final checks: build --strict 0 warnings / 0 errors; 4 generator --checks up to date; site_check 42 pages x 1280/390, 3956 internal links, 0 problems; concepts = 19 pages (README:51 verified).

Final-commit contents (2026-10-29):
- F final-pass subagent (237k tokens, 77 tool calls): TODO a ("no real scheduler (a no-op stand-in)" on compat-patches x2, roles, ffn-runtime, start-up, code/ffn-worker, vllm-v1-map + diagrams b3_ffn_runtime, s2_request_ffn, b4_startup_ffn); b (glossary afd-forward-metadata had the wrong field list; supervisor confirmed metadata.py:294-304); g (deployment-topologies: clients send to the proxy 18305 in disaggregation; supervisor confirmed 2p1a1f_eager_dbo.sh:110-115); h (npu-overview cites point at class lines; supervisor spot-checked attention_worker.py:30, deepseek_v4.py:649). c, d, e, f checked: already correct. Consistency sweep clean; no facts.md errors; no suspected bugs. Supervisor read the full diff.
- notes/facts.md: new section "Added after the final pass" (AFDForwardContextMetadata fields; disaggregation client port).
- request-stepper CSS moved into assets/viz/viz.css (like the other two visuals); example_stepper.js deleted. Browser test of all 3 visuals (4 mounts) at 1280 and 390: click and keyboard change the aria-live text, all buttons >= 40 px, 0 overflow, 0 JS errors.
- Home legend: `.sm-around { margin-top }` also hit the legend swatch → scoped to `section.sm-around` (assets/site.css:678). Measured: all swatches centred at both widths.
- Diagrams: a measuring script (scratchpad final_check.js) found text on or past box borders in 9 diagrams. Fix in diagrams/svglib.py: new `_fit_rows` tightens the line step (box min 13, step card min 14) and moves the first line up when lines do not fit, and prints a stderr warning (= build warning) when they still do not fit. Hand fixes: b2_wire_data "split back" box (h 58), b4_dbo (lane moved down, ffn boxes wider, dashed return arrow starts at the box edge). Also from earlier this session: b5_npu_overview footer was past the canvas edge (shortened). Re-measured: 0 flags except b4_dbo, which was then fixed and looked at.
- README.md: status → complete; fact-check totals → about 960 claims / about 40 corrected + final pass; out-of-scope bin/ line corrected (the Python does not import bin/; it loads the setup.py-built _C_ascend). Page count 42 and the reduced-check list verified.

This file is the memory of the project. A new session must be able to continue from it alone.
Update it after every subagent finishes and after every user decision.

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 0a Survey | done | notes/survey/survey.md, vllm-plugin-hooks.md; 5 claims spot-checked by supervisor (all true) |
| 0b Plan approval | done | 2026-10-28: "defaults ok" |
| 1 Foundation + samples | done | 8 pages fact-checked; site check 0 problems (2026-10-28) |
| Full build (plan §13) | done | S1-S2, B1-B5 written, fact-checked, committed |
| F Final pass | done, committed | see top of file |

## Full build — batch status

| Batch | Writer | Fact check | Committed |
|---|---|---|---|
| F1 Foundation | done (186k tokens) | done in FC-S1 | yes |
| S1 Samples (home, learn/vllm-plugins, code/index, code/init-py) | done (239k tokens) | done (6 defects, 208k tokens) | yes |
| S2 Samples (tour life-of-a-request, reference/afd-config) | done (260k tokens) | done (6 defects) | yes |
| B1 Basics + boundary | done (280k) | done (6 defects, 215k) | yes |
| B2 Roles, topology, connectors | done (277k) | done (2 defects) | yes |
| B3 Model split + execution | done (260k) | done (2 defects, 252k) | yes |
| B4 Graphs, DBO, patches | done (306k) | done (7 defects) | yes |
| B5 Deploy, NPU, reference | done (367k) | done (~140 claims, 12 defects + supervisor diagram fixes, 227k) | yes |
| F Final | done (237k) + supervisor checks | (consistency pass) | yes |

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

- USER INSTRUCTION (2026-10-28): "i checked usage and it is at 13%. so I think it is safe do B4 and B5. what do you think" (13 % measured while the B3 writer ran) → supervisor agreed: no usage pauses through B5 fact-checked (FC-B3, B4, B5); one subagent at a time; commit per writer and per fact check; pause after B5 fact-checked before F unless the user also approves F. Projection ≈ 18-20 % at the end.

- USER INSTRUCTION (2026-10-28): "yes, I agree with yout recommendation" → run to the end with no usage pauses: FC-B3, B4, B5, F (consistency subagent), supervisor site check script, README, final commit. Stop early only for user decisions (suspected bug, safety stop, unfixable build) or a batch far over the expected cost. No push or publish.

## RESUME NOTES 2 (2026-10-29, second session) — RESOLVED

Resolved the same day: the user left auto mode and Bash worked again. Steps 1-3 below are DONE (see "Done"). Kept for the record.

**The second session ALSO lost Bash** (same safety classifier, right after the FC-B5 report arrived with an
"unreviewed" note). Read/Edit still work. START A NEW SESSION (or run outside auto mode).

State:
- Done and committed: B5 writer = `5552e37` "B5: ... (fact check pending)". Verified before commit: build
  --strict 42 pages / 54 terms / 30 diagrams / 0 warnings / 0 errors; 4 generator --check up to date;
  site_check 42 pages x 1280/390, 3956 links, 0 problems. README.md still uncommitted (final commit).
- FC-B5 FINISHED, edits ON DISK, NOT COMMITTED, NOT verified by the supervisor (`git diff` not run).
  Files it says it touched: src/concepts/npu-overview.html, deployment-topologies.html,
  src/tours/run-a-recipe.html, diagrams/b5_npu_overview.py, b5_deployment_topologies.py, b5_run_a_recipe.py
  (maybe tuning). It reports `build.py --preview` 0/0 and gen_env_vars / gen_recipes `--check` up to date.
- Supervisor spot-check with Read: camp2p.py:395-400 IS the init_afd_connector docstring; HCCL groups
  :418-431, FFN "afd_moe" group :443-454, Gloo "p2p" group :460-468, control_plane :385. Checker correct.

FC-B5 report summary (~140 claims; 12 edits: 7 citation, 1 logic, 4 wording/label):
1. npu-overview: CAMP2p HCCL/Gloo cite :395-400 → :418-431 / :460-468.
2. npu-overview: async FFN loop cite :441-443 → :442-446.
3. npu-overview: dp_metadata = None "each step" → "each work item" (async_ffn_model_runner.py:473 is inside the loop at :442).
4. deployment-topologies: DP4 derivation cites the DP flags (multipod_2a_2a_2f_graph.sh:33-34, :27-28, :70, :6-8). DP4 = DP2 local x 2 pods CONFIRMED.
5. deployment-topologies: "blocks differ by at most one" cite topology.py:118-146 → :107-115 (subgroup_attention_block).
6. "no scheduler" → "no real scheduler (a no-op stand-in)": tour stop 6, two diagram labels, two alt texts. FAQ was already right.
7. b5_npu_overview.py labels follow edits 1-2.
- All 8 B5 [W] facts CONFIRMED. gen_env_vars 51 vars correct (all profiler + setup.py rows checked). All 5 FAQ docs-vs-code items CONFIRMED. No suspected bugs.
- Sampled on env-vars / recipes: first screen, defaults, profiler + setup.py rows (README: list both as sample-checked).

Next session, in order:
1. `git diff` (only B5 files changed? ../afd-plugin and ../vllm clean at 7452d52 / ced6857a?), `python3 build.py --strict`, all four `--check`s, `node tools/site_check.js`.
2. Fold into notes/facts.md: mark the "Added after B5" [W] lines [FC] with these corrections: camp2p groups :418-431 / :443-454 / :460-468 (not :395-400); async loop :442-443 (not 441); dp_metadata=None per work item at :473 (not per step); ensure_cam_async_ops_available :108-120; env prepends ops.py:48, :51, AFD_CUST_OPAPI_LIB_PATH :54.
3. Commit "B5 fact-checked: 12 defects fixed" (author is repo-local; add the Co-Authored-By line).
4. Final pass and supervisor checks as in "Next step" below. Totals for README (FC-S1..FC-B5): ~960 claims, ~41 defects (S1 6, S2 6, B1 6, B2 2, B3 2, B4 7, B5 12).

FINAL-PASS TODO (from FC-B5):
- deployment-topologies "Start order and ports": 18303 is the disaggregation attention server port, but clients send to the proxy at 18305 (recipe/gpu/P2pNcclAFDConnector/deepseek_v2_lite/README.md:40-50). Add "(in disaggregation, clients send to the proxy)".
- npu-overview deep-dive tables cite NPU worker/wrapper files at :1-3 (SPDX header). Point at the class lines: AFDNPUAttentionWorker :30, AFDNPUAttentionModelRunnerV2 :208, AFDNPUFFNWorker :67, AFDNPUFFNModelRunner :56, AsyncNPUFFNModelRunner :73, AsyncFFNTwoStream :41, NPUUBatchRunner :67 (checker's lines; re-open each file).
- "no real scheduler (a no-op stand-in)" also on concepts/ffn-runtime, concepts/roles and any engine-core code page (B1-B4; already a TODO).

## RESUME NOTES

**2026-10-29. The supervisor session lost the Bash tool.** A safety classifier (not a tool error, not about
this project) blocked every Bash call for the rest of that conversation, including read-only ones. Read,
Write and Edit still worked, which is how these notes were written. START A NEW SESSION to continue.

State at that moment:
- Last commit: `ee31e83` "B4 fact-checked: 7 defects fixed". Everything up to and including B4 is committed.
- The B5 writer FINISHED and left its files on disk, UNCOMMITTED: 7 pages (concepts/deployment-topologies,
  tuning, npu-overview; tours/run-a-recipe; reference/env-vars, recipes, faq), diagrams/b5_*.py (4),
  src/glossary/b5.json (3 terms), tools/gen_env_vars.py, tools/gen_recipes.py.
- The B5 writer reported: `build.py --strict` = 42 pages, 54 glossary terms, 30 diagrams, 0 errors,
  0 warnings; both new generators' `--check` pass. The supervisor COULD NOT VERIFY this (Bash was blocked).
  Verify before you trust it.
- FC-B5 has NOT run. The final pass has NOT run. README.md is still the unfilled template.

First steps in the new session:
1. `python3 build.py --strict`; `--check` on all four generators (gen_afd_config, gen_env_vars, gen_recipes,
   gen_folder_tree); `node tools/site_check.js`.
2. Merge the B5 writer facts (below, marked [W]) into notes/facts.md, then commit B5 as
   "B5: ... (fact check pending)".
3. FC-B5, then the final pass (see "Next step").

## Done

- 2026-10-29: FC-B5 VERIFIED and committed ("B5 fact-checked: 12 defects fixed"). Supervisor read the full diff (only B5 files; ../afd-plugin 7452d52 and ../vllm ced6857a clean) and re-opened async_ffn_model_runner.py:442-446/:473, topology.py:107-115, camp2p.py:418-468, multipod script :27-34/:70: all correct. Supervisor fixes: restored "no client traffic" (checker had cut it to "no traffic") in b5_run_a_recipe; text touched box borders in b5_run_a_recipe (cards and boxes taller) and b5_deployment_topologies (Decode FFN box + panel 2); b5_tuning row label "recipe" overlapped its value (→ "ex"); b5_npu_overview said "prebuilt operators" for _C_ascend, which setup.py builds (→ "compiled Ascend extension"), and cited ops.py:72-94 (→ :73-91). facts.md B5 block → [FC] with line corrections. Build --strict 0/0, 4 generator --checks, site_check 42 pages 3956 links 0 problems.
- FINAL-PASS TODO (supervisor): other diagrams may have the same text-on-border problem; screenshot all 30 SVGs in the final check (tools/shot.js on site/diagrams/*.svg).
- 2026-10-29: NEW SESSION verified B5: `build.py --strict` 42 pages, 54 terms, 30 diagrams, 0 warnings, 0 errors; all four generator `--check` up to date; `node tools/site_check.js` 42 pages x 1280/390, 3956 internal links, 0 problems. B5 [W] facts were already merged in facts.md. Pins: ../vllm ced6857a, ../afd-plugin 7452d52. Committed B5 (fact check pending); README.md left uncommitted until the final commit.
- 2026-10-29: SUPERVISOR SESSION LOST BASH (safety classifier, not about this project). B5 writer output is
  on disk and uncommitted. See RESUME NOTES. progress.md was repaired with Read/Edit, which still worked.
- 2026-10-28: B5 writer done (367k tokens, last batch): concepts deployment-topologies, tuning,
  npu-overview; tours/run-a-recipe; reference/env-vars, recipes, faq; diagrams b5_* (4); b5.json
  (multipod, hccl, batch-size-factor); generators tools/gen_env_vars.py (51 variables) and
  tools/gen_recipes.py (24 AFD serve blocks), both with `--check` and `--report`. Writer reported
  `build.py --strict` 0 errors and 0 warnings (UNVERIFIED by the supervisor). No suspected bugs.
  The 4 B5 concept and tour pages ended the earlier "coming soon" warnings.
- FINAL-PASS TODO: FAQ "docs vs code" gained 3 more items from B5, all to verify in FC-B5:
  (a) recipe/gpu/P2pNcclAFDConnector/deepseek_v2_lite/README.md:111 says `bash tools/benchmarks/benchmark.sh`,
  which does not exist at the pin (the real harness is tools/benchmarks/request_generator.sh);
  (b) tools/benchmarks/decode_bench_server.sh:26-30 names two scripts that do not exist at the pin;
  (c) VLLM_TORCH_PROFILER_DIR is read by the plugin profilers (compat/profiler.py:132,
  compat/npu/profiler.py:149) but is not declared anywhere in vLLM v0.30.0, so it is read with plain
  os.getenv and unset only means the per-role default.
- 2026-10-28: FC-B4 done (full): ~210 claims, 7 defects (async_dp_engine selection :117-120 in 2 places; config_validation cite :200-214; "five patch modules imported by register_afd" → four + scoped gpu_mrv2_ubatching in diagram and alt; 3 off-by-one ranges). All 13 vLLM patch targets verified. No suspected bugs.
- FINAL-PASS TODO: "no scheduler" for the FFN EngineCore → "no real scheduler (a no-op stand-in)" on concepts/compat-patches step 4, reference/compat-patches __init__ row, concepts/roles (check), tours/life-of-a-request (check). Source: engine_core.py:599-623.
- 2026-10-28: B4 writer done: concepts cuda-graphs, dbo (+ dbo-timeline visual), compat-patches; reference/compat-patches; tours start-up, one-decode-step; 6 diagrams; b4.json (5 terms). Build 0 errors; site check 35 pages 0 problems; dbo-timeline tested on both pages (40 px, aria-live, 390). No suspected bugs.
- 2026-10-28: FC-B3 done: ~190 claims, 2 defects (sampling mechanism: native sample_tokens, not execute_model; Qwen3.5 registered class). Supervisor verified in vLLM and fixed the same claim on tours/life-of-a-request (stops 4, 12, quiz) and request-stepper.js stop 12. Lesson 12 sharpened. Sampled: code/attention-worker, code/ffn-worker, code/deepseek-v2-py. No suspected bugs.
- BUDGET NOTE: sample-checked (not full): code/attention-worker, code/ffn-worker, code/deepseek-v2-py (B3). List in README.
- FINAL-PASS TODO: check the AFDForwardContextMetadata fields behind glossary b3 "afd-forward-metadata" ("connector, transaction id, per-stage token counts").
- 2026-10-28: B3 writer done: concepts model-wrappers, moe-handoff, attention-runtime, ffn-runtime; code attention-worker, ffn-worker, deepseek-v2-py; 4 diagrams; b3.json (3 terms). Build 0 errors; site check 0 problems. No suspected bugs; no docs-vs-code differences in scope.
- 2026-10-28: FC-B2 done: ~70 claims, 2 citation defects (p2p-py lifecycle cite split; roles engine_core.py:605-606). Mapper re-derived for A = F, F+1, 2F, 2F+1 and A < F: all match the code. Sampled: code/connectors-core, code/p2p-py. No suspected bugs.
- BUDGET NOTE: sample-checked (not full): code/connectors-core, code/p2p-py (B2). List in README.
- FINAL-PASS TODO: concepts/model-wrappers (B3) must give the full construction branch set (deepseek_v2.py:493-517 incl. GateOnlyRemoteMoE :502 and dense MLP :509 for compute_gate_on_attention; FFN role :519-561) so it matches the simplified table on concepts/roles.
- FINAL-PASS TODO: concepts/npu-overview (B5) must own and cite the async CAM "receive loop drives the FFN side" mechanism that concepts/control-plane (step 6, quiz) states in one line.
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

In a NEW session (the old one lost Bash; see RESUME NOTES). The user approved running to the end with no
usage pauses and no push.

1. **Verify and commit B5.** Build `--strict`, all four generator `--check`s, `node tools/site_check.js`.
   Merge the B5 [W] facts into notes/facts.md. Commit "B5: ... (fact check pending)".
2. **FC-B5** (explainer-worker, notes/brief-factcheck.md). FULL check: concepts/deployment-topologies,
   tuning, npu-overview; tours/run-a-recipe; reference/faq; diagrams b5_*; src/glossary/b5.json.
   SAMPLE check (1 in 3 + every default, number, order): reference/env-vars and reference/recipes, plus a
   verification that each generator's output matches the source (run `--report`).
   FACT-CHECK FOCUS for FC-B5:
   - the Qwen 122B multipod page: the 4A2F rank counts are literal, but "DP4 = DP2 local x 2 pods" is the
     writer's interpretation of --data-parallel-size 4 / --data-parallel-size-local 2 /
     ATTENTION_DP_START_RANK=2. Re-derive it.
   - gen_env_vars completeness: 51 variables claimed. Spot-check the profiler and setup.py rows for a
     missed read or a false positive.
   - the async CAM layer index from token_nums_rankid_layeridx[2] (async_cam.py:497-556, :526-541).
   - camp2p.py:395-400 is cited from a docstring; move it to the HCCL/Gloo group-creation lines if better.
   - every FAQ answer, because the FAQ repeats facts from all earlier batches.
   Then commit "B5 fact-checked: N defects fixed".
3. **Final pass** (one explainer-worker, template E): clear every FINAL-PASS TODO line in this file, sweep
   all pages against notes/facts.md, re-run every generator with `--check`.
4. **Supervisor (not a subagent):** `node tools/site_check.js` over all 42 pages; test all three visuals
   (request-stepper, topology-mapper, dbo-timeline) with mouse and keyboard at 1280 and 390 px; mark this
   file done; final commit. Do NOT push or publish.
   README.md is ALREADY WRITTEN (2026-10-29, supervisor, no Bash needed). Before the final commit, check
   these three things in it, which were written from reports and not verified by a build:
   - the page count (42) and the part descriptions;
   - "about 1,000 claims examined, about 30 corrected" (add up the fact-check reports in this file);
   - the reduced-check list, against the BUDGET NOTE lines below, plus reference/env-vars and
     reference/recipes once FC-B5 confirms they were sample-checked.

## Questions for the user

(none open)

## Issues log

- 2026-10-28 (survey): design docs in `docs/design/module/` reference afd-plugin `36dadb4` (`index.md:38`); treat their line references as stale; cite code.
- 2026-10-28 (survey): `tools/proxy_server.py` is a prefill/decode proxy copied from vLLM-Ascend (`:1`), not part of the A/F split.
- DONE (supervisor, tooling): two-repo support in build.py (2026-10-28).
- FACT-CHECK FOCUS: worker selection only when `worker_cls == "auto"`; explicit wrong worker is rejected later (`validation.py:357-367`).
- FACT-CHECK FOCUS: "every connector has a control plane" is false (async CAM has none).
- FACT-CHECK FOCUS (FC-B4): attention_metadata.py:115-116, :252-257 and attention_model_runner_v2.py:153-157 reused from facts (re-open); config.py:303-308; reference/compat-patches config_validation row cites :62-89 for the backend relax (decision fn :200-214); async_dp_engine.py:248-252 and :389-401 (grep only).
- FACT-CHECK FOCUS (FC-B3): INFERRED 27 layers for DeepSeek-V2-Lite; deduction that on CUDA every MoE layer uses the remote-experts shell regardless of the gate flag (GateOnlyRemoteMoE only on NPU); sampling once per step via delegation to native execute_model.
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
| 2026-10-28 | explainer-worker: FC-B2 (full + sample for 2 module pages) | done; ~70 claims, 2 defects |
| 2026-10-28 | explainer-worker: B3 writer | done; 7 pages, 4 diagrams |
| 2026-10-28 | explainer-worker: FC-B3 (full + sample for 3 module pages) | done; ~190 claims, 2 defects |
| 2026-10-28 | explainer-worker: B4 writer | done; 6 pages, 6 diagrams, dbo-timeline, 306k |
| 2026-10-28 | explainer-worker: FC-B4 (full) | done; ~210 claims, 7 defects |
| 2026-10-28 | explainer-worker: B5 writer | done; 7 pages, 4 diagrams, 2 generators, 367k |
| 2026-10-29 | explainer-worker: no-tools re-test (new session) | PASS (site, folder, both repos read only, claude-opus-4-8) |
| 2026-10-29 | explainer-worker: FC-B5 (full + sample for env-vars, recipes) | done; ~140 claims, 12 edits, 227k tokens, 61 tool calls; report arrived with "safety review could not be evaluated" note; content read as a normal report |
| 2026-10-29 | explainer-worker: F final consistency pass (template E; TODOs a-h) | done; 237k tokens, 77 tool calls; a, b, g, h fixed; c-f already correct; no suspected bugs |
