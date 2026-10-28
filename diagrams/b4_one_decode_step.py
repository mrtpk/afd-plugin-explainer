"""One decode step on 2A2F with DBO and FULL_DECODE_ONLY graphs.

Used by: src/tours/one-decode-step.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/attention_metadata.py:115-116   control-plane publish once/step
  afd_plugin/v1/worker/attention_model_runner_v2.py:270-303  FULL replay on attention
  afd_plugin/v1/worker/ffn_worker.py:176               one recv per step
  afd_plugin/v1/worker/ffn_model_runner.py:222-269     layer x stage forward
  vllm/v1/worker/gpu/model_runner.py:2048-2050         native sampling (attention)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("One decode step on 2A2F with DBO",
         "The control plane publishes once. Then every layer runs two stages of send/receive. Sampling runs once at the end.",
         params="attention_metadata.py  ·  ffn_model_runner.py  ·  canvas 1100")

# ---- Panel 1: once per step ------------------------------------------------
y0 = 124
P1_H = 150
d.panel(y0, P1_H, 1, "Once per step, before and after the layer loop",
        "One control-plane publish; the FFN loop receives one payload; sampling is a separate native call.")

cy = y0 + 70
d.step_card(46, cy, 320, 56, 1, "control plane publish", VIOLET, tag="once/step",
            rows=[("attn", "attention_metadata.py:115-116")])
d.step_card(390, cy, 320, 56, 2, "FFN recv DP metadata", VIOLET, tag="once/step",
            rows=[("ffn", "ffn_worker.py:176")])
d.step_card(734, cy, 320, 56, 3, "sample_tokens (after layers)", BLUE, tag="once/step",
            rows=[("native", "gpu/model_runner.py:2048-2050")])
d.arrow(366, cy + 28, 388, cy + 28, VIOLET)
d.text(710 + 12, cy + 70, "after the last layer only", 11, MUTE)

# ---- Panel 2: per layer and stage ------------------------------------------
y2 = y0 + P1_H + 20
P2_H = 210
d.panel(y2, P2_H, 2, "Per layer, per stage: the data plane",
        "Graphs replay per side; each stage sends hidden states, yields, and receives the FFN output.")

# attention row
ay = y2 + 66
d.text(46, ay - 6, "attention  (graph replay, :270-303)", 12, BLUE, "bold")
d.box(46, ay, 220, 44, "stage 0: send", ["deepseek_v2.py:146"], col=BLUE, align="left")
d.box(286, ay, 180, 44, "DBO yield", ["dbo.py"], col=VIOLET, align="left")
d.box(486, ay, 220, 44, "stage 1: send", ["deepseek_v2.py:146"], col=BLUE, align="left")
d.box(726, ay, 328, 44, "recv s0, recv s1", ["deepseek_v2.py:155"], col=BLUE, align="left")

# ffn row
fy = ay + 80
d.text(46, fy - 6, "FFN  (graph key lookup + replay, :166-176)", 12, EMERALD, "bold")
d.box(46, fy, 320, 44, "recv_attn_output (per stage)", ["ffn_model_runner.py:236"], col=EMERALD, align="left")
d.box(400, fy, 300, 44, "compute", ["experts / FFN  :251-267"], col=EMERALD, align="left")
d.box(734, fy, 320, 44, "send_ffn_output", ["ffn_model_runner.py:268"], col=EMERALD, align="left")
d.arrow(366, fy + 22, 398, fy + 22, EMERALD)
d.arrow(700, fy + 22, 732, fy + 22, EMERALD)
d.arrow(156, ay + 44, 156, fy - 2, EMERALD, dash="4 3")
d.arrow(820, fy, 860, ay + 44, EMERALD, dash="4 3")

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(VIOLET, "control plane / yield"), (BLUE, "attention"),
                 (EMERALD, "FFN")])
y += 34
y = d.footnotes(30, y,
                ["Graphs replay only for pure-decode steps (FULL_DECODE_ONLY). The control plane does not "
                 "publish again inside the layer loop.",
                 "2A2F: A0 maps to F0 and A1 to F1 (topology.py:135-136). Times are not shown."])
d.save(height=y + 14)
