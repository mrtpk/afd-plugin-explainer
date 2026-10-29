"""The FFN runtime: a connector-driven server loop and the layers x stages forward.

Used by: src/concepts/ffn-runtime.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/ffn_worker.py:133-158    daemon thread server loop
  afd_plugin/v1/worker/ffn_worker.py:168-196    one recv per step, dispatch to execute/capture
  afd_plugin/v1/worker/ffn_model_runner.py:186-215  _ffn_forward: layer_indices, stages
  afd_plugin/v1/worker/ffn_model_runner.py:236-268  recv_attn_output -> compute -> send_ffn_output
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import EMERALD, BLUE, NEUTRAL, INK, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The FFN runtime",
         "No real scheduler and no KV cache: a daemon thread reads the control plane and drives the model.",
         params="ffn_worker.py  ·  ffn_model_runner.py  ·  canvas 1100")

# ---- Panel 1: the server loop ----------------------------------------------
y0 = 120
P1_H = 170
d.panel(y0, P1_H, 1, "The server loop: one step per control payload",
        "A daemon thread blocks on the control plane, then dispatches one step (ffn_worker.py:168-196).")

cw = 320
cy = y0 + 70
d.step_card(46, cy, cw, 64, 1, "recv_dp_metadata_list", EMERALD, tag="once/step",
            rows=[("in", "control plane :176"), ("out", "dp_metadata_list")])
d.step_card(390, cy, cw, 64, 2, "dispatch", EMERALD, tag="branch",
            rows=[("eager", "execute_model :191"), ("graph", "capture_model :185")])
d.step_card(734, cy, cw, 64, 3, "synchronize", EMERALD, tag="cuda",
            rows=[("then", "loop again :198"), ("stop", "shutdown event")])
d.arrow(366, cy + 32, 388, cy + 32, EMERALD)
d.arrow(710, cy + 32, 732, cy + 32, EMERALD)

# ---- Panel 2: the layers x stages forward ----------------------------------
y2 = y0 + P1_H + 22
P2_H = 196
d.panel(y2, P2_H, 2, "_ffn_forward: for each layer, for each stage",
        "layer_indices = expert layers only when gate-on-attention, else all layers (:211-215).")

ly = y2 + 70
d.box(46, ly, 300, 56, "recv_attn_output",
      ["hidden_states + context", "ffn_model_runner.py:236"], col=BLUE, align="left")
d.box(400, ly, 300, 56, "compute",
      ["experts / FFN output", "compute_experts/ffn :251-267"], col=EMERALD, align="left")
d.box(754, ly, 300, 56, "send_ffn_output",
      ["result back to attention", "ffn_model_runner.py:268"], col=EMERALD, align="left")
d.arrow(346, ly + 28, 398, ly + 28, BLUE)
d.arrow(700, ly + 28, 752, ly + 28, EMERALD)

d.box(46, ly + 86, 1008, 40, "loop extent",
      ["layers (:223)  x  stages (:230)   ·   stage = DBO ubatch index on the wire"],
      col=NEUTRAL, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "receive from attention"), (EMERALD, "FFN compute / send"),
                 (NEUTRAL, "loop")])
y += 34
y = d.footnotes(30, y,
                ["The GPU FFN runner needs a control plane: a connector with control_plane None is "
                 "rejected in the loop (ffn_worker.py:169-174).",
                 "sample_tokens raises; the FFN role never samples (ffn_model_runner.py:405-406)."])
d.save(height=y + 14)
