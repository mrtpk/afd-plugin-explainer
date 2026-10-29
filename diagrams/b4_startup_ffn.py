"""Start-up tour, half 2: the FFN server comes up.

Used by: src/tours/start-up.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/compat/patches/config_validation.py:92-93,179-197  worker_cls rewrite
  afd_plugin/compat/patches/engine_core.py:56-68,599-623  FFN EngineCore early return
  afd_plugin/v1/worker/ffn_worker.py:93-98            runner swap
  afd_plugin/v1/worker/ffn_worker.py:107-113          connector init + start loop
  afd_plugin/compat/patches/engine_core.py:650-659    collective_rpc start_ffn_server_loop
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import EMERALD, NEUTRAL, BLUE, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Start-up, half 2: the FFN server",
         "The FFN EngineCore returns after the executor; its worker loads the model, joins the connector, and runs a daemon loop.",
         params="config_validation.py  ·  engine_core.py  ·  ffn_worker.py  ·  canvas 1100")

x = 130
w = 840
h = 52
gap = 16
y = 128
steps = [
    (1, "vllm serve  (role: ffn)", NEUTRAL, "vLLM",
     [("recipe", "same recipe, role: ffn")]),
    (2, "plugin load: register_afd", BLUE, "afd",
     [("guard", "_registered once per process  (:150-153)")]),
    (3, "create_engine_config: worker_cls auto -> AFDFFNWorker", BLUE, "patch",
     [("only if", "worker_cls was 'auto'  (:92-93, :179-197)")]),
    (4, "FFN EngineCore: return after the executor", EMERALD, "early",
     [("no real scheduler, blocks 0", "engine_core.py:56-68, 599-623")]),
    (5, "AFDFFNWorker.init_device: swap runner class", EMERALD, "afd",
     [("builds", "GPUFFNModelRunner  (:93-98)")]),
    (6, "initialize_from_config: join connector, start loop", EMERALD, "afd",
     [("then", "start_ffn_server_loop  (:107-113)")]),
    (7, "collective_rpc start_ffn_server_loop -> loop runs", EMERALD, "ready",
     [("from", "FFN EngineCore  (engine_core.py:650-659)")]),
]
for (n, title, col, tag, rows) in steps:
    d.step_card(x, y, w, h, n, title, col, tag=tag, rows=rows, key_w=52)
    if n != steps[-1][0]:
        d.arrow(x + w / 2, y + h, x + w / 2, y + h + gap - 2, MUTE)
    y += h + gap

y += 4
d.legend(30, y, [(BLUE, "plugin / patch"), (EMERALD, "FFN role"), (NEUTRAL, "native vLLM / state")])
y += 34
y = d.footnotes(30, y,
                ["The FFN EngineCore keeps a no-op scheduler (not None) so the native readiness handshake "
                 "still works (engine_core.py:608-614).",
                 "Either role can rendezvous first; init_afd_connector is collective across both."])
d.save(height=y + 14)
