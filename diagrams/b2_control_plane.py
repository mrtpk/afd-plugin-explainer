"""The control plane: DP metadata, once per step, before the layer loop.

Used by: src/concepts/control-plane.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/attention_model_runner_v2.py:153-157  DBO prepare seam publish
  afd_plugin/v1/worker/attention_metadata.py:211-257         non-ubatch publish path
  afd_plugin/v1/worker/attention_metadata.py:115-116         update_state + send_dp_metadata_list
  afd_plugin/connectors/metadata.py:320-346                  encode_control_payload (JSON)
  afd_plugin/connectors/metadata.py:376-420                  send/recv over the control group
  afd_plugin/v1/worker/ffn_worker.py:176                     recv_dp_metadata_list (once per step)
  afd_plugin/v1/worker/ffn_model_runner.py:194-203           update_state_from_dp_metadata
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The control plane: DP metadata, once per step",
         "Before the layer loop, the attention side publishes per-stage token counts to the FFN side.",
         params="afd_plugin/v1/worker/  ·  connectors/metadata.py  ·  canvas 1100")

# ---- Panel 1: frequency ----------------------------------------------------
y0 = 120
P1_H = 150
d.panel(y0, P1_H, 1, "How often does it run?",
        "The control plane runs once per step; the data plane runs once per layer and stage.")

by = y0 + 70
d.box(46, by, 300, 52, "control plane",
      ["DP metadata: ONCE per step", "before the layer loop"], col=VIOLET, align="left")
d.box(386, by, 420, 52, "data plane  (layer loop)",
      ["hidden states: once per layer AND stage",
       "send_attn_output / recv_ffn_output"], col=BLUE, align="left")
d.box(846, by, 224, 52, "sampling",
      ["once per step", "attention side"], col=EMERALD, align="left")
d.arrow(346, by + 26, 386 - 2, by + 26, INK)
d.arrow(806, by + 26, 846 - 2, by + 26, INK)

# ---- Panel 2: the path -----------------------------------------------------
y2 = y0 + P1_H + 22
P2_H = 250
d.panel(y2, P2_H, 2, "What carries it, and where?",
        "Both attention publish paths call update_state then send; the FFN loop receives and applies.")

# attention publish paths
px = 46
pw = 300
pyr = y2 + 64
d.box(px, pyr, pw, 70, "attention publish (2 paths)",
      ["DBO seam: prepare()  :153-157",
       "non-DBO: forward ctx :252-257",
       "both: update_state + send :115-116"],
      col=BLUE, align="left")

# payload
d.box(px + pw + 30, pyr, 300, 70, "AFDControlPayload  (JSON)",
      ["num_tokens_across_dp_cpu (int32)",
       "max_tokens; graph/warmup flags",
       "encode_control_payload :320-346"],
      col=VIOLET, align="left")

# control group
d.box(px + 2 * (pw + 30), pyr, 324, 70, "separate control group",
      ["NCCL process group \"p2p\"",
       "send -> size tensor + uint8 bytes",
       "metadata.py:376-420"],
      col=NEUTRAL, align="left")

d.arrow(px + pw, pyr + 35, px + pw + 30 - 2, pyr + 35, BLUE)
d.arrow(px + 2 * pw + 30, pyr + 35, px + 2 * (pw + 30) - 2, pyr + 35, VIOLET)

# FFN receive
fy = pyr + 108
d.box(px, fy, 490, 58, "FFN server loop  (once per step)",
      ["recv_dp_metadata_list()  ffn_worker.py:176",
       "then capture_model / execute_model"], col=EMERALD, align="left")
d.box(px + 520, fy, 504, 58, "update_state_from_dp_metadata",
      ["derive wire shapes per stage; preallocate",
       "receive buffers in graph mode  ffn_model_runner.py:194-203"],
      col=EMERALD, align="left")
d.arrow(px + 490, fy + 29, px + 520 - 2, fy + 29, EMERALD)
# down arrow from control group to FFN loop
d.path_arrow(f"M {px + 2 * (pw + 30) + 162:.0f},{pyr + 70} L {px + 2 * (pw + 30) + 162:.0f},{fy - 18} "
             f"L {px + 245:.0f},{fy - 18} L {px + 245:.0f},{fy - 2}", VIOLET)

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention side"), (VIOLET, "control plane"), (EMERALD, "FFN side")])
y += 34
y = d.footnotes(30, y,
                ["The async NPU connector has no control plane (control_plane = None); its receive loop drives "
                 "the FFN side instead.",
                 "The control group is separate from the per-subgroup data communicators; only FFN ranks and the "
                 "first ffn_size attention ranks join it."])
d.save(height=y + 14)
