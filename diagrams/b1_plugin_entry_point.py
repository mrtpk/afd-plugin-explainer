"""register_afd: two guards and three early exits.

Used by: src/concepts/plugin-entry-point.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/__init__.py:150-153   guard: if _registered -> return
  afd_plugin/__init__.py:157-160   find_spec("vllm") is None -> set, return
  afd_plugin/__init__.py:162-170   version check, try/except, strict=False
  afd_plugin/compat/vllm.py:48-50  strict=False warns instead of raising
  vllm/plugins/__init__.py:82-85   vLLM guard plugins_loaded (one per process)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import TEAL, NEUTRAL, AMBER, EMERALD, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("register_afd: safe to call many times",
         "Two guards stop repeated work in one process; three checks can return before anything is registered.",
         params="afd_plugin/__init__.py:142-216  ·  compat/vllm.py:38-50")

# ---- Panel 1: the two guards ---------------------------------------------
y0 = 120
P1_H = 186
d.panel(y0, P1_H, 1, "Two guards: one in vLLM, one in the plugin",
        "Each guard is module state, so a new process starts it at False and the plugin runs again.")
by = y0 + 74
d.box(70, by, 400, 92, "vLLM load_general_plugins", [
    "guard: plugins_loaded",
    "one run per process"], NEUTRAL)
d.arrow(474, by + 46, 638, by + 46, MUTE, sw=2)
d.arrow_label(556, by + 46, "calls the entry point", MUTE)
d.box(640, by, 400, 92, "register_afd()", [
    "guard: _registered",
    "returns on a second call"], TEAL)

# ---- Panel 2: three early exits ------------------------------------------
y2 = y0 + P1_H + 20
pitch = 76
ch = 60
P2_H = 64 + 3 * pitch - (pitch - ch) + 6
d.panel(y2, P2_H, 2, "Three checks run before any registration",
        "Any one can return early, so registration never runs on a bad setup.")
cy = y2 + 60
d.step_card(70, cy + 0 * pitch, 960, ch, 1, "Already registered in this process?", AMBER,
            tag="__init__.py:150-153", key_w=46,
            rows=[("if", "_registered is True  ->  return at once")])
d.step_card(70, cy + 1 * pitch, 960, ch, 2, "Is vLLM importable? (import safety)", AMBER,
            tag="__init__.py:157-160", key_w=46,
            rows=[("if not", "set _registered = True, then return")])
d.step_card(70, cy + 2 * pitch, 960, ch, 3, "Does the vLLM version match 0.30.0?", AMBER,
            tag="__init__.py:162-170", key_w=46,
            rows=[("no", "warn only (strict=False), then go on", EMERALD)])

y = y2 + P2_H + 18
d.legend(30, y, [(NEUTRAL, "vLLM"), (TEAL, "the plugin entry"), (AMBER, "check / early exit"),
                 (EMERALD, "warn, do not stop")])
y += 34
y = d.footnotes(30, y,
                ["After the checks: import the 4 patches, register the routing strategy, the DBO op, the "
                 "NPU-only Ascend patch, then each AFD<arch> model (__init__.py:172-214).",
                 "try/except wraps the version check, the patch imports and the DBO op; not the routing "
                 "strategy, the NPU patch or the model loop."])
d.save(height=y + 12)
