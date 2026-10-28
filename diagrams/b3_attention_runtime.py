"""The attention runtime: a thin AFD seam over native GPU Model Runner V2.

Used by: src/concepts/attention-runtime.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/v1/worker/attention_model_runner_v2.py:358-365  class + delegation docstring
  afd_plugin/v1/worker/attention_model_runner_v2.py:454-462  load_model defers init_afd_connector
  afd_plugin/v1/worker/attention_model_runner_v2.py:569-595  execute_model wraps + delegates
  afd_plugin/v1/worker/attention_model_runner_v2.py:153-158  ubatch prepare seam publishes control
  afd_plugin/v1/worker/attention_metadata.py:248-257         non-ubatch provider publishes control
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, NEUTRAL, VIOLET, INK, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("The attention runtime",
         "AFDAttentionModelRunnerV2 overrides a few seams; native V2 still runs the model and sampling.",
         params="attention_model_runner_v2.py  ·  attention_metadata.py  ·  canvas 1100")

# ---- Panel 1: the seam -----------------------------------------------------
y0 = 120
P1_H = 196
d.panel(y0, P1_H, 1, "A thin seam over native Model Runner V2",
        "The AFD class overrides construction/lifecycle methods and delegates the work to super().")

by = y0 + 66
d.box(46, by, 500, 112, "AFDAttentionModelRunnerV2  (overrides)",
      ["__init__        make the connector (:369-411)",
       "load_model      init connector at the end (:454-462)",
       "initialize_kv_cache   DP1 ubatch (:473-486)",
       "capture_model   graph warm-up/capture (:509-553)",
       "execute_model   wrap + delegate (:569-595)"],
      col=BLUE, align="left")
d.box(620, by, 434, 112, "native GPUModelRunnerV2  (super)",
      ["request state + input prep",
       "attention + KV cache",
       "the model forward",
       "logits + sampling, every step",
       "ModelRunnerOutput"],
      col=NEUTRAL, align="left")
d.arrow(546, by + 56, 618, by + 56, BLUE)
d.arrow_label(582, by + 48, "delegates", BLUE)

# ---- Panel 2: two control-plane publish paths ------------------------------
y2 = y0 + P1_H + 22
P2_H = 182
d.panel(y2, P2_H, 2, "Control plane: once per step, before the layer loop",
        "One of two seams publishes the DP metadata. The data plane then runs once per layer and stage.")

d.box(46, y2 + 64, 470, 56, "DBO path: ubatch prepare seam",
      ["send_dp_metadata(None, slices)", "attention_model_runner_v2.py:156-157"],
      col=VIOLET, align="left")
d.box(46, y2 + 128, 470, 40, "non-DBO path: forward-context provider",
      ["install_afd_metadata_on_forward_context :248-257"], col=VIOLET, align="left")
d.box(640, y2 + 86, 414, 60, "control_plane.send_dp_metadata_list",
      ["update_state_from_dp_metadata", "then send  (attention_metadata.py:115-116)"],
      col=BLUE, align="left")
d.arrow(516, y2 + 92, 638, y2 + 108, VIOLET)
d.arrow(516, y2 + 148, 638, y2 + 124, VIOLET)

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "AFD / control send"), (VIOLET, "publish seam"),
                 (NEUTRAL, "native vLLM")])
y += 34
y = d.footnotes(30, y,
                ["execute_model opens _use_afd_execution_context (:582), which scopes the metadata "
                 "provider, DBO dispatch, and FULL-graph replay hook, then calls super (:586).",
                 "Sampling is native and runs once per step after the last layer, on the attention side."])
d.save(height=y + 14)
