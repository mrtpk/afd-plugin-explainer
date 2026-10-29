"""The data plane: tensors that cross per layer and stage, and the fan-in.

Used by: src/concepts/wire-data.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/connectors/gpu/p2p.py:323-390    send_attn_output: hidden, router_logits, input_ids
  afd_plugin/connectors/gpu/p2p.py:428-552    recv_attn_output: concat by peer, record seq_lens
  afd_plugin/connectors/gpu/p2p.py:554-613    send_ffn_output: split by seq_lens
  afd_plugin/connectors/metadata.py:188-200   AFDTransferMetadata (layer_idx, stage_idx, seq_lens)
  afd_plugin/connectors/gpu/p2p.py:195-197    hidden_size from hf_text_config
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Data on the wire: one layer, one stage",
         "Hidden states go A->F; the FFN rank fans in its peers, computes, and sends each slice back.",
         params="afd_plugin/connectors/gpu/p2p.py  ·  metadata.py  ·  canvas 1100")

# ---- Panel 1: one exchange -------------------------------------------------
y0 = 120
P1_H = 214
d.panel(y0, P1_H, 1, "What crosses for one layer and stage?",
        "Hidden states, then optional router logits and input IDs; the FFN output returns.")

by = y0 + 66
d.box(46, by, 440, 130, "attention rank: send_attn_output",
      ["hidden_states   [n, H]   model dtype",
       "router_logits   [n, E]   if gate on attn",
       "input_ids       int32 [n]  (V4 hash MoE)",
       "wire order: hidden, logits, ids",
       "metadata: layer_idx, stage_idx, seq_lens"],
      col=BLUE, align="left")
d.box(614, by, 440, 130, "FFN rank: recv -> compute -> send",
      ["recv_attn_output  ->  FFN / MoE experts",
       "send_ffn_output   [n, H]",
       "shape check: shape[0] == total_tokens",
       "total_tokens = sum(seq_lens)",
       "metadata.py:188-200, :230-231"],
      col=EMERALD, align="left")
d.arrow(486, by + 42, 614 - 2, by + 42, BLUE)
d.arrow_label((486 + 614) / 2, by + 42, "A -> F", BLUE)
d.arrow(614 - 2, by + 96, 486, by + 96, EMERALD)
d.arrow_label((486 + 614) / 2, by + 96, "F -> A", EMERALD)

# ---- Panel 2: fan-in worked example ----------------------------------------
y2 = y0 + P1_H + 22
P2_H = 196
d.panel(y2, P2_H, 2, "Worked example: two peers into one FFN rank (4A2F)",
        "H = 2048 (DeepSeek-V2-Lite, INFERRED); A0 and A1 each send 8 tokens to F0.")

cy = y2 + 72
d.box(46, cy, 240, 50, "A0 send", ["[8, 2048]"], col=BLUE, align="left")
d.box(46, cy + 64, 240, 50, "A1 send", ["[8, 2048]"], col=BLUE, align="left")
d.box(430, cy + 32, 260, 50, "F0 concat", ["[16, 2048]  seq_lens=[8,8]"], col=EMERALD, align="left")
d.box(820, cy + 28, 234, 58, "split back", ["[8,2048] -> A0", "[8,2048] -> A1"], col=EMERALD, align="left")
d.arrow(286, cy + 25, 430 - 2, cy + 50, EMERALD)
d.arrow(286, cy + 89, 430 - 2, cy + 66, EMERALD)
d.arrow(690, cy + 57, 820 - 2, cy + 57, EMERALD)

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention rank"), (EMERALD, "FFN rank")])
y += 34
y = d.footnotes(30, y,
                ["The transfers are custom ops (afd_p2p_send / afd_p2p_recv and the _group variants) so they "
                 "stay traceable under torch.compile and CUDA graph capture (p2p.py:979-1122).",
                 "With one peer the single slice is the whole tensor; no concat or split happens."])
d.save(height=y + 14)
