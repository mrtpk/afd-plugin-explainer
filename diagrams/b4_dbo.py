"""Dual-batch overlap (DBO): exactly two stages overlap across the connector.

Used by: src/concepts/dbo.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/dbo.py:12-24                 maybe_apply_dbo_yield
  afd_plugin/model_executor/models/deepseek_v2.py:146-158  send, yield, recv
  afd_plugin/v1/worker/ubatch_wrapper.py:28-29      stage_idx 0/1, num_stages 2
  afd_plugin/validation.py:126-131                  exactly two ubatches
  afd_plugin/compat/patches/gpu_mrv2_ubatching.py:263-283  scoped DP1 seams
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Dual-batch overlap (DBO)",
         "One step is split into exactly two stages. While stage 0 waits on the FFN side, stage 1 computes attention.",
         params="dbo.py  ·  deepseek_v2.py  ·  gpu_mrv2_ubatching.py  ·  canvas 1100")

# ---- Panel 1: the overlap --------------------------------------------------
y0 = 124
P1_H = 214
d.panel(y0, P1_H, 1, "Two stages overlap on one layer",
        "The proxy sends stage 0, yields, then stage 1 runs; the FFN side answers each stage (deepseek_v2.py:146-158).")

# attention lane
lane_y = y0 + 66
d.text(46, lane_y - 6, "attention", 12, BLUE, "bold")
d.box(46, lane_y, 150, 40, "attn s0", ["compute"], col=BLUE, align="left")
d.box(206, lane_y, 120, 40, "send s0", [":146"], col=BLUE, align="left")
d.box(336, lane_y, 150, 40, "attn s1", ["while s0 waits"], col=BLUE, align="left")
d.box(496, lane_y, 120, 40, "send s1", [":146"], col=BLUE, align="left")
d.box(626, lane_y, 130, 40, "recv s0", [":155"], col=BLUE, align="left")
d.box(766, lane_y, 130, 40, "recv s1", [":155"], col=BLUE, align="left")

# yield marker
d.text(326, lane_y + 64, "DBO yield between send and recv (dbo.py)", 11.5, VIOLET, "bold", "middle")
d.line(266, lane_y + 40, 266, lane_y + 52, VIOLET, sw=1.4, dash="3 3")

# ffn lane
fy = lane_y + 92
d.text(46, fy - 6, "FFN", 12, EMERALD, "bold")
d.box(206, fy, 130, 40, "ffn s0", ["recv/compute/send"], col=EMERALD, align="left")
d.box(496, fy, 130, 40, "ffn s1", ["recv/compute/send"], col=EMERALD, align="left")
d.arrow(266, lane_y + 40, 266, fy - 2, EMERALD)
d.arrow(556, lane_y + 40, 556, fy - 2, EMERALD)
d.arrow(271, fy + 40, 686, lane_y + 40, EMERALD, dash="4 3")

# ---- Panel 2: where DP1 DBO is enabled -------------------------------------
y2 = y0 + P1_H + 20
P2_H = 120
d.panel(y2, P2_H, 2, "DP1 DBO: scoped patches re-enable what native vLLM excludes",
        "Native vLLM builds no ubatch runner at DP1. The patch does, only inside AFD's own calls (gpu_mrv2_ubatching.py).")

by = y2 + 66
d.box(46, by, 480, 40, "use_gpu_mrv2_ubatch_factory",
      ["scoped in initialize_kv_cache  (:263-271, :480)"], col=VIOLET, align="left")
d.box(560, by, 494, 40, "use_gpu_mrv2_dbo_dispatch",
      ["scoped in execute_model context  (:274-282, :342)"], col=VIOLET, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention stage"), (EMERALD, "FFN stage"),
                 (VIOLET, "DBO yield / scoped patch")])
y += 34
y = d.footnotes(30, y,
                ["Exactly two stages: enable_dbo sets num_ubatches = 2; the validator rejects any other "
                 "count (validation.py:126-131).",
                 "Times here are illustrative, not measured. Thresholds (--dbo-decode-token-threshold / "
                 "--dbo-prefill-token-threshold) decide when a step splits."])
d.save(height=y + 14)
