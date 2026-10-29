"""What afd-plugin lets you tune, grouped by goal.

Used by: src/concepts/tuning.html
Sources (at the pinned commit in explainer.json):
  afd_plugin/distributed/topology.py:52-58     A >= F
  recipe/.../2a2f_graph_dbo_dp1tp2.sh:24-29     DBO 2/12, capture 64
  vllm:vllm/config/parallel.py:227,232          vLLM DBO defaults 32/512
  afd_plugin/config.py:66,70                     gate, timeout
  afd_plugin/validation.py:45-54                 BATCH_SIZE_FACTOR
  afd_plugin/model_executor/routing_simulator.py:26-28,122   routing simulator
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, AMBER, TEAL, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header(
    "What you can tune in AFD",
    "Only knobs the repo exposes  ·  recipe values are examples to tune, not tuned defaults",
    params="A >= F   ·   DBO recipe 2/12 vs vLLM 32/512   ·   capture 64",
)

CW = 320  # card width
X = [46, 382, 718]

y = 112
P1 = 150
d.panel(y, P1, 1, "Tune throughput", "The split, the overlap and the graph size.")
cy = y + 62
d.step_card(X[0], cy, CW, 74, 1, "Rank ratio A:F", BLUE, tag="A >= F", rows=[
    ("rule", "A = DP x TP"),
    ("src", "topology.py:52"),
])
d.step_card(X[1], cy, CW, 74, 2, "DBO thresholds", BLUE, tag="2 / 12", rows=[
    ("vLLM", "32 / 512 default"),
    ("recipe", "dbo *_token_threshold"),
])
d.step_card(X[2], cy, CW, 74, 3, "CUDA graph size", BLUE, tag="64", rows=[
    ("flag", "max-cudagraph-capture-size"),
    ("mode", "FULL_DECODE_ONLY"),
])
y += P1 + 20

P2 = 150
d.panel(y, P2, 2, "Tune reliability and placement", "Timeouts, the gate, and NPU capacity.")
cy = y + 62
d.step_card(X[0], cy, CW, 74, 4, "Group timeout", AMBER, tag="120 s", rows=[
    ("key", "afd_process_group_timeout_s"),
    ("src", "config.py:70"),
])
d.step_card(X[1], cy, CW, 74, 5, "Gate placement", AMBER, tag="false", rows=[
    ("key", "compute_gate_on_attention"),
    ("src", "config.py:66"),
])
d.step_card(X[2], cy, CW, 74, 6, "NPU CAM capacity", AMBER, tag="x1", rows=[
    ("env", "BATCH_SIZE_FACTOR"),
    ("src", "validation.py:45"),
])
y += P2 + 20

P3 = 150
d.panel(y, P3, 3, "Measure", "Profile, simulate routing, benchmark.")
cy = y + 62
d.step_card(X[0], cy, CW, 74, 7, "Profiler", TEAL, tag="opt-in", rows=[
    ("env", "AFD_GPU_*_PROFILER_*"),
    ("src", "compat/profiler.py"),
])
d.step_card(X[1], cy, CW, 74, 8, "Routing simulator", TEAL, tag="afd_balanced", rows=[
    ("env", "VLLM_MOE_ROUTING_SIM..."),
    ("src", "routing_simulator.py"),
])
d.step_card(X[2], cy, CW, 74, 9, "Benchmark", TEAL, tag="bench serve", rows=[
    ("tool", "request_generator.sh"),
    ("k8s", "run-vllm-bench-k8s"),
])
y += P3 + 24

d.legend(30, y, [
    (BLUE, "throughput"), (AMBER, "reliability / placement"), (TEAL, "measurement"),
])
y += 40
y = d.footnotes(30, y, [
    "The recipe DBO thresholds (2/12) and capture size (64) are example values; the READMEs say to tune them.",
    "The routing simulator and the forced top-n change model outputs: use it only for benchmarks.",
])
d.save(height=y + 14)
