"""Role-aware decoder-layer construction: which module each AFD role builds.

Used by: src/concepts/model-wrappers.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/model_executor/models/deepseek_v2.py:459-517  attention-role branches
  afd_plugin/model_executor/models/deepseek_v2.py:493-500  CUDA MoE -> remote experts shell
  afd_plugin/model_executor/models/deepseek_v2.py:501-507  NPU MoE + gate -> GateOnlyRemoteMoE
  afd_plugin/model_executor/models/deepseek_v2.py:508-515  dense + gate -> native MLP
  afd_plugin/model_executor/models/deepseek_v2.py:516-517  dense -> RemoteFFNProxy
  afd_plugin/model_executor/models/deepseek_v2.py:519-561  FFN-role branches
  afd_plugin/model_executor/models/qwen3_moe.py:142-180    Qwen3-MoE branches
  afd_plugin/model_executor/models/qwen3_5.py:146-243      Qwen3.5/3.6 branches
  afd_plugin/model_executor/models/deepseek_v4.py:134-173  DeepSeek-V4 branches
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, NEUTRAL, VIOLET, INK, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Role-aware decoder layers",
         "AFDDeepseekV2DecoderLayer.__init__ builds only the module its AFD role owns.",
         params="deepseek_v2.py:383-561  ·  one branch per layer kind  ·  canvas 1100")

# ---- Panel 1: attention-role branches --------------------------------------
y0 = 120
P1_H = 262
d.panel(y0, P1_H, 1, "Attention role: what replaces mlp?",
        "self_attn is always the native attention module (:474-491). mlp depends on the layer.")

d.box(400, y0 + 60, 300, 40, "role == attention",
      ["self_attn: native  (:474-491)"], col=NEUTRAL, align="middle")

r1 = y0 + 126
d.box(46, r1, 500, 52, "dense layer  (default)",
      ["mlp = RemoteFFNProxy                 :516-517"], col=BLUE, align="left")
d.box(566, r1, 500, 52, "CUDA MoE layer",
      ["mlp = AFDDeepseekV2RemoteExpertsMoE   :493-500"], col=BLUE, align="left")
r2 = r1 + 66
d.box(46, r2, 500, 52, "NPU MoE layer + gate-on-attention",
      ["mlp = GateOnlyRemoteMoE              :501-507"], col=BLUE, align="left")
d.box(566, r2, 500, 52, "dense layer + gate-on-attention",
      ["mlp = native DeepseekV2MLP (local)   :508-515"], col=BLUE, align="left")

# ---- Panel 2: FFN-role branches --------------------------------------------
y2 = y0 + P1_H + 22
P2_H = 160
d.panel(y2, P2_H, 2, "FFN role: self_attn is dropped, mlp is the real compute",
        "self_attn = PPMissingLayer (:520). mlp depends on the layer kind.")

bw = 330
fy = y2 + 72
d.box(46, fy, bw, 56, "dense + gate-on-attention",
      ["mlp = PPMissingLayer", "owned by attention  :521-522"], col=EMERALD, align="left")
d.box(394, fy, bw, 56, "MoE layer",
      ["mlp = native DeepseekV2MoE", "gate cleared on CUDA  :523-553"], col=EMERALD, align="left")
d.box(742, fy, bw, 56, "dense layer",
      ["mlp = native DeepseekV2MLP", "full FFN here  :554-561"], col=EMERALD, align="left")

# ---- Panel 3: the four model families --------------------------------------
y3 = y2 + P2_H + 22
P3_H = 170
d.panel(y3, P3_H, 3, "Four model families, one pattern",
        "Each wrapper replaces the remote stage with a parameter-free proxy; the details differ.")

my = y3 + 62
d.box(46, my, 500, 44, "DeepSeek V2 / V3 / V3.2 / GLM-MoE-DSA",
      ["deepseek_v2.py   gate-on-attention optional"], col=VIOLET, align="left")
d.box(566, my, 500, 44, "Qwen3-MoE",
      ["qwen3_moe.py   CUDA only, gate always on FFN"], col=VIOLET, align="left")
my2 = my + 56
d.box(46, my2, 500, 44, "Qwen3.5 / 3.6 MoE",
      ["qwen3_5.py   CUDA, text only"], col=VIOLET, align="left")
d.box(566, my2, 500, 44, "DeepSeek-V4",
      ["deepseek_v4.py   CUDA, sends int32 input_ids"], col=VIOLET, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y3 + P3_H + 18
d.legend(30, y, [(BLUE, "attention role"), (EMERALD, "FFN role"),
                 (NEUTRAL, "native module"), (VIOLET, "model family")])
y += 34
y = d.footnotes(30, y,
                ["On CUDA every MoE layer uses the remote-experts shell (uses_remote_experts, :444); "
                 "GateOnlyRemoteMoE is the NPU gate-on-attention path.",
                 "The FFN role keeps the gate weights loadable but clears the runner gate on CUDA, so it "
                 "consumes the attention-side router logits (:548-553)."])
d.save(height=y + 14)
