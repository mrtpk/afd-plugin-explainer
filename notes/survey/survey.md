# AFD Plugin — Codebase Survey

Target repo: `/mnt/c/Users/tpesc/Downloads/test-harness/afd-plugin` @ `7452d52748fec2a858b63e4cb22941dadd7a3ee3`
(github.com/vllm-project/afd-plugin). vLLM: `/mnt/c/Users/tpesc/Downloads/test-harness/vllm` @ `ced6857a` (v0.30.0).

Conventions: every claim carries `path:line`; vLLM paths prefixed `vllm:`. "not checked" means I did not open the file.
`csrc/` kernel internals are out of scope by instruction — only Python-side selection/build/load/call is reported.
Companion file: `vllm-plugin-hooks.md` (section 4 detail).

---

## 1. Size

Totals (tracked files, `git ls-files`): 595 files. By extension (top):
`.py` 238, `.md` 97, `.h` 82, `.cpp` 43, `.hpp` 40, `.sh` 33, `.yaml` 17, `.yml` 13, `.png` 6, plus 1 `.whl` and 1 `.run` (vendored NPU binaries), 1 `.jsonl` (benchmark dataset), `uv.lock` (1.1 MB).

Lines per language/area:
- `afd_plugin/` Python: **20,195** lines across 82 files (`find afd_plugin -name '*.py' | xargs wc -l` → 20195 total).
- `csrc/` C/C++: 165 files (`.cpp/.h/.hpp`), **45,616** lines — OUT OF SCOPE (kernels).
- `tests/` Python: **40,925** lines (149 files) — facts only.
- `docs/` Markdown: **4,733** lines (21 files).
- `tools/` Python: **2,089** lines; `tools/proxy_server.py` alone is **1,351** lines.
- `recipe/`: 15 `.sh` scripts + READMEs/PNGs (24 files).

Top-level folder map (one line each):
- `afd_plugin/` — the plugin package: config, workers, runners, connectors, model wrappers, compat shims (82 files).
- `csrc/` — native CANN/ACLNN (`npu/`) and reserved `gpu/` kernels; 179 files (OUT OF SCOPE).
- `docs/` — design modules (`design/module/*.md`), gpu/npu user guides, assets (logo + architecture SVG + 2 PNGs).
- `recipe/` — deployment+benchmark launch scripts, by hardware/connector/model.
- `tests/` — unit + hardware-gated e2e (149 files); source of facts only.
- `tools/` — `proxy_server.py`, benchmarks, datasets, pre-commit helpers.
- `docker/` — 1 file; `.buildkite/`, `.github/` — CI; `.agents/` — 95 files of agent skills (see §11); `.claude/` — 1 file.
- Root: `README.md`, `pyproject.toml`, `setup.py`, `AGENTS.md`, `CLAUDE.md`, `uv.lock`, `MANIFEST.in`, `LICENSE`.

`afd_plugin/` GPU vs NPU vs shared (line counts, by path heuristic — a file is "NPU" if under any `/npu/` dir or `compat/npu`, "GPU" if under `/gpu/` or `gpu_mrv2_*`, else "shared"):
- **NPU-specific: ~9,329 lines** (`compat/npu/*`, `compat/patches/npu/*`, `connectors/npu/*`, `model_executor/models/npu/*`, `model_executor/npu/*`, `v1/worker/npu/*`, `async_cam_startup.py` counts as shared but is async-CAM only).
- **GPU-specific: ~1,414 lines** (`connectors/gpu/p2p.py` 1125, `connectors/gpu/__init__.py` 7, `compat/patches/gpu_mrv2_ubatching.py` 282).
- **Shared: ~9,452 lines** (config/validation/metadata/topology/base-connector/CUDA-graph policy/dbo, the GPU-oriented but "shared"-pathed attention/ffn runners, DeepSeek/Qwen model wrappers, compat vllm/engine_core/async_dp patches).

Caveat: the "shared" bucket includes `v1/worker/attention_model_runner_v2.py` (622), `v1/worker/ffn_model_runner.py` (483) and the DeepSeek/Qwen wrappers; these are effectively CUDA runtime though not under `/gpu/`. The NPU bucket is the single largest concentration of code. (heuristic script run this session.)

---

## 2. What AFD is; what it runs on

AFD = **Attention-FFN Disaggregation**: a vLLM external plugin that splits a model's per-layer execution so the Attention sublayer runs on one set of workers ("attention" role) and the FFN/MoE sublayer runs on a different set ("ffn" role), exchanging hidden states over a connector (`README.md:9-15`, `:11-15`). It provides plugin-owned worker classes, model runners, model wrappers, connectors, config validation, compat shims, hardware-gated tests (`README.md:12-15`). Experimental (`README.md:17-19`).

Target runtime: **vLLM `v0.30.0` @ `ced6857a`**; Ascend integration targets vLLM-Ascend `8d4409d6` (`README.md:21-25`). Does not modify vLLM source; installed via the `vllm.general_plugins` entry point + `--additional-config` + auto-selected role workers + plugin model wrappers + version-scoped shims (`README.md:22-25`).

Runs on: **CUDA GPU** and **Ascend NPU** (`README.md:14-15`, `:36-37`). Models (`README.md:47-51`):
- DeepSeekV2 / V3 / V3.2 → wrappers `AFDDeepseek{,V2,V3}ForCausalLM`; V3.2 reuses V3 wrapper.
- Qwen3 MoE → `AFDQwen3MoeForCausalLM` (CUDA, `compute_gate_on_attention=false`).
- Qwen3.5/3.6 MoE → `AFDQwen3_5MoeForConditionalGeneration` (CUDA text-only).
Connectors (`README.md:57-61`): `P2pNcclAFDConnector` (CUDA, sync, decode), `CAMP2pAFDConnector` (NPU, sync), `CAMAsyncAFDConnector` (NPU, async prefill/decode).
Both roles require `VLLM_USE_V2_MODEL_RUNNER=1`; Attention uses native ModelRunnerV2, FFN stays connector-driven; no V1 fallback (`README.md:204-210`, `:76-78`).

---

## 3. vLLM integration surface

**Entry point.** `pyproject.toml:45-46`: `[project.entry-points."vllm.general_plugins"] afd = "afd_plugin:register_afd"`. Dist name `vllm-afd-plugin`, import name `afd_plugin` (`pyproject.toml:12`, `README.md:194-195`). vLLM pinned as optional extra `vllm==0.30.0` (`pyproject.toml:36-37`).

`register_afd()` (`afd_plugin/__init__.py:142-216`), guarded once-per-process by `_registered` (`:48`, `:150-153`, `:216`). Steps: version check `assert_vllm_version_supported(strict=False)` (`:163-165`); import-apply 4 GPU/engine patches (`async_dp_engine`, `async_dp_forward_context`, `config_validation`, `engine_core`) (`:172-181`); register the `afd_balanced` routing strategy (`:183-187`); register the `manual_dbo_yield` custom op (`:189-197`); if platform is NPU apply the Ascend config patch (`:202-209`); register AFD model wrappers into `vllm.model_executor.models.ModelRegistry` with an `AFD`-prefixed arch name (`:211-214`). It is import-safe without vLLM (`:157-160`). Model registration table at `:96-139`. Also a multiprocessing spawn override, opt-in via `AFD_FORCE_SPAWN_MULTIPROCESSING=1`, applied at import time (`:51-94`).

**`--additional-config` parsing.**
- `afd_plugin/config.py`: `AFDConfig` dataclass (frozen) `:41-117` with fields `connector, async_dp, role, port(1239), host(127.0.0.1), num_attention_ranks(1), num_ffn_ranks(1), compute_gate_on_attention(False), afd_process_group_timeout_s(120), connector_extra_config({})`. Aliases `afd_connector/afd_role/afd_port/afd_host/async` → canonical (`:32-38`). `_normalize_mapping` rejects unknown keys, coerces types (`:120-176`). `parse_afd_config`/`parse_optional_afd_config` read `additional_config["afd"]` (`:244-279`); AFD is active iff the key is present and passes validation (`:289-292`). `is_afd_async_dp` selects async patches (`:295-308`). `validate_afd_config` (`:311-351`) enforces role∈{attention,ffn}, connector∈ the 3, async⇒async connector, P2P topology, host/port/rank bounds.
- `afd_plugin/config_utils.py:8-66` — `coerce_extra_{bool,str,int,positive_int}` + optional variant.
- `afd_plugin/validation.py` — runtime wiring validators: `validate_gpu_model_runner_v2_config` (`:76-143`) and `validate_npu_model_runner_v2_config` (`:146-239`) enforce V2 runner, connector/device match, no PP/CP, ranks == DP*TP, static EP, 2-ubatch DBO, registered AFD model, graph-mode constraints. `assert_compatible_afd_stack` (`:312-369`) verifies `worker_cls` matches the role's expected FQCN. Worker/runner FQCNs are `Final` constants `:26-41`.

**Role worker registration/selection.** Not registered as classes; selected by **rewriting `worker_cls`**. `afd_plugin/compat/patches/config_validation.py:179-197` (`_select_afd_worker_for_auto`) runs inside the patched `EngineArgs.create_engine_config` (`:51-113`) only when `--worker-cls` was left `"auto"` (`:60`, `:92-93`); it calls `afd_worker_qualname_for_platform_default` (`validation.py:280-309`) which maps the platform default worker (`vllm.v1.worker.gpu_worker.Worker` or `vllm_ascend.worker.worker.NPUWorker`) to the AFD worker FQCN for the role. Explicit `--worker-cls` is still accepted (`README.md:200-202`). The actual worker classes: GPU `AFDAttentionWorker`/`AFDFFNWorker` (`v1/worker/attention_worker.py:22`, `ffn_worker.py:32`), NPU `AFDNPUAttentionWorker`/`AFDNPUFFNWorker` (`v1/worker/npu/__init__.py:7-15`). Lazy export maps at `v1/worker/__init__.py:7-12` and `v1/worker/npu/__init__.py:7-15`.

**Model runners.** GPU Attention: `AFDAttentionModelRunnerV2(AFDMetadataProviderMixin, GPUModelRunnerV2)` (`attention_model_runner_v2.py:358`). GPU FFN: `GPUFFNModelRunner` (standalone, connector-driven) (`ffn_model_runner.py:52`). Worker swaps the native `GPUModelRunner` module symbol during `init_device` (`attention_worker.py:82-88`, `ffn_worker.py:93-99`). NPU runners under `v1/worker/npu/` (attention_model_runner_v2 515 lines, ffn_model_runner 636, async_ffn_model_runner 523) — not read in full (facts from sizes + `__init__`).

**Model wrappers / registered models.** `afd_plugin/__init__.py:96-139` registers (as `AFD<arch>`): DeepSeek{,V2,V3,V32,V4}, GlmMoeDsa, Qwen3Moe, Qwen3_5. Note `DeepseekV4ForCausalLM` resolves to the NPU wrapper iff `torch_npu` is importable (`:109-113`). Wrapper code: `model_executor/models/deepseek_v2.py` (994), `deepseek_v4.py` (608), `qwen3_moe.py` (333), `qwen3_5.py` (554), plus NPU variants. Key mechanism (CUDA DeepSeek): the decoder layer constructs **only the modules its role owns** (`deepseek_v2.py:383-562`); the FFN stage on the Attention role is a parameter-free `RemoteFFNProxy` whose `forward` sends hidden states and receives the FFN output through the connector (`deepseek_v2.py:117-158`). MoE handoff variants: `AFDAttentionFusedMoE` / `GateOnlyRemoteMoE` / `AFDDeepseekV2RemoteExpertsMoE` (`:161-372`). `has_afd_model_registration`/`get_afd_model_config` (`model_utils.py:16-46`) swap the arch to the `AFD`-prefixed one at worker init.

**Connectors.** Base contract `connectors/base.py`: `AFDConnectorBase` (ABC) `:37-255` with lifecycle `init_afd_connector/close/is_initialized`, Attention-side `send_attn_output/recv_ffn_output`, FFN-side `recv_attn_output/send_ffn_output`, and an optional `AFDControlPlane` (`:258-307`) with `update_state_from_dp_metadata/send_dp_metadata_list/recv_dp_metadata_list`. Factory `connectors/factory.py:23-105` is a name→loader registry; registers the 3 connectors (`:88-102`); `create_connector` resolves role-rank then constructs (`:49-68`). Metadata/wire types `connectors/metadata.py` (438): `AFDDPMetadata`, `AFDControlPayload`, `AFDTransferMetadata/Context/State`, `AFDA2FTransferPayload`/`AFDF2ATransferPayload`, `AFDForwardContextMetadata`, plus JSON `encode/decode/send/recv_control_payload` (`:320-420`). GPU P2P `connectors/gpu/p2p.py` (1125): NCCL point-to-point via `PyNcclCommunicator` wrapped in `afd_p2p_{send,recv}[_group]` custom ops (`:979-1122`); world ordered `[F0..A0..]`; has a control plane `P2pNcclAFDControlPlane` (`:724-908`). NPU CAM variants: `connectors/npu/camp2p.py` (1206, sync, has control plane `:385`,`:767`), `connectors/npu/async_cam.py` (1068, async, `control_plane = None` `:283`). Vendored NPU binaries: `connectors/npu/bin/CAM_ascend910_93_openEuler_aarch64.run` (9.9 MB) + `umdk_cam_op_lib-209.0.0b1-cp312-cp312-linux_aarch64.whl` (350 KB) — see §11.

**Distributed topology / process groups.** `distributed/topology.py`: `AFDRankMapping` (`:16-43`), `resolve_role_rank` linearizes DP/PCP/TP into a role rank (`:61-105`), `build_rank_mapping` builds the P2P subgroup layout (`:118-184`), `validate_p2p_topology` requires `num_attention_ranks >= num_ffn_ranks` (`:52-58`). `distributed/afd_process_group.py`: `init_afd_process_group` builds a plugin-owned PG via private torch APIs without patching vLLM (`:62-120`), `DefaultProcessGroupSwitcher` (`:25-40`), `create_hccl_process_group_options` (`:43-59`).

**Compat shims / monkey patches (`afd_plugin/compat/*`).** What each replaces and where (upstream = vLLM@ced6857 unless noted):
- `compat/vllm.py` — not a patch; version gate (target `0.30.0`) (`:12`, `:53-68`).
- `compat/patches/config_validation.py` — patches `EngineArgs.create_engine_config` (`vllm:vllm/engine/arg_utils.py`) and `VllmConfig.__post_init__` (`vllm:vllm/config/vllm.py`) to (a) relax the native ubatching all2all-backend assertion by swapping a temp backend `deepep_low_latency` during validation (`:73-89`, `:138-157`), and (b) rewrite `worker_cls` when auto (`:92-93`,`:179-197`). Install site `:235-261`.
- `compat/patches/engine_core.py` (737) — patches `vllm.v1.engine.core` so an AFD **FFN** EngineCore returns right after building the executor (no KV/scheduler setup), keeping FFN out of `HybridKVCacheCoordinator` (`:1-14`; header read, body not read in full).
- `compat/patches/async_dp_engine.py` (438) — patches `EngineCoreProc.run_engine_core`, `vllm.v1.engine.utils.launch_core_engines`, `DPAsyncMPClient.add_request_async` so async-DP Attention uses plain `EngineCoreProc` instead of `DPEngineCoreProc` and skips wave coordination (`:1-33`).
- `compat/patches/async_dp_forward_context.py` (218) — patches `vllm.forward_context.set_forward_context` to skip MoE DP-metadata all-reduce for the async connector (`:1-24`).
- `compat/patches/gpu_mrv2_ubatching.py` (282) — scoped (context-manager) replacements of `vllm.v1.worker.gpu.model_runner.maybe_build_ubatch_runner` and `dispatch_cg_and_sync_dp` to enable DP1 DBO (`:47-73`, `:125-260`, `:263-282`).
- `compat/patches/npu/*` — `ascend_config.py` (258), `ascend_platform.py` (131), `mla_graph.py` (58), `mrv2_ubatching.py` (346): Ascend-platform/config/graph patches (NPU; headers only).
- Non-patch NPU compat: `compat/npu/{feature_validation,forward_context,ops,profiler,runtime,runtime_config}.py` (`runtime.py` is the public facade `:1-108`).
- `compat/profiler.py` (141) — plugin-owned torch profiler for GPU runners (env `AFD_GPU_{ATTENTION,FFN}_PROFILER*`).

Note the worker-side runner swap is itself a localized patch inside `init_device` (module-attribute substitution of `GPUModelRunner`): `attention_worker.py:60-90`, `ffn_worker.py:73-100`.

---

## 4. vLLM plugin mechanism at ced6857a

Full detail in `vllm-plugin-hooks.md`. Summary: group `vllm.general_plugins` (`vllm:vllm/plugins/__init__.py:18`) read by `load_plugins_by_group` (`:36-74`) and executed by `load_general_plugins` (`:77-90`), guarded once-per-process by `plugins_loaded` (`:33`, `:82-85`). Filtered by env `VLLM_PLUGINS` (comma list; `None`=all) (`:40`,`:64`; `vllm:vllm/envs.py:1146-1149`). Called in **every** relevant process/moment: `EngineArgs` arg parsing/validation (`vllm:vllm/engine/arg_utils.py:839`,`:3009`), engine-core process (`vllm:vllm/v1/engine/core.py:119`), each worker process (`vllm:vllm/v1/worker/worker_base.py:271`), and the lazy-registration subprocess (`vllm:vllm/model_executor/models/registry.py:1570`). Models register via `ModelRegistry.register_model(arch, "module:Class")` (lazy string form avoids CUDA re-init) (`vllm:vllm/model_executor/models/registry.py:1126-1169`).

---

## 5. Main flows (numbered, with file:function)

### (a) Start-up of an attention server and an FFN server
1. `vllm serve ... --additional-config '{"afd":{...}}'` on each role; both need `VLLM_USE_V2_MODEL_RUNNER=1` (`README.md:204-213`, recipe `2a2f_graph_dbo_dp1tp2.sh:1-60`).
2. `EngineArgs.create_engine_config` runs → patched version loads plugins, so `register_afd()` has run; worker_cls is `auto` → rewritten to the role worker (`config_validation.py:51-113`, `:179-197`).
3. For the FFN role, `engine_core.py` makes EngineCore return after executor construction (daemon, no scheduler) (`engine_core.py:1-14`).
4. Worker process: `load_general_plugins()` again (idempotent) then constructs the role worker (`vllm:worker_base.py:271`).
5. `AFDAttentionWorker.init_device` validates the stack, swaps `GPUModelRunner`→`AFDAttentionModelRunnerV2`, calls native `init_device` (`attention_worker.py:60-90`). Runner `__init__` creates the connector via the factory and asserts a control plane exists (`attention_model_runner_v2.py:369-411`). `load_model` defers `connector.init_afd_connector()` to the end so A/F weight loading overlaps (`:454-462`).
6. `AFDFFNWorker.init_device` swaps in `GPUFFNModelRunner` (`ffn_worker.py:73-99`); `get_kv_cache_spec` returns `{}` (no KV) (`:102-105`); `initialize_from_config` initializes the connector and starts the daemon loop (`:107-113`); `compile_or_warm_up_model` is a no-op (`:115-120`).
7. **Connector handshake** (collective, either start order OK — `README.md:258-260`): `init_afd_connector` joins the AFD NCCL world `[F0..A0..]` rendezvoused at `tcp://host:port`, builds per-subgroup `StatelessProcessGroup` + two `PyNcclCommunicator`s (a2e, e2a), and, on DP-metadata ranks, a separate `p2p` control PG (`p2p.py:245-316`). Rank math `build_rank_mapping` (`topology.py:118-184`).
8. FFN daemon loop: `AFDFFNWorker._run_ffn_server_loop` blocks on `control_plane.recv_dp_metadata_list()` and dispatches to `capture_model` or `execute_model` (`ffn_worker.py:160-199`).

### (b) One request through the proxy and the attention side
1. `tools/proxy_server.py` is the vLLM-Ascend **prefill/decode** load-balancing proxy (copied, `proxy_server.py:1`), OpenAI `/v1/completions` + `/v1/chat/completions` (`:14`), round-robin/score across prefiller+decoder backends (`:205-268`). It does **not** itself split attention/FFN — AFD's split is internal to the decode server's connector. (Body routing functions not read in full.)
2. Requests go only to the Attention API server (`README.md:258-260`). The native scheduler/EngineCore run on the Attention side normally.
3. Attention `execute_model` (`attention_model_runner_v2.py:569-595`) wraps native V2 execute in `_use_afd_execution_context` (`:316-356`), which installs the AFD metadata provider (`forward_context.py:37-67`) and (for FULL_DECODE_ONLY) the replay hook.
4. Native V2 builds a `ForwardContext`; the provider attaches `afd_metadata` and, via the control plane, sends per-stage DP token metadata to FFN (`attention_metadata.py:211-257`, `:75-116`).

### (c) One decode step across attention and FFN workers, layer by layer
1. Attention runs the native model forward per layer. Each decoder layer computes attention locally (`deepseek_v2.py:577-647`), then its FFN/MoE stage is a `RemoteFFNProxy` whose `forward` → `_send_and_receive` (`:117-158`).
2. `_send_and_receive`: build `AFDTransferMetadata` (layer_idx, stage_idx, seq_len), `connector.send_attn_output(hidden_states, context[, router_logits][, input_ids])` (`:140-150`); if DBO active, `maybe_apply_dbo_yield` yields to the peer ubatch thread (`:151-154`, `dbo.py:12-24`); then `connector.recv_ffn_output(ref_tensor=hidden_states, ubatch_idx=stage)` returns the FFN output to continue the layer (`:155-158`).
3. **Tensors crossing the connector (P2P):** hidden states `(num_tokens, hidden_size)` A→F; optionally router_logits (when `compute_gate_on_attention`) and int32 input_ids (DeepSeek-V4 hash MoE) (`p2p.py:323-390`). F→A: the per-peer FFN output slices (`p2p.py:554-613`). All on the current CUDA stream via `afd_p2p_*` custom ops.
4. **Metadata/control plane:** DP token counts travel on a separate `p2p` NCCL PG as JSON (`metadata.py:320-420`, `p2p.py:853-908`); `update_state_from_dp_metadata` derives per-stage wire-tensor shapes and (graph mode) preallocates receive buffers (`p2p.py:744-851`).
5. **FFN side:** daemon → `GPUFFNModelRunner.execute_model` (`ffn_model_runner.py:153-184`) → `_ffn_forward` loops layers×stages: `recv_attn_output` (concat peers, record seq_lens) → `compute_ffn_output`/`compute_experts_output` → `send_ffn_output` (split by seq_lens back to each Attention peer) (`ffn_model_runner.py:186-269`, `p2p.py:428-613`).
6. **DBO / micro-batching:** native DBO with exactly 2 ubatches (`validation.py:126-131`); DP1 enabled by `gpu_mrv2_ubatching.py` scoped patches (`:47-73`,`:125-260`); the two stages are driven as `stage_idx` 0/1 through the same connector.
7. **CUDA graphs:** only `FULL_DECODE_ONLY` (`cuda_graph.py:20-21`,`:42-85`). Attention captures via native `capture_model` wrapped to emit AFD warmup/capture control (`attention_model_runner_v2.py:509-553`) and replays via `run_fullgraph` hook (`:237-313`). FFN captures/replays its own `torch.cuda.CUDAGraph` keyed by DP metadata in its daemon (`ffn_model_runner.py:316-403`, `make_ffn_graph_key` in `cuda_graph.py:104-133`).

---

## 6. ~30 concepts a learner must understand (grouped, with implementing files)

**A. vLLM plugin basics**
1. `vllm.general_plugins` entry point & once-per-process load — `pyproject.toml:45-46`, `vllm:vllm/plugins/__init__.py:77-90`.
2. `register_afd()` registration flow — `afd_plugin/__init__.py:142-216`.
3. `ModelRegistry.register_model` lazy string registration — `__init__.py:211-214`, `vllm:registry.py:1126-1169`.
4. Patch discipline (idempotent, version-gated) — `compat/patches/__init__.py:1-8`, `compat/vllm.py:53-68`.

**B. AFD configuration**
5. `--additional-config["afd"]` schema & aliases — `config.py:41-117`, `:32-38`.
6. Active vs disabled AFD; validate — `config.py:289-351`.
7. Role/runner validators (ranks==DP*TP, static EP, no PP/CP) — `validation.py:76-239`.
8. Connector `connector_extra_config` strict parse — `base.py:64-72`, `camp2p.py:78-160`, `async_cam.py:146-230`.

**C. Roles & workers**
9. Attention vs FFN role — `config.py:92-97`.
10. Auto worker selection — `config_validation.py:179-197`, `validation.py:280-309`.
11. Worker→runner swap at `init_device` — `attention_worker.py:60-90`, `ffn_worker.py:73-99`.
12. FFN daemon loop (connector-driven, no scheduler) — `ffn_worker.py:133-199`.

**D. Topology & process groups**
13. `[F0..A0..]` world ordering & subgroups — `topology.py:16-43`, `p2p.py:124-143`.
14. `resolve_role_rank` (DP/PCP/TP linearization) — `topology.py:61-105`.
15. `build_rank_mapping` balanced blocks — `topology.py:108-184`.
16. Plugin-owned process groups — `afd_process_group.py:62-120`.

**E. Connector data/control plane**
17. Connector ABC contract — `base.py:37-255`.
18. Control plane (DP metadata) — `base.py:258-307`, `p2p.py:724-908`.
19. Transfer metadata/context/payloads — `metadata.py:153-312`.
20. Control-payload wire (JSON send/recv) — `metadata.py:320-420`.
21. P2P custom ops (`afd_p2p_*`) for compile/graph — `p2p.py:979-1122`.
22. Factory registry — `factory.py:23-105`.

**F. Model wrappers / MoE handoff**
23. Role-aware decoder layer construction — `deepseek_v2.py:383-562`.
24. `RemoteFFNProxy` send/receive — `deepseek_v2.py:117-158`.
25. Gate placement (`compute_gate_on_attention`) & remote experts — `deepseek_v2.py:161-372`, `:649-721`.
26. AFD forward-context metadata provider — `forward_context.py:18-67`, `attention_metadata.py:211-257`.
27. Remote-experts boundary (router_logits/input_ids) — `metadata.py:164-169`, `ffn_model_runner.py:221-268`.

**G. Execution: graphs, DBO, profiling**
28. CUDA graph policy `FULL_DECODE_ONLY` — `cuda_graph.py:20-85`.
29. DBO yield custom op & 2-ubatch constraint — `dbo.py:27-57`, `validation.py:126-131`.
30. DP1 DBO scoped patches — `gpu_mrv2_ubatching.py:47-282`.
31. (NPU) async connector no-control-plane model — `async_cam.py:273-283`.
32. Deterministic routing simulator (benchmarks) — `routing_simulator.py:122-172`.

---

## 7. ~20 central files (line count, one-line role)

| File | Lines | Role |
|---|---|---|
| `afd_plugin/__init__.py` | 234 | Entry point `register_afd`, model registry table, spawn override |
| `afd_plugin/config.py` | 370 | `AFDConfig` + parse/validate of `additional_config["afd"]` |
| `afd_plugin/validation.py` | 388 | Worker/runner FQCNs + V2 deployment validators |
| `afd_plugin/compat/patches/config_validation.py` | 264 | Patch: worker auto-select + ubatching backend relax |
| `afd_plugin/compat/patches/engine_core.py` | 737 | Patch: FFN EngineCore becomes a connector daemon |
| `afd_plugin/compat/patches/async_dp_engine.py` | 438 | Patch: async-DP Attention engine scheduling |
| `afd_plugin/compat/patches/gpu_mrv2_ubatching.py` | 282 | Patch: DP1 DBO dispatch/runner seams |
| `afd_plugin/connectors/base.py` | 310 | Connector ABC + control-plane ABC |
| `afd_plugin/connectors/metadata.py` | 438 | Transfer/DP metadata types + wire codec |
| `afd_plugin/connectors/factory.py` | 105 | Name→connector registry + `create_connector` |
| `afd_plugin/connectors/gpu/p2p.py` | 1125 | GPU NCCL P2P connector + control plane + custom ops |
| `afd_plugin/connectors/npu/camp2p.py` | 1206 | NPU sync CAM P2P connector (control plane) |
| `afd_plugin/connectors/npu/async_cam.py` | 1068 | NPU async CAM connector (no control plane) |
| `afd_plugin/distributed/topology.py` | 193 | Rank mapping + role-rank resolution |
| `afd_plugin/v1/worker/attention_model_runner_v2.py` | 622 | GPU Attention runner (seam over native V2) |
| `afd_plugin/v1/worker/ffn_model_runner.py` | 483 | GPU FFN runner (connector-driven) |
| `afd_plugin/v1/worker/attention_metadata.py` | 357 | `AFDMetadataProviderMixin` (metadata/control plumbing) |
| `afd_plugin/v1/worker/cuda_graph.py` | 210 | CUDA-graph policy + FFN graph keys |
| `afd_plugin/v1/worker/ffn_worker.py` | 226 | GPU FFN worker + daemon loop |
| `afd_plugin/model_executor/models/deepseek_v2.py` | 994 | CUDA DeepSeek AFD wrapper (role split, MoE handoff) |
| `tools/proxy_server.py` | 1351 | P/D load-balancing proxy (copied from vLLM-Ascend) |

NPU-central (not read in full): `v1/worker/npu/ffn_model_runner.py` (636), `attention_model_runner_v2.py` (515), `async_ffn_model_runner.py` (523), `model_executor/models/npu/deepseek_v4.py` (777), `deepseek_v2_attention_gate.py` (447).

---

## 8. Configuration sources

**`--additional-config["afd"]` top-level keys** — declared in `AFDConfig` (`config.py:51-73`), coerced/validated in `_normalize_mapping` (`:120-176`) + `validate_afd_config` (`:311-351`):
| Key | Default | Set/validated |
|---|---|---|
| `connector` | `"P2pNcclAFDConnector"` | must be one of 3 (`config.py:26-30`,`:326-330`) |
| `role` | `"attention"` | ∈{attention,ffn} (`:318-321`) |
| `host` | `"127.0.0.1"` | non-empty (`:339-340`) |
| `port` | `1239` | 1..65535 (`:341-342`) |
| `num_attention_ranks` | `1` | >0, ≥`num_ffn_ranks` for P2P (`:343-346`, `topology.py:52-58`) |
| `num_ffn_ranks` | `1` | >0 (`:347-350`) |
| `compute_gate_on_attention` | `False` | bool coerce (`:170-174`) |
| `async_dp` (alias `async`) | `False` | requires async connector (`:331-334`) |
| `afd_process_group_timeout_s` | `120` | positive int (`:164-168`) |
| `connector_extra_config` | `{}` | strictly parsed by the selected connector |
Aliases accepted: `afd_connector/afd_role/afd_port/afd_host` (`config.py:32-38`, `README.md:308-309`).

**`connector_extra_config` keys (per connector):** P2P: none allowed (`p2p.py:145-158`). CAMP2P: `core_num(8)`, `attn_core_num`, `ffn_core_num`, `compute_gate_on_attention(False)`, `hccl_buffer_size`, `quant_mode(0)` (`camp2p.py:84-108`). Async CAM: `dynamicQuant(0)`, `attn_ranks_per_dp(1)`, `hccl_buffer_size`, `ffn_two_stream(False)`, `ffn_compute_aic_num(12)`, `ffn_compute_aiv_num(24)`, `ffn_combine_aiv_num(24)`, … (`async_cam.py:146-230`; not all fields read).

**Env vars.** Plugin: `AFD_FORCE_BALANCED_TOPK_IDS`, `AFD_ASYNC_CAM_LAYERED_GMM` (`envs.py:9-19`); `AFD_FORCE_SPAWN_MULTIPROCESSING` (`__init__.py:60`); `AFD_BENCHMARK_FORCE_LB_TOPN_PER_RANK` + `VLLM_MOE_ROUTING_SIMULATION_STRATEGY=afd_balanced` (`routing_simulator.py:26-27`); `AFD_GPU_{ATTENTION,FFN}_PROFILER*` + `VLLM_TORCH_PROFILER_DIR` (`compat/profiler.py:18-31`); `BATCH_SIZE_FACTOR` (CAM capacity, `validation.py:49-54`); build: `AFD_BUILD_ASCEND_OPS`, `SOC_VERSION` (`setup.py:43-67`, `README.md:158-167`). vLLM envs consumed: `VLLM_USE_V2_MODEL_RUNNER`, `VLLM_PLUGINS`.

**Recipe flags:** `--data-parallel-size/--tensor-parallel-size/--enable-expert-parallel/--enforce-eager/--enable-dbo/--dbo-{decode,prefill}-token-threshold/--max-cudagraph-capture-size/--compilation-config/--additional-config` (recipe `2a2f_graph_dbo_dp1tp2.sh:7-60`, README `:122-157`).

**Generator feasibility:** YES for top-level keys — a script could extract them from `AFDConfig.__dataclass_fields__` + the field comments in `config.py:51-73` and the validation messages in `config.py:311-351`. Per-connector extra config is extractable from each `parse_extra_config`/`*ExtraInfo` dataclass (`camp2p.py:78-108`, `async_cam.py:146-230`). Env vars are centralized in `envs.py` (only 2) but others are scattered — a `grep 'os.environ'` pass across `afd_plugin/` + `setup.py` would be needed. Recipe flags: parse the `*.sh` for `--additional-config`/`--dbo-*`.

---

## 9. Recipes

Index `recipe/README.md:34-38`. GPU layout `recipe/gpu/P2pNcclAFDConnector/deepseek_v2_lite/README.md`:
- `prefill_decode_disaggregation/` — `2p1a1f_{eager,graph}_dbo.sh`: 2 colocated prefillers + 1 Attention + 1 FFN + proxy (5 processes, 4 GPUs) (`README.md:40-50`).
- `prefill_decode_colocation/` — `2a2f_{eager,graph}_dbo_dp1tp2.sh`, `..._dp2tp1.sh` (TP/DP cross product), `4a4f_{eager,graph}_dbo_dp2tp2.sh` (DP=2 each side), `multipod_2a_2f_graph_dbo_dp1tp2.sh` (k8s 2-pod, gated on `POD` env, not run directly) (`README.md:52-77`).
- `qwen3_5_122b_a10b_fp8/.../multipod_2a_2a_2f_graph.sh` (Qwen3.5, 2 attention pods + 1 FFN).
Key flags per recipe: role/connector/host/port/num_*_ranks in `--additional-config`; DBO `--enable-dbo --dbo-decode-token-threshold 2 --dbo-prefill-token-threshold 12`; graph via `--max-cudagraph-capture-size 64 --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[64]}'` (`README.md:122-157`, script `:1-60`). README tuning notes: thresholds/capture sizes are example defaults, tune per workload (`README.md:141-157`). Benchmark via `tools/benchmarks/benchmark.sh` → `vllm bench serve` (`README.md:102-120`).

NPU: `recipe/npu/CAMP2pAFDConnector/deepseek_v3_2/` (`afd_attention.sh`, `afd_ffn.sh`, `baseline_ep64.sh`, throughput PNGs 16k/32k) and `recipe/npu/CAMAsyncAFDConnector/deepseek_v3_2/` (+ `v0_26_accuracy/attention_dp2tp8.sh`, `ffn_ep16.sh`, median-TTFT PNG). READMEs claim v0.30 hardware validation pending; async v0.26 DP2TP8+EP16 reached 0.9522 strict match (`recipe/README.md:37-38`). (NPU recipe README bodies not read in full.)

Topologies named: `2a2f`, `4a4f`, `2p1a1f`, `multipod_2a_2f`, `2a_2a_2f`, `dp2tp8`/`ep16`/`ep64`.

---

## 10. Good existing docs / images; doc-vs-code spot checks

Reusable docs (`docs/design/module/`, 2,898 lines): `index.md` (routing + mermaid dependency graph, `:75-91`), `plugin_boundary.md` (266), `attention_runtime.md` (417), `ffn_runtime.md` (392), `connector_contracts.md` (362), `model_integration.md` (354), `execution_platforms.md` (438, incl. "tested runtime matrix"), `compatibility_and_patches.md` (244), `e2e_testing.md` (288). User guides: `docs/gpu/NCCL_P2P_CONNECTOR_USER_GUIDE.md`, `docs/npu/{CAM_P2P,CAM_ASYNC}_CONNECTOR_USER_GUIDE.md`, `CAM_ASYNC_ROUTED_OPS.md`, `ASYNC_FFN_RUNTIME.md`, `TESTING.md`, `TROUBLESHOOTING.md`, `LAYERED_W2_MDL_VALIDATION.md`. Connector overview `afd_plugin/connectors/README.md`. Images reusable: `docs/assets/vllm-afd-plugin-architecture.svg` (architecture), `docs/assets/afd-plugin-logo.png`, `docs/npu/dbo.png`, recipe throughput/TTFT PNGs.

Spot checks (no bugs claimed; observations):
- `index.md:38` references AFD `36dadb4`; current HEAD is `7452d52`. The design docs were last source-reviewed against an older commit — site should treat design-doc line references as potentially stale vs HEAD code.
- README canonical config uses `port: 1239` (`README.md:293`) and `AFDConfig` default is `1239` (`config.py:58`) — consistent; but recipes use `6269`/`6239` — these are example overrides, not the default (consistent).
- `index.md:106` routes `compat/npu/forward_context.py` etc. to "Execution platforms"; file exists (`compat/npu/forward_context.py` 72 lines) — consistent.
- `connector_contracts.md`/`base.py` both state async CAM has no control plane; code confirms `async_cam.py:283 control_plane = None` — consistent.

(Full doc bodies for attention_runtime/ffn_runtime/connector_contracts NOT read line-by-line; a dedicated fact-check pass is advisable before quoting them.)

---

## 11. Git / submodules / comments / unusual items

- Git: 651 commits (`git rev-list --count HEAD`), latest commit date 2026-10-27, `.git` ≈ 50 MB. No submodules (`.gitmodules` absent). Uses Git LFS (`.lfsconfig`, `.gitattributes`).
- **`AGENTS.md`** (8.7 KB) — contributor guidelines (code style, naming, patch discipline); `CLAUDE.md` (104 B) just points to AGENTS.md.
- **`.agents/skills/`** — 95 files, 10 skills: `adapt-model`, `deploy-afd-k8s`, `deploy-dsv4-flash-async`, `maintain-vllm-main`, `review-pr`, `run-e2e`, `run-vllm-bench-k8s`, `upgrade-gpu-version`, `upgrade-npu`, `upgrade-layered-gmm-ops`. `.claude/` has 1 file.
- **Vendored binaries** (not built from source in this repo): `afd_plugin/connectors/npu/bin/CAM_ascend910_93_openEuler_aarch64.run` (9.9 MB, CANN op package) + `umdk_cam_op_lib-209.0.0b1-cp312-cp312-linux_aarch64.whl` (350 KB, Python 3.12 aarch64 wheel). These are the prebuilt NPU CAM operators the async/CAMP2P connectors depend on; loaded via `afd_plugin.compat.npu.ensure_afd_ascend_ops_loaded` (`README.md:177-182`, `compat/npu/__init__.py:14`). Python packaging includes `_cann_ops_custom/**` as package-data (`pyproject.toml:70-71`), excluded as a package (`:67`).
- No CJK/non-English comments found under `afd_plugin/` (grep for `\p{Han}` empty). `pyproject.toml:132-194` has a large typo-allowlist of CANN/Ascend identifiers (hints at vendored upstream naming in `csrc/npu`).
- `tools/proxy_server.py` is explicitly copied from vLLM-Ascend (`:1`).
- Build: `setup.py` auto-detects Ascend (`torch_npu` present or CANN env) to decide whether to build ops; overridable by `AFD_BUILD_ASCEND_OPS` (`setup.py:35-67`, `README.md:326-331`).

---

## 12. Proposal: GPU-only / NPU-only / shared, and NPU section sizing

**GPU-only** (~1.4k lines direct, plus the CUDA-oriented "shared"-pathed runtime): `connectors/gpu/p2p.py`, `compat/patches/gpu_mrv2_ubatching.py`, `connectors/gpu/__init__.py`. Functionally GPU: the attention/ffn runners + DeepSeek/Qwen CUDA wrappers.

**NPU-only** (~9.3k lines, the largest block): `connectors/npu/{camp2p,async_cam}.py` + `bin/`, `compat/npu/*`, `compat/patches/npu/*`, `model_executor/models/npu/*`, `model_executor/npu/*`, `v1/worker/npu/*`, `async_cam_startup.py`, plus `csrc/npu` kernels (out of scope).

**Shared** (~9.5k lines): `config.py`, `config_utils.py`, `validation.py`, `envs.py`, `connectors/{base,metadata,factory}.py`, `distributed/*`, `v1/worker/{attention_metadata,ffn_metadata,cuda_graph,dbo,ubatch_wrapper}.py`, `model_executor/models/{deepseek_v2,deepseek_v4,qwen3_moe,qwen3_5,forward_context,model_utils}.py`, `routing_simulator.py`, `compat/{vllm,profiler}.py`, `compat/patches/{config_validation,engine_core,async_dp_engine,async_dp_forward_context}.py`.

**Sizing an NPU (Ascend) section if in scope:** The NPU surface is ≈46% of plugin Python and spans 3 connectors-worth of distinct machinery (sync CAMP2P with control plane, async CAM without, two-stream FFN, W4A8, MLA graph, attention-gate, DBO) plus Ascend platform patches and the CAM startup protocol. A full treatment would need roughly **8–12 pages**: ~2 (Ascend platform + compat patches), ~2 (CAMP2P connector + topology), ~3 (Async CAM connector: control-plane-less model, two-stream FFN, startup protocol, routed ops, W4A8), ~2 (NPU attention/FFN runners + MLA graph + DBO), ~1 (vendored binaries, build, install). **If kept as overview only: 1–2 pages** — one page explaining "same AFD contract, different transport (HCCL/CAM) and prebuilt operators; async connector has no control plane and drives FFN from its receive loop," plus a pointer table to the NPU docs. Given the reader is GPU-literate and the repo's own NPU hardware validation is "pending," I recommend the **short overview** and deep GPU coverage.

---

## For the supervisor (control-flow observations — NOT called bugs)

1. **FFN role runs the full native model-load/scheduler-adjacent path but no scheduler.** `AFDFFNWorker.execute_model` raises immediately (`ffn_worker.py:122-131`); FFN work only flows through the daemon `_run_ffn_server_loop` (`:160-199`). If a deployment sends decode requests to the FFN API server, they fail fast by design — worth stating clearly on the site so readers don't expect FFN to be an API endpoint.
2. **Worker selection is a `worker_cls` string rewrite, only when `auto`.** `config_validation.py:60` reads `self.worker_cls`; `_select_afd_worker_for_auto` (`:92-93`) only fires when it was `"auto"`. An explicit non-AFD `--worker-cls` is NOT rewritten and is later rejected by `assert_compatible_afd_stack` (`validation.py:357-367`). Control flow: auto→rewrite→pass; explicit-wrong→no rewrite→validation error. Reader-facing nuance.
3. **Two connectors have a control plane, one does not.** P2P (`p2p.py:222`) and CAMP2P (`camp2p.py:385`) set `control_plane`; async CAM leaves it `None` (`async_cam.py:283`). GPU FFN runner asserts the control plane is non-None (`ffn_model_runner.py:87-89`), so async CAM is NPU-only by construction. Verify this framing before the site states "every connector has a control plane."
4. **DP1 DBO relies on scoped monkey-patches of two vLLM functions**, installed only around AFD's own `initialize_kv_cache`/`execute_model` (`gpu_mrv2_ubatching.py:263-282`, used at `attention_model_runner_v2.py:342`,`:480`). The patches are context-managed (restored on exit). Control flow: native `maybe_build_ubatch_runner` excludes DP1; AFD re-enables it only within its scope.
5. **`get_afd_model_config` deepcopies the ModelConfig and relies on the `hf_text_config is hf_config` identity surviving deepcopy** to keep vLLM-Ascend's text-vs-multimodal detection correct (`model_utils.py:40-45`). This is a subtle invariant; flag before explaining model selection on NPU.
</content>
</invoke>
