"""The AFD world order, role ranks, P2P subgroups and DP-metadata destinations.

Used by: src/concepts/topology.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/distributed/topology.py:16-23    world order [F0..A0..]
  afd_plugin/distributed/topology.py:52-58    num_attention_ranks >= num_ffn_ranks
  afd_plugin/distributed/topology.py:92        role_rank formula
  afd_plugin/distributed/topology.py:135-136   attention world_rank / subgroup_index
  afd_plugin/distributed/topology.py:143-144   FFN world_rank / subgroup_index
  afd_plugin/distributed/topology.py:153-160   subgroup_ranks (FFN rank first)
  afd_plugin/distributed/topology.py:164-170   dp_metadata_destinations (first min_size attn ranks)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402


def rank_chip(d, x, y, label, col, world_rank):
    d.chip(x, y, 70, label, col, h=34)
    d.text(x + 35, y + 50, f"w{world_rank}", 11, MUTE, anchor="middle", mono=True)
    return x + 82


d = Diagram(width=1100)
d.header("The AFD world: ranks, subgroups and DP metadata",
         "FFN ranks first, then attention ranks. Subgroups carry hidden states; the control plane is narrower.",
         params="afd_plugin/distributed/topology.py  ·  canvas 1100")

# ---- Panel 1: the world order and the role-rank rule -----------------------
y0 = 122
P1_H = 186
d.panel(y0, P1_H, 1, "How are ranks ordered and numbered?",
        "The P2P world is [F0, F1, ..., A0, A1, ...] (topology.py:16-23).")

cx = 60
cy = y0 + 70
cx = rank_chip(d, cx, cy, "F0", EMERALD, 0)
cx = rank_chip(d, cx, cy, "F1", EMERALD, 1)
cx += 12
cx = rank_chip(d, cx, cy, "A0", BLUE, 2)
cx = rank_chip(d, cx, cy, "A1", BLUE, 3)
cx = rank_chip(d, cx, cy, "A2", BLUE, 4)
cx = rank_chip(d, cx, cy, "A3", BLUE, 5)
d.text(60, cy + 76, "Example world for 4A2F.  world_rank: FFN = role_rank;  attention = ffn_size + role_rank "
       "(topology.py:135, :143).", 12, MUTE)

d.box(640, y0 + 56, 430, 104, "role rank (topology.py:92)",
      ["role_rank =",
       "  (dp_rank*pcp + pcp_rank)*tp + tp_rank",
       "rule: num_attention_ranks >= num_ffn_ranks",
       "      (topology.py:52-58)"],
      col=NEUTRAL, align="left")

# ---- Panel 2: 2A2F ---------------------------------------------------------
y2 = y0 + P1_H + 20
P2_H = 158
d.panel(y2, P2_H, 2, "2A2F: the planes agree",
        "Two FFN subgroups, one attention peer each; data plane and control plane match.")

bw = 480
by = y2 + 62
d.box(46, by, bw, 58, "F0 subgroup  (data plane)",
      ["ranks: F0, A0     F0 = subgroup rank 0",
       "A0 -> F0 hidden states"], col=EMERALD, align="left")
d.box(566, by, bw, 58, "F1 subgroup  (data plane)",
      ["ranks: F1, A1     F1 = subgroup rank 0",
       "A1 -> F1 hidden states"], col=EMERALD, align="left")
d.callout(46, by + 70, 1000, "Control plane:",
          "A0 -> F0 and A1 -> F1 DP metadata (every attention rank also sends here).", VIOLET)

# ---- Panel 3: 4A2F ---------------------------------------------------------
y3 = y2 + P2_H + 20
P3_H = 172
d.panel(y3, P3_H, 3, "4A2F: the planes differ",
        "Data plane uses contiguous blocks; the control plane uses only the first F attention ranks.")

by3 = y3 + 62
d.box(46, by3, bw, 58, "F0 subgroup  (data plane)",
      ["ranks: F0, A0, A1    fan-in of 2",
       "A0,A1 -> F0 ; F0 splits output back"], col=EMERALD, align="left")
d.box(566, by3, bw, 58, "F1 subgroup  (data plane)",
      ["ranks: F1, A2, A3    fan-in of 2",
       "A2,A3 -> F1 ; F1 splits output back"], col=EMERALD, align="left")
d.callout(46, by3 + 70, 1000, "Control plane:",
          "only A0 -> F0 and A1 -> F1 send DP metadata; A2 and A3 send none (topology.py:164-170).",
          VIOLET)

# ---- legend + footnotes ----------------------------------------------------
y = y3 + P3_H + 18
d.legend(30, y, [(EMERALD, "FFN rank / subgroup"), (BLUE, "attention rank"),
                 (VIOLET, "control plane (DP metadata)")])
y += 34
y = d.footnotes(30, y,
                ["min_size = min(ffn_size, attention_size); under the A>=F rule it equals ffn_size, so the "
                 "first ffn_size attention ranks are the DP-metadata senders.",
                 "Simplified: TP and DP inside a role are folded into the role rank; the chips show one rank each."])
d.save(height=y + 14)
