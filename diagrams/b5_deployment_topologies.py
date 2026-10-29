"""AFD deployment topologies: colocation, disaggregation, multipod.

Used by: src/concepts/deployment-topologies.html
Sources (at the pinned commit in explainer.json):
  recipe/.../prefill_decode_colocation/2a2f_graph_dbo_dp1tp2.sh:7-32   2A2F
  recipe/.../prefill_decode_disaggregation/2p1a1f_eager_dbo.sh:22-125  2P1A1F + proxy
  recipe/.../qwen3_5_122b_a10b_fp8/.../multipod_2a_2a_2f_graph.sh:31-98 multipod 4A2F
  afd_plugin/validation.py:107-117   role ranks == DP * TP
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, INK, MUTE, NEUTRAL, VIOLET, AMBER, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header(
    "AFD deployment topologies",
    "One model, two or more vllm serve processes  ·  topology name xAyF  ·  GPU P2P connector",
    params="role ranks == DP * TP   ·   num_attention_ranks >= num_ffn_ranks",
)

y = 112

# --- Panel 1: colocation 2A2F --------------------------------------------
P1 = 176
d.panel(y, P1, 1, "Colocation (2A2F): two servers, four GPUs",
        "One attention server and one FFN server. A0->F0, A1->F1 over AFD port 6269.")
by = y + 70
d.box(46, by, 440, 80, "Attention server", [
    "role=attention  ·  GPUs 0,1",
    "DP1 TP2 -> ranks A0, A1",
    "HTTP 18305  ·  --enable-dbo",
], col=BLUE, align="left")
d.arrow(486, by + 40, 612, by + 40, NEUTRAL)
d.arrow_label(549, by + 40, "connector", MUTE)
d.box(614, by, 440, 80, "FFN server", [
    "role=ffn  ·  GPUs 2,3",
    "DP1 TP2 -> ranks F0, F1",
    "HTTP 18305  ·  no real scheduler, no KV",
], col=EMERALD, align="left")
y += P1 + 20

# --- Panel 2: disaggregation 2P1A1F --------------------------------------
P2 = 212
d.panel(y, P2, 2, "Disaggregation (2P1A1F): add prefillers and a proxy",
        "Five processes. The proxy prefills on a prefiller, then the decode pair (attention + FFN) decodes.")
by = y + 70
d.box(46, by, 320, 56, "Proxy (tools/proxy_server.py)", [
    "client endpoint  ·  HTTP 18305",
], col=VIOLET, align="left")
d.box(382, by, 320, 56, "2 prefillers", [
    "GPU0, GPU1  ·  NIXL kv_producer",
], col=NEUTRAL, align="left")
d.box(718, by, 336, 56, "Decode attention", [
    "GPU2  ·  role=attention  ·  18303",
], col=BLUE, align="left")
by2 = by + 76
d.arrow(886, by + 56, 886, by2, NEUTRAL)
d.box(718, by2, 336, 52, "Decode FFN", [
    "GPU3  ·  role=ffn  ·  18304",
], col=EMERALD, align="left")
d.callout(46, by2, 656, "Not the A/F split:",
          "the proxy and prefillers handle prefill/decode (NIXL KV), not attention/FFN.", VIOLET, h=52)
y += P2 + 20

# --- Panel 3: multipod ---------------------------------------------------
P3 = 168
d.panel(y, P3, 3, "Multipod (k8s): one pod per role, gated on POD",
        "Each vllm serve is wrapped in if [ \"$POD\" == ... ]. With POD unset, nothing runs.")
by = y + 70
d.box(46, by, 320, 70, "2A2F multipod", [
    "POD=ATTENTION_0 | FFN_0",
    "DP1 TP2 each  ·  2 pods",
], col=BLUE, align="left")
d.box(382, by, 340, 70, "Qwen3.5 122B FP8 (4A2F)", [
    "ATTENTION_0 + ATTENTION_1 + FFN_0",
    "DP4 (DP2 local x2) / DP2  ·  3 pods",
], col=EMERALD, align="left")
d.box(738, by, 316, 70, "The rule", [
    "attention: A = DP x TP",
    "ffn: F = DP x TP  ·  A >= F",
], col=AMBER, align="left")
y += P3 + 24

d.legend(30, y, [
    (BLUE, "attention role"), (EMERALD, "FFN role"),
    (VIOLET, "prefill/decode proxy"), (AMBER, "validation rule"),
    (NEUTRAL, "non-AFD / neutral"),
])
y += 40
y = d.footnotes(30, y, [
    "Eager variants pass --enforce-eager; graph variants pass --compilation-config cudagraph_mode=FULL_DECODE_ONLY.",
    "Start order: launch both roles, wait for 'Application startup complete' in each log, then send traffic to the attention HTTP port.",
])
d.save(height=y + 14)
