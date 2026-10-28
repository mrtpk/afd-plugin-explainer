"""Start-up tour, half 1: the attention server comes up.

Used by: src/tours/start-up.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/__init__.py:142-216                     register_afd
  afd_plugin/compat/patches/config_validation.py:92-93,179-197  worker_cls rewrite
  afd_plugin/v1/worker/attention_worker.py:82-87     runner swap
  afd_plugin/v1/worker/attention_model_runner_v2.py:454-462  deferred connector init
  afd_plugin/v1/worker/attention_model_runner_v2.py:509-553  graph capture control
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, NEUTRAL, VIOLET, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Start-up, half 1: the attention server",
         "vllm serve loads the plugin, the config patch picks the AFD worker, and the runner swap builds the AFD model runner.",
         params="__init__.py  ·  config_validation.py  ·  attention_worker.py  ·  canvas 1100")

x = 130
w = 840
h = 52
gap = 16
y = 128
steps = [
    (1, "vllm serve  (role: attention)", NEUTRAL, "vLLM",
     [("recipe", "2a2f_graph_dbo_dp1tp2.sh")]),
    (2, "plugin load: register_afd  (process 0)", BLUE, "afd",
     [("adds", "patches, routing, DBO op, models  (:142-216)")]),
    (3, "patched create_engine_config: worker_cls auto -> AFDAttentionWorker", BLUE, "patch",
     [("only if", "worker_cls was 'auto'  (:92-93, :179-197)")]),
    (4, "AFDAttentionWorker.init_device: swap runner class", BLUE, "afd",
     [("builds", "AFDAttentionModelRunnerV2  (:82-87)")]),
    (5, "load_model: connector init deferred to the end", BLUE, "afd",
     [("overlaps", "attention + FFN weight load  (:454-462)")]),
    (6, "KV cache (attention only) + graph capture", VIOLET, "graph",
     [("sends", "warm-up / capture control  (:509-553)")]),
    (7, "ready: the attention server accepts requests", NEUTRAL, "ready",
     [("note", "FFN side handshake must also finish")]),
]
for (n, title, col, tag, rows) in steps:
    d.step_card(x, y, w, h, n, title, col, tag=tag, rows=rows, key_w=52)
    if n != steps[-1][0]:
        d.arrow(x + w / 2, y + h, x + w / 2, y + h + gap - 2, MUTE)
    y += h + gap

y += 4
d.legend(30, y, [(BLUE, "plugin / patch"), (VIOLET, "graph capture"), (NEUTRAL, "native vLLM / state")])
y += 34
y = d.footnotes(30, y,
                ["The connector rendezvous is deferred to the end of load_model so the two roles load "
                 "weights at the same time (attention_model_runner_v2.py:454-462)."])
d.save(height=y + 14)
