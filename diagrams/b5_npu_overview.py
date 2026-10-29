"""Ascend NPU: same AFD contract, two CAM transports.

Used by: src/concepts/npu-overview.html
Sources (at the pinned commit in explainer.json):
  afd_plugin/connectors/npu/camp2p.py:6-8,385,418-431,460-468   CAMP2p: HCCL data + Gloo control plane
  afd_plugin/connectors/npu/async_cam.py:277-283          CAMAsync: no control plane
  afd_plugin/v1/worker/npu/async_ffn_model_runner.py:442-446  receive loop drives FFN
  afd_plugin/compat/npu/ops.py:73-91                       operator loader
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, TEAL, NEUTRAL, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header(
    "Ascend NPU: same contract, two CAM transports",
    "Same attention/FFN split as GPU  ·  different connectors  ·  compiled Ascend extension loaded by the plugin",
    params="CAMP2pAFDConnector (sync)   ·   CAMAsyncAFDConnector (async)",
)

y = 112

# Panel 1: same contract
P1 = 150
d.panel(y, P1, 1, "The AFD contract is unchanged",
        "The attention role sends hidden states; the FFN role computes experts and sends the result back.")
by = y + 70
d.box(46, by, 430, 62, "Attention role (NPU)", [
    "send hidden states -> recv FFN output",
], col=BLUE, align="left")
d.arrow(476, by + 31, 612, by + 31, NEUTRAL)
d.arrow_label(544, by + 31, "CAM", NEUTRAL)
d.box(614, by, 440, 62, "FFN role (NPU)", [
    "recv -> experts -> send output",
], col=EMERALD, align="left")
y += P1 + 20

# Panel 2: CAMP2p sync
P2 = 162
d.panel(y, P2, 2, "CAMP2pAFDConnector: synchronous, with a control plane",
        "HCCL carries the hidden states; a smaller Gloo group carries DP metadata once per step.")
by = y + 70
d.box(46, by, 460, 70, "Data plane (HCCL)", [
    "CAMP2p custom ops over HCCL",
    "camp2p.py:418  ·  one group per batch",
], col=EMERALD, align="left")
d.box(560, by, 494, 70, "Control plane (Gloo)", [
    "CAMP2pAFDControlPlane  ·  camp2p.py:385",
    "token counts, once per step",
], col=VIOLET, align="left")
y += P2 + 20

# Panel 3: CAMAsync
P3 = 168
d.panel(y, P3, 3, "CAMAsyncAFDConnector: asynchronous, no control plane",
        "CAM dispatch/combine carry the routing metadata, so control_plane is None and the receive loop drives FFN.")
by = y + 70
d.box(46, by, 320, 74, "control_plane = None", [
    "async_cam.py:283",
    "no DP metadata path",
], col=NEUTRAL, align="left")
d.arrow(366, by + 37, 462, by + 37, TEAL)
d.box(464, by, 300, 74, "recv_ffn_work_item", [
    "layer_idx from CAM",
    "async_ffn_...:443",
], col=TEAL, align="left")
d.arrow(764, by + 37, 860, by + 37, EMERALD)
d.box(862, by, 192, 74, "compute + send", [
    "per layer",
], col=EMERALD, align="left")
y += P3 + 24

d.legend(30, y, [
    (BLUE, "attention role"), (EMERALD, "FFN role / data plane"),
    (VIOLET, "control plane"), (TEAL, "async receive loop"),
])
y += 40
y = d.footnotes(30, y, [
    "Out of scope: the CAM kernel internals. The plugin loads its compiled Ascend extension (afd_plugin._C_ascend, built by setup.py) and asserts the torch.ops.afd_ascend namespace (ops.py:73-91).",
    "The async receive loop reads each layer index from CAM metadata, so no separate control plane is needed.",
])
d.save(height=y + 14)
