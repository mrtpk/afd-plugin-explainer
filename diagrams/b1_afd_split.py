"""Why AFD splits attention from the FFN/MoE part.

Used by: src/learn/what-is-afd.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/config.py:61-64        num_attention_ranks / num_ffn_ranks
  afd_plugin/connectors/gpu/p2p.py:11-20   world order [F.. A..], A >= F rule
General knowledge (no citation): attention is KV-cache memory-bound per request;
dense FFN and MoE experts are weight-bound and favour large batches.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, AMBER, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Why AFD splits attention from the FFN",
         "Attention is memory-bound per request. The FFN and MoE experts are weight-bound and want a large batch.",
         params="afd_plugin/config.py:61-64  ·  connectors/gpu/p2p.py:11-20")

# ---- Panel 1: two parts, two bottlenecks ---------------------------------
y0 = 124
P1_H = 196
d.panel(y0, P1_H, 1, "One model, two very different workloads",
        "Each part is slow for a different reason, so each wants a different batch size and rank count.")
cy = y0 + 72
d.box(60, cy, 470, 104, "Attention part",
      ["state per request: the KV cache",
       "memory-bound: many reads,",
       "little compute per byte moved"], BLUE)
d.box(570, cy, 470, 104, "FFN / MoE part",
      ["shared weights and experts",
       "weight-bound: compute-heavy,",
       "faster with a large batch"], EMERALD)

# ---- Panel 2: AFD runs each part as its own server group -----------------
y2 = y0 + P1_H + 20
P2_H = 232
d.panel(y2, P2_H, 2, "AFD runs each part as its own server group",
        "A connector moves hidden states both ways; the attention side keeps the KV cache and the API server.")
by = y2 + 78
d.box(70, by, 360, 108, "Attention role",
      ["x ranks (e.g. 2)",
       "KV cache + scheduler",
       "sends hidden states"], BLUE)
d.box(670, by, 360, 108, "FFN role",
      ["y ranks (e.g. 2)",
       "experts, no KV cache",
       "returns the FFN output"], EMERALD)
# connector arrows both ways
mid_y = by + 40
d.arrow(430, mid_y, 668, mid_y, AMBER, sw=2)
d.arrow_label(549, mid_y, "hidden states ->", AMBER)
mid_y2 = by + 74
d.arrow(668, mid_y2, 432, mid_y2, EMERALD, sw=2)
d.arrow_label(549, mid_y2, "<- FFN output", EMERALD)
d.text(549, by + 100, "connector", 12, MUTE, "bold", "middle", mono=True)

# ---- legend + footnotes ---------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention role"), (EMERALD, "FFN role"), (AMBER, "hidden states")])
y += 34
y = d.footnotes(30, y,
                ["Topology name xAyF: x attention ranks and y FFN ranks (e.g. 2A2F). The P2P connector needs "
                 "num_attention_ranks >= num_ffn_ranks (config.py:61-64, gpu/p2p.py:11-20).",
                 "Bottleneck facts are general serving knowledge, not repository claims."])
d.save(height=y + 12)
