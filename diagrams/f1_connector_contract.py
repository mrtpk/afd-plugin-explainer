"""The AFD connector contract: lifecycle, the two data paths, and the three connectors.

Used by: src/concepts/connector-contract.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/connectors/base.py:145-171   send_attn_output (attention side)
  afd_plugin/connectors/base.py:173-200   recv_ffn_output (attention side)
  afd_plugin/connectors/base.py:206-227   recv_attn_output (FFN side)
  afd_plugin/connectors/base.py:229-255   send_ffn_output (FFN side)
  afd_plugin/connectors/base.py:113-139   close / init_afd_connector / is_initialized
  afd_plugin/connectors/base.py:56-60      control_plane attribute (optional)
  afd_plugin/connectors/factory.py:88-102  the three registered connectors
  afd_plugin/connectors/npu/async_cam.py:283   CAMAsyncAFDConnector.control_plane = None
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, NEUTRAL, VIOLET, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The AFD connector contract",
         "One base class. The attention side and the FFN side each make two data-path calls.",
         params="afd_plugin/connectors/base.py  ·  factory.py  ·  canvas 1100")

# ---- Panel 1: the two data paths -----------------------------------------
y0 = 120
P1_H = 250
d.panel(y0, P1_H, 1, "Who calls what, in which order?",
        "The attention side sends then receives; the FFN side receives, computes, then sends.")

bw, bh = 300, 66
ty = y0 + 64        # top row (attention)
by = ty + 118       # bottom row (FFN)
lx, rx = 70, 640    # left and right columns

d.box(lx, ty, bw, bh, "send_attn_output", ["attention side", "base.py:145"], col=BLUE)
d.box(rx, ty, bw, bh, "recv_ffn_output", ["attention side", "base.py:173"], col=BLUE)
d.box(lx, by, bw, bh, "recv_attn_output", ["FFN side", "base.py:206"], col=EMERALD)
d.box(rx, by, bw, bh, "send_ffn_output", ["FFN side", "base.py:229"], col=EMERALD)

# data A -> F (left column, down)
d.arrow(lx + 170, ty + bh, lx + 170, by - 2, BLUE)
d.text(lx + 180, (ty + bh + by) / 2 + 3, "hidden states", 11.5, BLUE, "bold")
# control plane A -> F (optional, dashed violet, offset left)
d.arrow(lx + 70, ty + bh, lx + 70, by - 2, VIOLET, dash="5 4")
d.text(lx + 10, (ty + bh + by) / 2 - 7, "control plane", 11, VIOLET, "bold")
d.text(lx + 10, (ty + bh + by) / 2 + 8, "(optional)", 11, VIOLET)
# FFN compute (bottom, left -> right)
d.arrow(lx + bw, by + bh / 2, rx - 2, by + bh / 2, EMERALD)
d.text((lx + bw + rx) / 2, by + bh / 2 - 10, "FFN compute", 11.5, EMERALD, "bold", anchor="middle")
# data F -> A (right column, up)
d.arrow(rx + 150, by, rx + 150, ty + bh + 2, EMERALD)
d.text(rx + 160, (ty + bh + by) / 2 + 3, "FFN output", 11.5, EMERALD, "bold")

# ---- Panel 2: the lifecycle ----------------------------------------------
y2 = y0 + P1_H + 22
P2_H = 150
d.panel(y2, P2_H, 2, "What is the lifecycle?",
        "The runtime initializes the connector once, uses the data path many times, then closes it.")

lw, lh = 300, 60
ly = y2 + 62
x1, x2, x3 = 70, 400, 730
d.box(x1, ly, lw, lh, "init_afd_connector", ["collective, once", "base.py:124"], col=NEUTRAL)
d.box(x2, ly, lw, lh, "data path (per layer/stage)", ["send / recv calls", "many times"], col=NEUTRAL)
d.box(x3, ly, lw, lh, "close", ["release resources", "base.py:113"], col=NEUTRAL)
d.arrow(x1 + lw, ly + lh / 2, x2 - 2, ly + lh / 2, INK)
d.arrow(x2 + lw, ly + lh / 2, x3 - 2, ly + lh / 2, INK)
d.text(x2 + lw / 2, ly + lh + 18, "is_initialized is true between init and close (base.py:135)",
       11, MUTE, anchor="middle")

# ---- Panel 3: the three connectors ---------------------------------------
y3 = y2 + P2_H + 22
P3_H = 140
d.panel(y3, P3_H, 3, "Which connector for which device?",
        "The factory registers three connectors by name (factory.py:88).")

cw, ch = 328, 58
cy = y3 + 60
cx1, cx2, cx3 = 40, 386, 732
d.box(cx1, cy, cw, ch, "P2pNcclAFDConnector",
      ["GPU (CUDA) · sync", "control plane: yes"], col=NEUTRAL)
d.box(cx2, cy, cw, ch, "CAMP2pAFDConnector",
      ["NPU (Ascend) · sync", "control plane: yes"], col=NEUTRAL)
d.box(cx3, cy, cw, ch, "CAMAsyncAFDConnector",
      ["NPU (Ascend) · async", "control plane: none"], col=NEUTRAL)

# ---- legend + footnotes ---------------------------------------------------
y = y3 + P3_H + 18
d.legend(30, y, [(BLUE, "attention side"), (EMERALD, "FFN side"), (VIOLET, "control plane (DP metadata)")])
y += 36
y = d.footnotes(30, y,
                ["Simplified: the data path repeats for every layer and every DBO stage; the diagram shows one pass.",
                 "The attention side's recv_ffn_output and the FFN side's recv_attn_output both take a stage index."])
d.save(height=y + 14)
