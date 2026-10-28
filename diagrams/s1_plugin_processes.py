"""When and in which processes vLLM loads general plugins.

Used by: src/learn/vllm-plugins.html
Sources (vLLM at the pinned commit in explainer.json, extra_repos.vllm):
  vllm/plugins/__init__.py:77-90       load_general_plugins + plugins_loaded guard
  vllm/engine/arg_utils.py:3003-3009   AsyncEngineArgs.add_cli_args call site (process 0)
  vllm/engine/arg_utils.py:837-839     EngineArgs.__post_init__ call site (process 0)
  vllm/v1/engine/core.py:116-119       EngineCore.__init__ call site (EngineCore process)
  vllm/v1/worker/worker_base.py:269-271  WorkerBase.init_worker call site (each worker)
  vllm/model_executor/models/registry.py:1566-1570  _run call site (model-inspection subprocess)
Source (afd-plugin):
  afd_plugin/__init__.py:150-153        register_afd's own _registered guard
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, AMBER, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Where vLLM loads general plugins",
         "vLLM calls load_general_plugins() from 5 call sites, in 4 kinds of process.",
         params="group vllm.general_plugins  ·  guard plugins_loaded  ·  afd = afd_plugin:register_afd")

# ---- Panel 1: the processes and call sites -------------------------------
y0 = 128
P1_H = 262
d.panel(y0, P1_H, 1, "Which process calls it, and when?",
        "Each process that builds args, the engine core, or a worker loads the plugins once.")

bw, bh = 300, 80
ty = y0 + 78
x1, x2, x3 = 46, 396, 746

d.box(x1, ty, bw, bh, "Process 0 (launch / API)",
      ["add_cli_args", "arg_utils.py:3009", "__post_init__  :839"], col=BLUE, align="left")
d.box(x2, ty, bw, bh, "EngineCore process",
      ["__init__", "v1/engine/core.py:119"], col=EMERALD, align="left")
d.box(x3, ty, bw, bh, "Each worker process",
      ["init_worker", "v1/worker/worker_base.py:271"], col=VIOLET, align="left")

d.arrow(x1 + bw, ty + bh / 2, x2 - 2, ty + bh / 2, INK)
d.arrow_label((x1 + bw + x2) / 2, ty + bh / 2, "spawns", INK)
d.arrow(x2 + bw, ty + bh / 2, x3 - 2, ty + bh / 2, INK)
d.arrow_label((x2 + bw + x3) / 2, ty + bh / 2, "spawns", INK)

# model-inspection subprocess, branching from process 0
iy = ty + bh + 36
d.box(x1, iy, 430, 56, "Model-inspection subprocess",
      ["_run   registry.py:1570   (spawned to resolve a model class)"], col=NEUTRAL, align="left")
d.path_arrow(f"M {x1 + 60},{ty + bh} L {x1 + 60},{iy - 2}", INK, dash="5 4")
d.text(x1 + 70, iy - 12, "spawned on demand", 11, MUTE)

# ---- Panel 2: the guard --------------------------------------------------
y2 = y0 + P1_H + 22
P2_H = 150
d.panel(y2, P2_H, 2, "Why a plugin must be idempotent",
        "The guard stops a second load inside one process; a new process starts fresh.")

gw, gh = 500, 62
gy = y2 + 64
d.box(46, gy, gw, gh, "Same process: second call returns early",
      ["plugins_loaded = True", "plugins/__init__.py:82-85"], col=NEUTRAL, align="left")
d.box(560, gy, gw, gh, "New process (spawn): guard is False again",
      ["the plugin runs once more -> must be idempotent", "afd adds its own guard  __init__.py:150-153"],
      col=AMBER, align="left")

# ---- legend + footnotes ---------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "process 0"), (EMERALD, "EngineCore"), (VIOLET, "worker"),
                 (NEUTRAL, "short-lived subprocess")])
y += 36
y = d.footnotes(30, y,
                ["Process 0 loads plugins twice: once in add_cli_args (to extend the parser) and once when the engine config is built.",
                 "The guard plugins_loaded is module state, so it resets in every new process; spawn copies no Python state."])
d.save(height=y + 14)
