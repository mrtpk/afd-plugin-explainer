"""How additional_config['afd'] becomes a validated AFDConfig.

Used by: src/concepts/afd-config.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/config.py:227-234   read the 'afd' key from additional_config
  afd_plugin/config.py:120-176   _normalize_mapping: aliases + coercion
  afd_plugin/config_utils.py:35-45   coerce_extra_int rejects bool and float
  afd_plugin/config.py:190       AFDConfig(**normalized, connector_extra_config=...)
  afd_plugin/config.py:311-350   validate_afd_config
  afd_plugin/config.py:289-292   is_afd_active: present and valid
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, TEAL, AMBER, NEUTRAL, EMERALD, PINK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("From a dict to a validated AFDConfig",
         "The plugin reads one key, renames aliases, coerces types, builds the dataclass, then validates it.",
         params="afd_plugin/config.py:120-350  ·  config_utils.py:35-54")

# ---- Panel 1: the pipeline -----------------------------------------------
y0 = 120
pitch = 74
ch = 58
n = 5
P1_H = 60 + n * pitch - (pitch - ch) + 6
d.panel(y0, P1_H, 1, "The parse pipeline",
        "One function, afd_config_from_mapping, runs these steps in order (config.py:179-194).")
cy = y0 + 58
x, w = 60, 980
d.step_card(x, cy + 0 * pitch, w, ch, 1, "Read the 'afd' key", NEUTRAL,
            tag="config.py:227-234", key_w=42,
            rows=[("in", 'additional_config["afd"] mapping')])
d.step_card(x, cy + 1 * pitch, w, ch, 2, "Normalize: apply aliases, pull out extra config", BLUE,
            tag="config.py:120-146", key_w=42,
            rows=[("map", "afd_connector->connector, async->async_dp, ...")])
d.step_card(x, cy + 2 * pitch, w, ch, 3, "Coerce types (reject bool/float as int)", BLUE,
            tag="config.py:147-174", key_w=42,
            rows=[("int", "port, num_attention_ranks, num_ffn_ranks")])
d.step_card(x, cy + 3 * pitch, w, ch, 4, "Build the frozen dataclass", TEAL,
            tag="config.py:190", key_w=42,
            rows=[("new", "AFDConfig(**normalized, connector_extra_config)")])
d.step_card(x, cy + 4 * pitch, w, ch, 5, "Validate values", AMBER,
            tag="config.py:311-350", key_w=42,
            rows=[("check", "role, connector, host, port, rank counts")])

# ---- Panel 2: active iff the key is present ------------------------------
y2 = y0 + P1_H + 20
P2_H = 150
d.panel(y2, P2_H, 2, "AFD is active only when the 'afd' key is present",
        "No key means parse returns None, and AFD stays off (config.py:244-292).")
by = y2 + 70
d.box(70, by, 430, 60, "'afd' key present", ["parse + validate  ->  AFDConfig"], EMERALD,
      align="left")
d.box(600, by, 430, 60, "'afd' key absent", ["parse returns None  ->  AFD off"], PINK,
      align="left")

y = y2 + P2_H + 18
d.legend(30, y, [(NEUTRAL, "input"), (BLUE, "transform"), (TEAL, "build"), (AMBER, "validate")])
y += 34
y = d.footnotes(30, y,
                ["coerce_extra_int rejects bool and float, so 1.0 or True for an int field raises "
                 "(config_utils.py:35-45).",
                 "connector_extra_config is kept aside and parsed later by each connector."])
d.save(height=y + 12)
