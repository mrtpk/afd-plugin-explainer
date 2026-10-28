"""Life of a request, half 2: the connector and the FFN server.

Used by: src/tours/life-of-a-request.html (<x-diagram name="s2_request_ffn" />)
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/ffn_worker.py:122-131     scheduler-driven execute_model fails fast
  afd_plugin/v1/worker/ffn_worker.py:160-196      _run_ffn_server_loop (daemon thread)
  afd_plugin/v1/worker/ffn_worker.py:176          recv_dp_metadata_list (once per step)
  afd_plugin/v1/worker/ffn_model_runner.py:186-269  _ffn_forward (layers x stages)
  afd_plugin/v1/worker/ffn_model_runner.py:236     recv_attn_output
  afd_plugin/v1/worker/ffn_model_runner.py:263     FFN / MoE compute
  afd_plugin/v1/worker/ffn_model_runner.py:268     send_ffn_output
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, VIOLET, EMERALD, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Life of a request - the connector and the FFN server",
         "The FFN server runs no scheduler. A daemon loop waits for the attention side and answers per layer and stage.",
         params="afd_plugin/v1/worker/ffn_worker.py  ·  ffn_model_runner.py  ·  canvas 1100")

# ---- Panel 1: what crosses the connector ---------------------------------
y0 = 120
P1_H = 196
d.panel(y0, P1_H, 1, "What crosses the connector, and how often?",
        "The control plane carries DP metadata once per step; the data plane carries tensors per layer and stage.")

aw, ah = 300, 64
ax = 60
fx = 740
ry = y0 + 86
d.box(ax, ry, aw, ah, "Attention server (A0)", ["sends / receives", "deepseek_v2.py:146,155"], col=BLUE)
d.box(fx, ry, aw, ah, "FFN server (F0)", ["receives / sends", "ffn_model_runner.py:236,268"], col=EMERALD)

midl, midr = ax + aw, fx
# control plane A -> F (once per step)
d.arrow(midl + 2, ry + 14, midr - 2, ry + 14, VIOLET)
d.text((midl + midr) / 2, ry + 6, "DP metadata  (control plane, once per step)", 11.5, VIOLET, "bold", anchor="middle")
# data plane A -> F (per layer and stage)
d.arrow(midl + 2, ry + 34, midr - 2, ry + 34, EMERALD)
d.text((midl + midr) / 2, ry + 29, "hidden states  (data plane, per layer x stage)", 11.5, EMERALD, "bold", anchor="middle")
# data plane F -> A (per layer and stage)
d.arrow(midr - 2, ry + 54, midl + 2, ry + 54, EMERALD, dash="5 4")
d.text((midl + midr) / 2, ry + 66, "FFN output  (data plane, back)", 11.5, EMERALD, "bold", anchor="middle")

# ---- Panel 2: the FFN server loop ----------------------------------------
y2 = y0 + P1_H + 22
P2_H = 236
d.panel(y2, P2_H, 2, "What does the FFN server loop do?",
        "It has no API server and no scheduler. A connector-driven thread runs each step.")

bx = 60
bw = 300
bh = 58
gy = y2 + 70
# step 1: no request
d.box(bx, gy, bw, bh, "No request, no scheduler", ["execute_model raises", "ffn_worker.py:122-131"], col=NEUTRAL)
# step 2: recv DP metadata
d.box(bx + 360, gy, bw, bh, "recv DP metadata", ["once per step", "ffn_worker.py:176"], col=VIOLET)
# step 3: _ffn_forward loop
d.box(bx + 720, gy, bw, bh, "_ffn_forward", ["layers x stages", "ffn_model_runner.py:186"], col=EMERALD)
d.arrow(bx + bw + 2, gy + bh / 2, bx + 360 - 2, gy + bh / 2, MUTE)
d.arrow(bx + 360 + bw + 2, gy + bh / 2, bx + 720 - 2, gy + bh / 2, MUTE)

# the inner loop row
ly = gy + bh + 34
d.text(bx, ly - 8, "For each layer, for each stage:", 12.5, INK, "bold")
iw = 300
iy = ly + 4
d.box(bx, iy, iw, 52, "recv_attn_output", ["ffn_model_runner.py:236"], col=EMERALD)
d.box(bx + 360, iy, iw, 52, "FFN / MoE compute", ["ffn_model_runner.py:263"], col=NEUTRAL)
d.box(bx + 720, iy, iw, 52, "send_ffn_output", ["ffn_model_runner.py:268"], col=EMERALD)
d.arrow(bx + iw + 2, iy + 26, bx + 360 - 2, iy + 26, EMERALD)
d.arrow(bx + 360 + iw + 2, iy + 26, bx + 720 - 2, iy + 26, EMERALD)

y = y2 + P2_H + 22
d.legend(30, y, [(VIOLET, "control plane"), (EMERALD, "data plane / FFN side"),
                 (NEUTRAL, "no AFD transport")])
y += 40
y = d.footnotes(30, y, [
    "Simplified: one FFN rank (F0). The loop also handles warm-up and CUDA graph capture (ffn_worker.py:182-196), left out here.",
])
d.save(height=y + 14)
