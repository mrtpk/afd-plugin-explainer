"""Anatomy of the 2a2f_graph_dbo_dp1tp2 recipe.

Used by: src/tours/run-a-recipe.html
Sources (at the pinned commit in explainer.json):
  recipe/.../prefill_decode_colocation/2a2f_graph_dbo_dp1tp2.sh:5,7-32,34-59,61
  README.md:258-260   send requests only to the attention server
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, AMBER, NEUTRAL, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header(
    "Anatomy of one recipe: 2a2f_graph_dbo_dp1tp2.sh",
    "One attention server and one FFN server, DP1 TP2, graph + DBO  ·  same --additional-config, role differs",
    params="VLLM_USE_V2_MODEL_RUNNER=1   ·   AFD port 6269   ·   HTTP 18305",
)

y = 112

# Panel 1: the two serve commands
P1 = 212
d.panel(y, P1, 1, "Two vllm serve processes",
        "Both set the same afd block; only role and GPUs differ.")
by = y + 66
d.step_card(46, by, 494, 128, 1, "Attention server", BLUE, tag="role=attention", rows=[
    ("env", "VLLM_USE_V2_MODEL_RUNNER=1"),
    ("gpu", "CUDA_VISIBLE_DEVICES=0,1"),
    ("par", "--data-parallel-size 1 --tensor-parallel-size 2"),
    ("afd", "connector=P2pNcclAFDConnector 6269"),
    ("gfx", "cudagraph_mode=FULL_DECODE_ONLY"),
    ("http", "--port 18305  (clients connect here)"),
])
d.step_card(560, by, 494, 128, 2, "FFN server", EMERALD, tag="role=ffn", rows=[
    ("gpu", "CUDA_VISIBLE_DEVICES=2,3"),
    ("par", "--data-parallel-size 1 --tensor-parallel-size 2"),
    ("afd", "same host:port 6269, same ranks 2/2"),
    ("dbo", "--enable-dbo  2 / 12"),
    ("gfx", "cudagraph_mode=FULL_DECODE_ONLY"),
    ("note", "no scheduler, no KV, no client traffic"),
])
y += P1 + 20

# Panel 2: start order + traffic
P2 = 150
d.panel(y, P2, 2, "Start order and traffic",
        "Background both, wait for startup, then send requests to the attention port only.")
by = y + 68
d.box(46, by, 240, 56, "1. Background both", ["attn.log / ffn.log", "then wait"], col=NEUTRAL, align="left")
d.arrow(286, by + 28, 330, by + 28, NEUTRAL)
d.box(332, by, 260, 56, "2. Wait for startup", ["'Application startup", "complete' in each log"], col=AMBER, align="left")
d.arrow(592, by + 28, 636, by + 28, NEUTRAL)
d.box(638, by, 416, 56, "3. Send to attention 18305", ["vllm bench serve  ·  README:258", "never to the FFN server"], col=BLUE, align="left")
y += P2 + 24

d.legend(30, y, [
    (BLUE, "attention role / client traffic"), (EMERALD, "FFN role"),
    (AMBER, "wait condition"), (NEUTRAL, "shell step"),
])
y += 40
y = d.footnotes(30, y, [
    "Every claim is on the page with a line citation from the recipe script.",
    "The eager variant replaces the graph flags with --enforce-eager.",
])
d.save(height=y + 14)
