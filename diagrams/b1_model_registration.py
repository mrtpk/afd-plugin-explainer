"""How AFD registers model wrappers and swaps the model identity.

Used by: src/concepts/model-registration.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/__init__.py:96-139    _MODEL_REGISTRATIONS: arch -> "module:Class"
  afd_plugin/__init__.py:211-214   loop: register_model("AFD"+arch, lazy string)
  afd_plugin/model_executor/models/model_utils.py:16-22   has_afd_model_registration
  afd_plugin/model_executor/models/model_utils.py:25-46   get_afd_model_config
Sources (vLLM at extra_repos.vllm):
  vllm/model_executor/models/registry.py:1126-1141   lazy "module:Class" form
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, TEAL, EMERALD, NEUTRAL, VIOLET, PINK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Registering AFD model wrappers",
         "Each base architecture name is registered as AFD<arch>, as a lazy string, then swapped in at build time.",
         params="afd_plugin/__init__.py:96-214  ·  model_utils.py:16-46")

# ---- Panel 1: register the names -----------------------------------------
y0 = 118
P1_H = 150
d.panel(y0, P1_H, 1, "At plugin load: register each AFD<arch> name",
        "The value is a 'module:Class' string, so vLLM imports the class only when it is needed.")
by = y0 + 70
d.box(60, by, 430, 60, "_MODEL_REGISTRATIONS", ['arch -> "module:Class"'], NEUTRAL, align="left")
d.arrow(494, by + 30, 598, by + 30, MUTE, sw=2)
d.arrow_label(546, by + 30, 'AFD + arch', MUTE)
d.box(600, by, 440, 60, "ModelRegistry.register_model", ['("AFD"+arch, lazy string)'], TEAL, align="left")

# ---- Panel 2: swap at build time -----------------------------------------
y2 = y0 + P1_H + 20
P2_H = 160
d.panel(y2, P2_H, 2, "At build time: find and swap the model identity",
        "The worker asks model_utils whether the model is AFD, then rewrites the architecture name.")
by2 = y2 + 70
d.box(60, by2, 470, 72, "has_afd_model_registration", [
    'arch.removeprefix("AFD") in the map'], EMERALD, align="left")
d.box(560, by2, 480, 72, "get_afd_model_config", [
    'deepcopy, architectures = ["AFD"+arch]',
    "keeps hf_text_config is hf_config"], BLUE, align="left")

# ---- Panel 3: notable mappings -------------------------------------------
y3 = y2 + P2_H + 20
P3_H = 150
d.panel(y3, P3_H, 3, "Three mappings to remember",
        "The README names families loosely; the code registers these exact strings.")
by3 = y3 + 70
d.box(50, by3, 320, 64, "DeepseekV32ForCausalLM", [
    "-> AFDDeepseekV3", "reuses the V3 class"], NEUTRAL, align="left")
d.box(390, by3, 320, 64, "DeepseekV4ForCausalLM", [
    "-> NPU or GPU class", "chosen by torch_npu"], VIOLET, align="left")
d.box(730, by3, 320, 64, "Qwen3_5MoeFor...Generation", [
    "-> AFDQwen3_5...", "CUDA execution only"], PINK, align="left")

y = y3 + P3_H + 18
d.legend(30, y, [(NEUTRAL, "map / base arch"), (TEAL, "register"), (EMERALD, "detect"),
                 (BLUE, "rewrite identity"), (VIOLET, "NPU"), (PINK, "CUDA only")])
y += 34
y = d.footnotes(30, y,
                ["deepcopy keeps aliasing, so hf_text_config is hf_config stays true; vLLM Ascend uses that "
                 "identity to tell text models from multimodal (model_utils.py:39-43).",
                 "get_afd_model_config raises for Qwen3.5/3.6 when device_type is not cuda (model_utils.py:34-38)."])
d.save(height=y + 12)
