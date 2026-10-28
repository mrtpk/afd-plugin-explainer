# AFD Plugin Explainer — Progress

Last update: 2026-10-28
Current phase: **1b Samples** — F1 done and committed (fact check pending, part of FC-S1); usage pause; next: writer W-S1.

This file is the memory of the project. A new session must be able to continue from it alone.
Update it after every subagent finishes and after every user decision.

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 0a Survey | done | notes/survey/survey.md, vllm-plugin-hooks.md; 5 claims spot-checked by supervisor (all true) |
| 0b Plan approval | done | 2026-10-28: "defaults ok" |
| 1 Foundation + samples | running | 1a-0 done (kit, git, explainer.json, two-repo build.py) |
| Full build (plan §13) | not started | |
| F Final pass | not started | |

## Full build — batch status

| Batch | Writer | Fact check | Committed |
|---|---|---|---|
| F1 Foundation | done (186k tokens) | in FC-S1 | yes (pending) |
| S1 Samples (home, learn/vllm-plugins, code/index, code/init-py) | – | – | – |
| S2 Samples (tour life-of-a-request, reference/afd-config) | – | – | – |
| B1 Basics + boundary | – | – | – |
| B2 Roles, topology, connectors | – | – | – |
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

## RESUME NOTES

(none)

## Done

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

Usage pause after F1. Then writer W-S1 (plan §12 1b-1): home page (system map, Start here, `#code-version` with both commits), learn/vllm-plugins, code/index text (tree exists), code/init-py; copy the model page concepts/connector-contract. Then build, commit "S1 (fact check pending)", pause, then FC-S1 (also checks concepts/connector-contract, core.json, code/index descriptions).

## Questions for the user

- 2026-10-28: install Chromium system libraries for the site check (needs sudo).

## Issues log

- 2026-10-28 (survey): design docs in `docs/design/module/` reference afd-plugin `36dadb4` (`index.md:38`); treat their line references as stale; cite code.
- 2026-10-28 (survey): `tools/proxy_server.py` is a prefill/decode proxy copied from vLLM-Ascend (`:1`), not part of the A/F split.
- DONE (supervisor, tooling): two-repo support in build.py (2026-10-28).
- FACT-CHECK FOCUS: worker selection only when `worker_cls == "auto"`; explicit wrong worker is rejected later (`validation.py:357-367`).
- FACT-CHECK FOCUS: "every connector has a control plane" is false (async CAM has none).
- FACT-CHECK FOCUS (FC-S1, connector-contract): INFERRED DeepSeek-V2-Lite hidden_size 2048/bf16 and the 32,768-byte figure; "each FFN rank owns one attention peer" for 2A2F (check build_rank_mapping, topology.py:118); the call order in the "full call order" deep dive (writer did not read the runner loops).
- FACT-CHECK FOCUS: vLLM plugin load moments (5 call sites); which process runs each.

## Subagent log

| Date | Task | Result |
|---|---|---|
| 2026-10-28 | explainer-worker: no-tools config test | model accepted; stale definition loaded (needs session restart) |
| 2026-10-28 | explainer-worker: survey (template A) | done, 238k tokens, 62 tool calls; notes/survey/*.md |
| 2026-10-28 | explainer-worker: no-tools re-test (new session) | PASS, 28k tokens |
| 2026-10-28 | explainer-worker: F1 foundation (template B) | done, 186k tokens, 83 tool calls; 0 errors |
