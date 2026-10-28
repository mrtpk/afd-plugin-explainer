"""Compat patches: two version checks, then five GPU patch modules.

Used by: src/concepts/compat-patches.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/__init__.py:162-181            version check, then 4 patch imports
  afd_plugin/compat/vllm.py:38-50,53-68     strict check vs install gate
  afd_plugin/compat/patches/config_validation.py:235-261  install gate + guards
  afd_plugin/compat/patches/engine_core.py:722-727        install gate
  afd_plugin/compat/patches/gpu_mrv2_ubatching.py:263-283 scoped context managers
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, AMBER, VIOLET, EMERALD, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("How AFD patches vLLM",
         "AFD changes no vLLM source. register_afd imports patch modules that replace vLLM functions in place, behind a version gate.",
         params="__init__.py  ·  compat/vllm.py  ·  compat/patches/  ·  canvas 1100")

# ---- Panel 1: two version checks -------------------------------------------
y0 = 124
P1_H = 150
d.panel(y0, P1_H, 1, "Two separate version checks",
        "The start-up check only warns; each patch module has its own install gate (compat/vllm.py).")

cy = y0 + 66
d.box(46, cy, 500, 56, "assert_vllm_version_supported(strict=False)",
      ["warns if not exactly 0.30.0  (vllm.py:38-50)"], col=AMBER, align="left")
d.box(580, cy, 474, 56, "is_target_vllm_compatible()  = version gate",
      ["allows 0.30.0 + dev builds  (vllm.py:53-68)"], col=EMERALD, align="left")

# ---- Panel 2: the five GPU patch modules -----------------------------------
y2 = y0 + P1_H + 20
P2_H = 250
d.panel(y2, P2_H, 2, "Five GPU patch modules, imported by register_afd",
        "Install style differs: import-time method swap, or a scoped context manager (__init__.py:172-181).")

col_w = 335
gap = 20
x1 = 46
x2 = x1 + col_w + gap
x3 = x2 + col_w + gap
ry = y2 + 70
d.box(x1, ry, col_w, 60, "config_validation",
      ["create_engine_config +", "__post_init__  (import-time)"], col=BLUE, align="left")
d.box(x2, ry, col_w, 60, "engine_core",
      ["FFN EngineCore + busy loop", "(import-time)"], col=BLUE, align="left")
d.box(x3, ry, col_w, 60, "gpu_mrv2_ubatching",
      ["DP1 DBO seams", "(scoped context managers)"], col=VIOLET, align="left")

ry2 = ry + 76
d.box(x1, ry2, col_w, 60, "async_dp_engine",
      ["EngineCoreProc selection", "(import-time, NPU async only)"], col=NEUTRAL, align="left")
d.box(x2, ry2, col_w, 60, "async_dp_forward_context",
      ["set_forward_context", "(import-time, NPU async only)"], col=NEUTRAL, align="left")
d.box(x3, ry2, col_w, 60, "NPU patches (npu/*)",
      ["Ascend config, platform, MLA", "(device_type == npu only)"], col=NEUTRAL, align="left")

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "GPU, import-time"), (VIOLET, "GPU, scoped"),
                 (NEUTRAL, "runtime- or device-gated")])
y += 34
y = d.footnotes(30, y,
                ["On a non-matching, non-dev vLLM the install gate skips every patch. worker_cls is never "
                 "rewritten and AFD does not take effect.",
                 "async_dp patches install at import time but only change behavior for async configs, which "
                 "are NPU only (async_dp must be false on GPU)."])
d.save(height=y + 14)
