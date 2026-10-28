"""How one AFD config key gets its final value.

Used by: src/reference/afd-config.html (<x-diagram name="s2_config_resolution" />)
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/config.py:32-38      alias map (_ALIASES)
  afd_plugin/config.py:120-176    _normalize_mapping (alias + coercion)
  afd_plugin/config.py:62,64      num_attention_ranks / num_ffn_ranks defaults
  afd_plugin/config.py:189-190    AFDConfig(**normalized)
  afd_plugin/config.py:311-350    validate_afd_config
  afd_plugin/distributed/topology.py:52-58  validate_p2p_topology (A >= F)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, VIOLET, EMERALD, AMBER, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Where an AFD config value is finally set",
         "Example key: num_attention_ranks. The recipe value is coerced, then stored, then validated.",
         params="afd_plugin/config.py  ·  distributed/topology.py  ·  canvas 1100")

y0 = 120
P_H = 196
d.panel(y0, P_H, 1, "Trace one key from the recipe to the validated config",
        "A missing key takes the dataclass default; a present key is coerced to its type.")

bw, bh = 230, 84
yy = y0 + 70
xs = [24, 289, 554, 819]
boxes = [
    ("recipe JSON", ["num_attention_ranks: 2", "config.py:189"], BLUE),
    ("_normalize_mapping", ["alias + coerce_int", "config.py:120-176"], VIOLET),
    ("AFDConfig field", ["default 1 if absent", "config.py:62"], EMERALD),
    ("validate_afd_config", ["must be > 0; A >= F", "config.py:343 / topology.py:52"], AMBER),
]
for i, (title, lines, col) in enumerate(boxes):
    d.box(xs[i], yy, bw, bh, title, lines, col=col)
    if i > 0:
        d.arrow(xs[i - 1] + bw + 2, yy + bh / 2, xs[i] - 2, yy + bh / 2, MUTE)

y = y0 + P_H + 22
d.legend(30, y, [(BLUE, "deployment value"), (VIOLET, "alias + coercion"),
                 (EMERALD, "dataclass default"), (AMBER, "validation")])
y += 40
y = d.footnotes(30, y, [
    "The alias map (config.py:32-38) rewrites afd_role -> role, async -> async_dp, and so on before coercion.",
    "Only P2pNcclAFDConnector adds the A >= F check (topology.py:52-58); every connector gets the other checks.",
])
d.save(height=y + 14)
