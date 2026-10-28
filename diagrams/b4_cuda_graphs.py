"""CUDA graphs in AFD: FULL_DECODE_ONLY capture/replay on both roles.

Used by: src/concepts/cuda-graphs.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/cuda_graph.py:20-21          only FULL_DECODE_ONLY
  afd_plugin/v1/worker/attention_model_runner_v2.py:509-553  capture_model wrap
  afd_plugin/v1/worker/attention_model_runner_v2.py:237-313  fullgraph replay hook
  afd_plugin/v1/worker/ffn_model_runner.py:153-184  execute_model REPLAY path
  afd_plugin/v1/worker/ffn_model_runner.py:316-356  _dummy_run: one CUDAGraph per key
  afd_plugin/connectors/gpu/p2p.py:820-851          preallocated recv buffers in graph mode
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("CUDA graphs in AFD",
         "Only FULL_DECODE_ONLY. The attention side and the FFN side capture and replay separately, but must agree on token shapes.",
         params="cuda_graph.py  ·  attention_model_runner_v2.py  ·  ffn_model_runner.py  ·  canvas 1100")

# ---- Panel 1: attention side ----------------------------------------------
y0 = 124
P1_H = 176
d.panel(y0, P1_H, 1, "Attention side: wrap native capture and replay",
        "The AFD runner wraps native capture_model and the FULL replay hook to publish control before each forward.")

cw = 320
cy = y0 + 74
d.step_card(46, cy, cw, 70, 1, "capture_model", BLUE, tag="start-up",
            rows=[("warm-up", "then capture :509-553"),
                  ("sends", "DP metadata x2/desc")])
d.step_card(390, cy, cw, 70, 2, "run_fullgraph hook", BLUE, tag="per step",
            rows=[("before", "each replay :270-303"),
                  ("sends", "padded control once")])
d.step_card(734, cy, cw, 70, 3, "native replay", NEUTRAL, tag="vLLM",
            rows=[("owns", "the graph itself"),
                  ("mode", "FULL_DECODE_ONLY")])
d.arrow(366, cy + 35, 388, cy + 35, BLUE)
d.arrow(710, cy + 35, 732, cy + 35, MUTE)

# ---- Panel 2: FFN side -----------------------------------------------------
y2 = y0 + P1_H + 20
P2_H = 196
d.panel(y2, P2_H, 2, "FFN side: one torch.cuda.CUDAGraph per graph key",
        "The server loop picks capture or replay from the control payload (ffn_worker.py:182-196).")

ly = y2 + 74
d.box(46, ly, 300, 60, "make_ffn_graph_key",
      ["from DP metadata", "cuda_graph.py:104-133"], col=VIOLET, align="left")
d.box(400, ly, 300, 60, "graph exists?",
      ["_cuda_graphs[key]", "ffn_model_runner.py:166-174"], col=NEUTRAL, align="left")
d.box(754, ly, 300, 60, "REPLAY",
      ["graph.replay()  :176", "else capture / eager"], col=EMERALD, align="left")
d.arrow(346, ly + 30, 398, ly + 30, VIOLET)
d.arrow(700, ly + 30, 752, ly + 30, EMERALD)

d.box(46, ly + 92, 1008, 40, "capture path",
      ["_dummy_run: one CUDAGraph(), own graph pool  (ffn_model_runner.py:316-351)"],
      col=NEUTRAL, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention control"), (VIOLET, "graph key"),
                 (EMERALD, "FFN graph"), (NEUTRAL, "native vLLM")])
y += 34
y = d.footnotes(30, y,
                ["Both sides must agree on shapes. update_state_from_dp_metadata preallocates FFN receive "
                 "buffers while capturing (p2p.py:820-851).",
                 "afd_p2p_* custom ops wrap the NCCL send/recv so the transfers stay capturable "
                 "(p2p.py:979-1122). NPU uses ACL graphs (validation.py:233-239)."])
d.save(height=y + 14)
