"""The order of steps inside register_afd().

Used by: src/code/init-py.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/__init__.py:150-153   guard: if _registered -> return
  afd_plugin/__init__.py:155       _force_spawn_multiprocessing_if_requested()
  afd_plugin/__init__.py:157-160   vLLM not importable -> set _registered, return
  afd_plugin/__init__.py:162-165   assert_vllm_version_supported(strict=False)
  afd_plugin/__init__.py:172-176   import the 4 compat patch modules
  afd_plugin/__init__.py:183-187   register_afd_balanced_routing_strategy()
  afd_plugin/__init__.py:189-192   register_dbo_yield_custom_op()
  afd_plugin/__init__.py:202-209   NPU only: apply_afd_ascend_config_patch()
  afd_plugin/__init__.py:211-214   ModelRegistry.register_model for each AFD<arch>
  afd_plugin/__init__.py:216       _registered = True
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, VIOLET, AMBER, NEUTRAL, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("What register_afd() does, in order",
         "The entry point runs safety checks first, then the registration steps.",
         params="afd_plugin/__init__.py:142-216  ·  one call per process")

cx, cw = 80, 940
pitch = 68
ch = 58

# ---- Panel 1: safety -----------------------------------------------------
y0 = 128
P1_H = 348
d.panel(y0, P1_H, 1, "Safety first (before any registration)",
        "Any of these steps can return early, so registration never runs on a bad setup.")
cy = y0 + 64
d.step_card(cx, cy + 0 * pitch, cw, ch, 1, "Guard: already registered?", NEUTRAL,
            tag="__init__.py:150-153", rows=[("if", "_registered -> return")])
d.step_card(cx, cy + 1 * pitch, cw, ch, 2, "Force spawn start method, if requested", NEUTRAL,
            tag="__init__.py:155", rows=[("env", "AFD_FORCE_SPAWN_MULTIPROCESSING == 1")])
d.step_card(cx, cy + 2 * pitch, cw, ch, 3, "Is vLLM importable?", AMBER,
            tag="__init__.py:157-160", rows=[("if not", "set _registered = True, then return")])
d.step_card(cx, cy + 3 * pitch, cw, ch, 4, "Check the vLLM version", AMBER,
            tag="__init__.py:162-165", rows=[("call", "assert_vllm_version_supported(strict=False)")])

# ---- Panel 2: registration -----------------------------------------------
y2 = y0 + P1_H + 22
P2_H = 480
d.panel(y2, P2_H, 2, "Then register (vLLM is present)",
        "These steps run in this order; step 8 runs only on NPU.")
ry = y2 + 64
d.step_card(cx, ry + 0 * pitch, cw, ch, 5, "Import the 4 compat patch modules", BLUE,
            tag="__init__.py:172-176", rows=[("imports", "async_dp_engine, async_dp_forward_context, ...")])
d.step_card(cx, ry + 1 * pitch, cw, ch, 6, "Register the AFD routing strategy", BLUE,
            tag="__init__.py:183-187", rows=[("call", "register_afd_balanced_routing_strategy()")])
d.step_card(cx, ry + 2 * pitch, cw, ch, 7, "Register the DBO yield custom op", BLUE,
            tag="__init__.py:189-192", rows=[("call", "register_dbo_yield_custom_op()")])
d.step_card(cx, ry + 3 * pitch, cw, ch, 8, "NPU only: apply the Ascend config patch", VIOLET,
            tag="__init__.py:202-209", rows=[("if", "current_platform.device_type == \"npu\"")])
d.step_card(cx, ry + 4 * pitch, cw, ch, 9, "Register each AFD<arch> model", BLUE,
            tag="__init__.py:211-214", rows=[("loop", "ModelRegistry.register_model(\"AFD\"+arch, cls)")])
d.step_card(cx, ry + 5 * pitch, cw, ch, 10, "Mark the process done", EMERALD,
            tag="__init__.py:216", rows=[("set", "_registered = True")])

# ---- legend + footnotes ---------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "always (vLLM present)"), (VIOLET, "NPU only"),
                 (AMBER, "check / early exit"), (EMERALD, "done")])
y += 36
y = d.footnotes(30, y,
                ["Steps 4, 5 and 7 are wrapped in try/except; a failure is logged and does not stop the rest (__init__.py:162-197).",
                 "_force_spawn_multiprocessing_if_requested also runs once at package import time (__init__.py:94)."])
d.save(height=y + 14)
