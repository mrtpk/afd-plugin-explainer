"""Life of a request, half 1: the attention server.

Used by: src/tours/life-of-a-request.html (<x-diagram name="s2_request_attention" />)
Sources (afd-plugin / vLLM at the pinned commits in explainer.json):
  README.md:258-260                                    requests go only to the attention API server
  vllm/v1/engine/core.py                               native EngineCore + scheduler (attention side)
  afd_plugin/v1/worker/attention_worker.py:60-88       AFDAttentionWorker.init_device selects the runner
  afd_plugin/v1/worker/attention_model_runner_v2.py:570-594  execute_model wraps native MRV2
  afd_plugin/v1/worker/attention_model_runner_v2.py:156-157  control-plane publish from the prepare seam
  afd_plugin/v1/worker/attention_metadata.py:115-116   send_dp_metadata -> update_state + send
  afd_plugin/model_executor/models/deepseek_v2.py:146  RemoteFFNProxy.send_attn_output
  afd_plugin/model_executor/models/deepseek_v2.py:155  RemoteFFNProxy.recv_ffn_output
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, VIOLET, EMERALD, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Life of a request - the attention server",
         "One step on a 2A2F GPU recipe (one attention server, one FFN server, P2P connector). Follow rank A0.",
         params="afd_plugin/v1/worker/  ·  model_executor/models/deepseek_v2.py  ·  canvas 1100")

y0 = 120
P_H = 546
d.panel(y0, P_H, 1, "How does one request reach the connector?",
        "vLLM native code carries the request to the AFD runner; the plugin publishes metadata, then sends per layer.")

x = 60
w = 440
h = 52
gap = 26
top = y0 + 64

steps = [
    ("1", "HTTP request -> attention API server", "vLLM", "requests go only here (README.md:258)"),
    ("2", "EngineCore + scheduler", "vLLM", "attention side only; no FFN scheduler"),
    ("3", "executor -> AFDAttentionWorker", "afd", "attention_worker.py:60"),
    ("4", "AFDAttentionModelRunnerV2.execute_model", "afd", "attention_model_runner_v2.py:570"),
    ("5", "control-plane publish (DP metadata)", "afd", "attention_metadata.py:115-116"),
    ("6", "decoder layer: attention, then FFN proxy", "afd", "deepseek_v2.py:146,155"),
]

ys = []
for i, (num, title, tag, cite) in enumerate(steps):
    yy = top + i * (h + gap)
    ys.append(yy)
    col = BLUE if tag == "vLLM" else (VIOLET if num == "5" else EMERALD if num == "6" else BLUE)
    tcol = NEUTRAL if tag == "vLLM" else col
    d.step_card(x, yy, w, h, num, title, col, tag=tag, rows=[("", cite)])
    if i > 0:
        d.arrow(x + w / 2, ys[i - 1] + h, x + w / 2, yy - 2, MUTE)

# frequency annotations on the right
ax = x + w + 70
# control plane: once per step
cp_y = ys[4] + h / 2
d.arrow(x + w + 2, cp_y, ax - 2, cp_y, VIOLET)
d.callout(ax, cp_y - 17, 440, "once per step:",
          "before the layer loop, to the FFN server", VIOLET)
# layer loop: once per layer and stage
ll_y = ys[5] + h / 2
d.arrow(x + w + 2, ll_y, ax - 2, ll_y, EMERALD)
d.callout(ax, ll_y - 17, 440, "per layer and stage:",
          "send hidden states, receive FFN output", EMERALD)
# loop-back note under the last box
d.text(ax, ll_y + 36, "With DBO there are two stages per layer.", 12, MUTE, italic=True)
d.text(ax, ll_y + 54, "The connector crosses to the FFN server.", 12, MUTE, italic=True)

y = y0 + P_H + 22
d.legend(30, y, [(BLUE, "vLLM native"), (VIOLET, "control plane (DP metadata)"),
                 (EMERALD, "data plane (hidden states)")])
y += 40
y = d.footnotes(30, y, [
    "Simplified: one attention rank (A0). Left out: KV cache, sampling (after the last layer), the per-peer split, CUDA graphs.",
    "Native logits and sampling run after the last layer, on the attention side (not shown here).",
])
d.save(height=y + 14)
