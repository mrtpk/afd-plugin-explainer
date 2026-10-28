"""How the AFD role worker is selected, only when worker_cls was 'auto'.

Used by: src/concepts/worker-selection.html
Sources (afd-plugin at the pinned commit in explainer.json):
  compat/patches/config_validation.py:60      record worker_cls_was_auto
  compat/patches/config_validation.py:92-93    _select_afd_worker_for_auto
  compat/patches/config_validation.py:179-197  rewrite worker_cls
  validation.py:280-309   afd_worker_qualname_for_platform_default
  afd_plugin/v1/worker/attention_worker.py:60-88   init_device runner swap
Sources (vLLM at extra_repos.vllm):
  vllm/v1/worker/worker_base.py:273-277   import worker_cls by qualname
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, TEAL, NEUTRAL, EMERALD, VIOLET, MUTE, INK, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Choosing the AFD role worker",
         "A patched create_engine_config rewrites worker_cls, but only when the user left it as 'auto'.",
         params="config_validation.py:51-113  ·  validation.py:280-309")

# ---- Panel 1: the selection flow -----------------------------------------
y0 = 120
pitch = 74
ch = 58
n = 5
P1_H = 60 + n * pitch - (pitch - ch) + 6
d.panel(y0, P1_H, 1, "The rewrite runs only for worker_cls == 'auto'",
        "An explicit --worker-cls is kept and checked later, not overwritten.")
cy = y0 + 58
x, w = 60, 980
d.step_card(x, cy + 0 * pitch, w, ch, 1, "Patched create_engine_config: was it 'auto'?", BLUE,
            tag="config_validation.py:60", key_w=44,
            rows=[("flag", "worker_cls_was_auto = worker_cls == 'auto'")])
d.step_card(x, cy + 1 * pitch, w, ch, 2, "vLLM builds the config (platform default worker)", NEUTRAL,
            tag="config_validation.py:66-71", key_w=44,
            rows=[("set", "worker_cls = platform default, e.g. gpu_worker.Worker")])
d.step_card(x, cy + 2 * pitch, w, ch, 3, "If auto: rewrite to the AFD role worker", BLUE,
            tag="config_validation.py:92-93,179-197", key_w=44,
            rows=[("call", "afd_worker_qualname_for_platform_default(role, ...)")])
d.step_card(x, cy + 3 * pitch, w, ch, 4, "vLLM imports worker_cls by its qualname", NEUTRAL,
            tag="vllm worker_base.py:273-277", key_w=44,
            rows=[("load", "resolve_obj_by_qualname(parallel_config.worker_cls)")])
d.step_card(x, cy + 4 * pitch, w, ch, 5, "init_device: check the stack, then swap the runner", TEAL,
            tag="attention_worker.py:60-88", key_w=44,
            rows=[("then", "assert_compatible_afd_stack, swap GPUModelRunner")])

# ---- Panel 2: default -> AFD worker per platform and role -----------------
y2 = y0 + P1_H + 20
P2_H = 176
d.panel(y2, P2_H, 2, "Platform default worker  ->  AFD worker, per role",
        "Selected from the normalized platform default (validation.py:290-296).")
by = y2 + 70
d.box(60, by, 480, 84, "CUDA: gpu_worker.Worker", [
    "attention -> AFDAttentionWorker",
    "ffn       -> AFDFFNWorker"], BLUE, align="left")
d.box(560, by, 480, 84, "Ascend NPU: NPUWorker", [
    "attention -> AFDNPUAttentionWorker",
    "ffn       -> AFDNPUFFNWorker"], VIOLET, align="left")

y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "AFD rewrite step"), (NEUTRAL, "native vLLM"), (TEAL, "runner swap"),
                 (VIOLET, "NPU")])
y += 34
y = d.footnotes(30, y,
                ["Both roles need VLLM_USE_V2_MODEL_RUNNER=1; the validator rejects a config without it "
                 "(validation.py:90-91).",
                 "An explicit wrong worker is rejected by assert_compatible_afd_stack, not silently fixed "
                 "(validation.py:343-367)."])
d.save(height=y + 12)
