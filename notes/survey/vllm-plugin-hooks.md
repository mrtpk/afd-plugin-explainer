# vLLM plugin mechanism at ced6857a (v0.30.0)

For the AFD "plugin basics" page. All `vllm:` paths are in `/mnt/c/Users/tpesc/Downloads/test-harness/vllm` @ `ced6857afa0ea7b2e3f0846a62e1394e90f15607`.

## Entry-point groups vLLM reads

Defined in `vllm:vllm/plugins/__init__.py:16-30`:
- `vllm.general_plugins` (`:18`) — loaded in **all** processes (process0, engine-core, workers). **This is the group AFD uses.**
- `vllm.io_processor_plugins` (`:20`) — process0 only.
- `vllm.platform_plugins` (`:23`) — all processes, on first `current_platform` access.
- `vllm.stat_logger_plugins` (`:26`) — process0, async serving only.
- `vllm.endpoint_plugins` (`:30`) — API front-end only; opt-in, needs explicit `VLLM_PLUGINS` allowlist (`:93-158`).

## Functions that load them

- `load_plugins_by_group(group)` (`:36-74`) — discovers entry points via `importlib.metadata.entry_points(group=...)` (`:42`), filters by `VLLM_PLUGINS` allowlist (`:40`,`:64`), calls `plugin.load()` per entry, returns `{name: callable}`. Load failures are caught and logged, not raised (`:68-72`).
- `load_general_plugins()` (`:77-90`) — the general-group driver: once-per-process guard `plugins_loaded` (`:33`, `:82-85`), then for each loaded callable just **calls it** (`:88-90`). This is the call that invokes `afd_plugin:register_afd`.

## Once-per-process guard

Module global `plugins_loaded = False` (`vllm:vllm/plugins/__init__.py:33`), set `True` at the top of `load_general_plugins` before doing work (`:82-85`). AFD additionally has its own `_registered` guard in `register_afd` (`afd_plugin/__init__.py:48`, `:150-153`, `:216`), so re-entry within a process is a no-op even if vLLM calls it again.

## In which processes and at which moment they run

`load_general_plugins()` call sites (each a distinct process/moment):
- `vllm:vllm/engine/arg_utils.py:839` — inside `EngineArgs` post-processing (config build). AFD's `create_engine_config` patch wraps this path.
- `vllm:vllm/engine/arg_utils.py:3009` — inside `add_cli_args`, so plugins can extend the CLI parser (`:3005-3009`).
- `vllm:vllm/v1/engine/core.py:119` — EngineCore constructor ("plugins need to be loaded at the engine/scheduler level too", `:117-119`).
- `vllm:vllm/v1/worker/worker_base.py:271` — each worker process, before resolving `parallel_config.worker_cls` (`:271-274`). This is why AFD's `worker_cls` rewrite (done during config build) must be in place before the worker resolves the class.
- `vllm:vllm/model_executor/models/registry.py:1570` — the lazy model-inspection subprocess (`_run`, `:1565-1570`).

Implication for AFD: because the same once-guarded loader runs in config/engine/worker processes, `register_afd` must be idempotent and import-safe — which it is (`afd_plugin/__init__.py:142-160`).

## Env vars that filter plugins

- `VLLM_PLUGINS` — comma-separated allowlist of plugin **names** (the entry-point name, i.e. `afd`), or all plugins if unset (`vllm:vllm/plugins/__init__.py:40`,`:56-66`). Parsed at `vllm:vllm/envs.py:1146-1149` (`None` when unset; `split(",")` otherwise; note `VLLM_PLUGINS=""` → `[""]`). To load only AFD: `VLLM_PLUGINS=afd`.
- (Endpoint plugins additionally require being named in `VLLM_PLUGINS` even to be considered — not relevant to AFD.)

## How a plugin registers workers / models / config

- **Models:** `ModelRegistry.register_model(model_arch, model_cls)` (`vllm:vllm/model_executor/models/registry.py:1126-1169`). `model_cls` may be a class or a `"module:Class"` string; the string form is lazily imported (`_LazyRegisteredModel`, `:1153-1157`) to avoid CUDA init in the parent. AFD uses the string form with an `AFD`-prefixed arch name (`afd_plugin/__init__.py:211-214`); the worker swaps the model's HF arch to that prefixed name at init (`model_utils.py:25-46`).
- **Workers:** vLLM has **no** register-a-worker API in the general-plugin group. A plugin sets the worker by making `parallel_config.worker_cls` resolve to its class (`vllm:vllm/v1/worker/worker_base.py:271-277` resolves the qualname). AFD does this by rewriting `worker_cls` during config build (`afd_plugin/compat/patches/config_validation.py:179-197`).
- **Config:** plugins read vLLM's `additional_config` (free-form dict) rather than adding CLI flags; AFD parses `additional_config["afd"]` (`afd_plugin/config.py:244-279`). Plugins may also extend the CLI parser at the `add_cli_args` load moment, but AFD does not.
- **Other registration AFD performs at load:** a routing strategy via `RoutingSimulator.register_strategy` (`routing_simulator.py:166-172`), a custom op via `direct_register_custom_op` (`dbo.py:39-49`), and several monkey-patches applied at import of the patch modules (`afd_plugin/__init__.py:172-181`).
</content>
</invoke>
