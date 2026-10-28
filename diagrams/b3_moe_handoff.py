"""The MoE handoff: where the gate runs and what crosses the wire.

Used by: src/concepts/moe-handoff.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/model_executor/models/deepseek_v2.py:306-320  gate built on attention when flag set
  afd_plugin/model_executor/models/deepseek_v2.py:548-553  FFN gate cleared -> external routing
  afd_plugin/v1/worker/ffn_model_runner.py:211-215         FFN layer_indices: expert layers only when flag
  afd_plugin/v1/worker/ffn_model_runner.py:251-267         compute_experts_output vs compute_ffn_output
  afd_plugin/connectors/gpu/p2p.py:336-390                 wire order: hidden_states, router_logits, input_ids
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The MoE handoff",
         "compute_gate_on_attention decides which side runs the MoE gate, and what the connector carries.",
         params="deepseek_v2.py  ·  ffn_model_runner.py:211-215  ·  p2p.py:336-390  ·  canvas 1100")

# ---- Panel 1: gate on the FFN side (default, false) ------------------------
y0 = 120
P1_H = 150
d.panel(y0, P1_H, 1, "compute_gate_on_attention = false  (the default)",
        "The gate stays with the experts on the FFN side. The FFN runs every layer.")

by = y0 + 70
d.box(46, by, 430, 52, "attention side",
      ["self_attn -> hidden_states", "no gate"], col=BLUE, align="left")
d.box(630, by, 424, 52, "FFN side",
      ["gate + experts, all layers", "layer_indices = range(num_layers)"], col=EMERALD, align="left")
d.arrow(476, by + 26, 628, by + 26, BLUE)
d.arrow_label(553, by + 18, "hidden_states", BLUE)

# ---- Panel 2: gate on the attention side (true) ----------------------------
y2 = y0 + P1_H + 22
P2_H = 158
d.panel(y2, P2_H, 2, "compute_gate_on_attention = true",
        "The attention side builds the gate; the FFN side runs experts only, for expert layers.")

cy = y2 + 72
d.box(46, cy, 430, 56, "attention side",
      ["gate -> router_logits  (:306-320)", "GateOnlyRemoteMoE / remote shell"], col=BLUE, align="left")
d.box(630, cy, 424, 56, "FFN side",
      ["compute_experts_output  (:257-261)", "layer_indices = expert layers (:211-215)"],
      col=EMERALD, align="left")
d.arrow(476, cy + 28, 628, cy + 28, BLUE)
d.arrow_label(553, cy + 20, "+ router_logits", BLUE)

# ---- Panel 3: what crosses the wire ----------------------------------------
y3 = y2 + P2_H + 22
P3_H = 150
d.panel(y3, P3_H, 3, "What crosses on the data plane (send_attn_output)",
        "Order on the wire: hidden_states, then router_logits, then input_ids (p2p.py:336-338).")

wy = y3 + 66
d.box(46, wy, 330, 52, "any layer, gate on FFN",
      ["hidden_states only"], col=VIOLET, align="left")
d.box(394, wy, 330, 52, "MoE layer, gate on attention",
      ["hidden_states + router_logits"], col=VIOLET, align="left")
d.box(742, wy, 330, 52, "DeepSeek-V4 hash MoE",
      ["+ int32 input_ids  (:210)"], col=VIOLET, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y3 + P3_H + 18
d.legend(30, y, [(BLUE, "attention side"), (EMERALD, "FFN side"), (VIOLET, "wire payload")])
y += 34
y = d.footnotes(30, y,
                ["Router logits are consumed only when the FFN runner gate is None; AFD clears it so the "
                 "runner uses external routing (deepseek_v2.py:548-553, :714-721).",
                 "Qwen3-MoE requires compute_gate_on_attention=false, so it always ships the whole MoE "
                 "block (qwen3_moe.py:84-87)."])
d.save(height=y + 14)
