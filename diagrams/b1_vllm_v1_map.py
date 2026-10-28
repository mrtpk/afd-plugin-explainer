"""The vLLM v1 process and class chain, with the AFD hook on each box.

Used by: src/learn/vllm-v1-map.html
Sources (vLLM at the pinned commit extra_repos.vllm in explainer.json):
  vllm/v1/engine/async_llm.py:78       AsyncLLM (API server process)
  vllm/v1/engine/core.py:105,134       EngineCore: scheduler + model_executor
  vllm/v1/executor/abstract.py:70-77   MultiprocExecutor / UniProcExecutor
  vllm/v1/worker/worker_base.py:271-277   worker_cls resolved to a class
  vllm/v1/worker/gpu_worker.py:469-482 GPUModelRunner (V2) construction
AFD hooks (afd-plugin): config_validation.py worker rewrite; engine_core.py FFN
early return; attention_worker.py / ffn_worker.py runner swap; __init__.py models.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, VIOLET, EMERALD, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The vLLM v1 chain AFD hooks into",
         "One box per process or class, top to bottom; the violet row is where afd-plugin changes it.",
         params="vLLM v0.30.0  ·  cited at extra_repos.vllm")

x, w = 50, 1000
y0 = 118
pitch = 82
ch = 68
n = 6
P_H = 64 + n * pitch - (pitch - ch) + 6
d.panel(y0, P_H, 1, "API server -> EngineCore -> executor -> worker -> runner -> model",
        "Each box runs load_general_plugins in its own process, so the plugin runs in each one.")
cy = y0 + 60

d.step_card(x, cy + 0 * pitch, w, ch, 1, "API server process (AsyncLLM)", BLUE,
            tag="async_llm.py:78", key_w=52,
            rows=[("vLLM", "builds EngineArgs, parses the CLI, owns HTTP"),
                  ("hook", "plugin load in add_cli_args / __post_init__", VIOLET)])
d.step_card(x, cy + 1 * pitch, w, ch, 2, "EngineCore process", BLUE,
            tag="core.py:105,134", key_w=52,
            rows=[("vLLM", "builds the scheduler and the model_executor"),
                  ("hook", "FFN EngineCore returns early (engine_core patch)", VIOLET)])
d.step_card(x, cy + 2 * pitch, w, ch, 3, "Executor", BLUE,
            tag="abstract.py:70-77", key_w=52,
            rows=[("vLLM", "mp = worker processes; uni = one, in-process"),
                  ("hook", "none; AFD works through the worker it builds", VIOLET)])
d.step_card(x, cy + 3 * pitch, w, ch, 4, "Worker (per device)", BLUE,
            tag="worker_base.py:271-277", key_w=52,
            rows=[("vLLM", "imports parallel_config.worker_cls by name"),
                  ("hook", "worker_cls rewritten to the AFD role worker", VIOLET)])
d.step_card(x, cy + 4 * pitch, w, ch, 5, "Model Runner V2", BLUE,
            tag="gpu_worker.py:469-482", key_w=52,
            rows=[("vLLM", "built when VLLM_USE_V2_MODEL_RUNNER is set"),
                  ("hook", "runner class swapped in Worker.init_device", VIOLET)])
d.step_card(x, cy + 5 * pitch, w, ch, 6, "The model", EMERALD,
            tag="__init__.py:211-214", key_w=52,
            rows=[("vLLM", "ModelRegistry resolves the architecture name"),
                  ("hook", "AFD<arch> model wrapper makes it role-aware", VIOLET)])

y = y0 + P_H + 18
d.legend(30, y, [(BLUE, "vLLM v1 box"), (VIOLET, "AFD hook point"), (EMERALD, "model")])
y += 34
y = d.footnotes(30, y,
                ["One device uses UniProcExecutor, so the worker runs inside the EngineCore process "
                 "(abstract.py:74-77).",
                 "Line numbers are vLLM v0.30.0 at the pinned commit."])
d.save(height=y + 12)
