"""Attention role vs. FFN role: what each server owns, and the decoder-layer split.

Used by: src/concepts/roles.html
Sources (afd-plugin at the pinned commit in explainer.json):
  afd_plugin/compat/patches/engine_core.py:59-68      FFN EngineCore returns after executor build
  afd_plugin/compat/patches/engine_core.py:605,614    num_gpu_blocks = 0; no-op scheduler
  afd_plugin/v1/worker/ffn_worker.py:102-105          get_kv_cache_spec returns {}
  afd_plugin/v1/worker/ffn_worker.py:122-131          scheduler-driven execute_model raises
  afd_plugin/v1/worker/ffn_model_runner.py:405-406    sample_tokens raises
  afd_plugin/model_executor/models/deepseek_v2.py:474-491  attention role builds native self_attn
  afd_plugin/model_executor/models/deepseek_v2.py:516-517  dense layer -> RemoteFFNProxy
  afd_plugin/model_executor/models/deepseek_v2.py:493-500  MoE layer -> remote experts shell
  afd_plugin/model_executor/models/deepseek_v2.py:520      FFN role self_attn = PPMissingLayer
  afd_plugin/model_executor/models/deepseek_v2.py:538-559  FFN role mlp = native MoE / MLP
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svglib import BLUE, EMERALD, NEUTRAL, INK, MUTE, Diagram  # noqa: E402

d = Diagram(width=1100)
d.header("Two servers, one model",
         "The attention server owns scheduling and KV cache; the FFN server is a connector-driven loop.",
         params="afd_plugin/v1/worker/  ·  model_executor/models/deepseek_v2.py  ·  canvas 1100")

# ---- Panel 1: who owns what ------------------------------------------------
y0 = 120
P1_H = 232
d.panel(y0, P1_H, 1, "What does each server own?",
        "The attention server keeps the native vLLM parts. The FFN server drops them.")

bw, bh = 500, 150
by = y0 + 66
d.box(46, by, bw, bh, "Attention server  (attention role)",
      ["API server          receives the request",
       "scheduler           batches tokens per step",
       "KV cache            native, per layer",
       "sampler             logits + sampling, every step",
       "self_attn           native attention module",
       "mlp -> RemoteFFNProxy / remote experts"],
      col=BLUE, align="left")
d.box(566, by, bw, bh, "FFN server  (FFN role)",
      ["no API server       requests never arrive here",
       "no scheduler        a no-op stand-in only",
       "no KV cache         get_kv_cache_spec -> {}",
       "no sampler          sample_tokens raises",
       "self_attn -> PPMissingLayer (no attention)",
       "mlp -> native MoE / MLP experts + loop"],
      col=EMERALD, align="left")

# ---- Panel 2: the decoder-layer split --------------------------------------
y2 = y0 + P1_H + 22
P2_H = 196
d.panel(y2, P2_H, 2, "How is one decoder layer split?",
        "AFDDeepseekV2DecoderLayer builds only the modules its role owns (deepseek_v2.py:383-559).")

cw, ch = 300, 60
cy = y2 + 72
# centre source box
d.box(400, y2 + 66, 300, 44, "native decoder layer",
      ["self_attn  +  mlp"], col=NEUTRAL, align="middle")
# role branches
ly = y2 + 128
d.box(46, ly, 500, 56, "attention role",
      ["self_attn: native   ·   mlp: RemoteFFNProxy",
       "MoE layer -> AFDDeepseekV2RemoteExpertsMoE"],
      col=BLUE, align="left")
d.box(566, ly, 500, 56, "FFN role",
      ["self_attn: PPMissingLayer  (dropped)",
       "mlp: native DeepseekV2MoE / DeepseekV2MLP"],
      col=EMERALD, align="left")
d.arrow(500, y2 + 110, 300, ly - 2, BLUE)
d.arrow(600, y2 + 110, 820, ly - 2, EMERALD)

# ---- legend + footnotes ----------------------------------------------------
y = y2 + P2_H + 18
d.legend(30, y, [(BLUE, "attention server / role"), (EMERALD, "FFN server / role"),
                 (NEUTRAL, "native vLLM module")])
y += 34
y = d.footnotes(30, y,
                ["The FFN EngineCore returns after the executor is built: no KV cache, a no-op scheduler "
                 "(engine_core.py:59-68, :605, :614).",
                 "Send requests only to the attention API server (README.md:258-260)."])
d.save(height=y + 14)
