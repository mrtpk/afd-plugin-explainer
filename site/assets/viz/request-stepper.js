/* request-stepper.js - interactive stepper for the tour "Life of a request".
 *
 * Mounts into <x-viz id="request-stepper">. Vanilla JS, no libraries, no network.
 * It steps through the stops of one request on the simplest GPU recipe (2A2F, P2P
 * connector). For each stop it shows the active server and process, what crosses the
 * connector, and the file and function.
 *
 * Real rules copied from the code (afd-plugin / vLLM at the pinned commits):
 *   - requests go only to the attention API server (README.md:258-260)
 *   - the FFN worker is connector-driven; scheduler-driven execute_model raises
 *     (afd_plugin/v1/worker/ffn_worker.py:122-131)
 *   - the control plane publishes DP metadata once per step, before the layer loop
 *     (afd_plugin/v1/worker/attention_metadata.py:115-116;
 *      afd_plugin/v1/worker/ffn_worker.py:176)
 *   - the data plane sends per layer and stage: send_attn_output / recv_ffn_output
 *     (afd_plugin/model_executor/models/deepseek_v2.py:146,155) and recv_attn_output /
 *     send_ffn_output (afd_plugin/v1/worker/ffn_model_runner.py:236,268)
 *   - sampling runs on the attention side; the FFN runner's sample_tokens raises
 *     (afd_plugin/v1/worker/ffn_model_runner.py:405-406)
 *
 * Left out: the KV cache, the per-peer split and concat, CUDA graphs, the second DBO
 * stage, and the real tensor shapes (see the page deep dives). The content is fixed and
 * deterministic, so every reader sees the same stops; Reset returns to stop 1.
 *
 * Rules (STYLE.md section 10): IIFE scope; classes prefixed rqs- and scoped under the
 * mount; colours from site.css custom properties (dark mode works); real <button>
 * elements (min 40 px); Tab + Enter/Space; aria-live region; works at 390 px width.
 */
(function () {
  "use strict";

  var VIZ_ID = "request-stepper";

  // side: "attn" | "ffn" | "both" ; cross: text or "" for nothing on the wire.
  var STOPS = [
    { n: 1, title: "Client calls the attention API server", side: "attn",
      proc: "attention server · API server", cross: "",
      where: "vllm/entrypoints/openai/api_server.py" },
    { n: 2, title: "EngineCore and scheduler batch the request", side: "attn",
      proc: "attention server · EngineCore", cross: "",
      where: "vllm/v1/engine/core.py" },
    { n: 3, title: "Executor calls the AFD attention worker", side: "attn",
      proc: "attention server · attention worker", cross: "",
      where: "attention_worker.py · init_device" },
    { n: 4, title: "AFD runner wraps native execute_model", side: "attn",
      proc: "attention server · attention worker", cross: "",
      where: "attention_model_runner_v2.py · execute_model" },
    { n: 5, title: "Execution context installs the metadata provider", side: "attn",
      proc: "attention server · attention worker", cross: "",
      where: "attention_model_runner_v2.py · _use_afd_execution_context" },
    { n: 6, title: "Control plane publishes DP metadata (once per step)", side: "both",
      proc: "attention server · attention worker", cross: "DP metadata (control plane) → FFN",
      where: "attention_metadata.py · send_dp_metadata" },
    { n: 7, title: "Native model forward runs the decoder layers", side: "attn",
      proc: "attention server · attention worker", cross: "",
      where: "deepseek_v2.py · RemoteFFNProxy" },
    { n: 8, title: "Attention sends hidden states (per layer and stage)", side: "both",
      proc: "attention server · attention worker", cross: "hidden states (data plane) → FFN",
      where: "deepseek_v2.py · send_attn_output" },
    { n: 9, title: "FFN server loop receives the step", side: "ffn",
      proc: "FFN server · FFN worker loop", cross: "DP metadata received (once per step)",
      where: "ffn_worker.py · _run_ffn_server_loop" },
    { n: 10, title: "FFN runner computes each layer and stage", side: "ffn",
      proc: "FFN server · FFN worker", cross: "recv hidden states, send FFN output",
      where: "ffn_model_runner.py · _ffn_forward" },
    { n: 11, title: "Attention receives the FFN output, continues the layer", side: "both",
      proc: "attention server · attention worker", cross: "FFN output (data plane) → attention",
      where: "deepseek_v2.py · recv_ffn_output" },
    { n: 12, title: "Attention samples the token and returns it", side: "attn",
      proc: "attention server · attention worker", cross: "",
      where: "native GPUModelRunnerV2.sample_tokens (inherited)" }
  ];

  var SIDE_COLOR = { attn: "var(--viz-c1)", ffn: "var(--viz-c3)", both: "var(--viz-c5)" };
  var SIDE_LABEL = { attn: "Attention server", ffn: "FFN server", both: "Across the connector" };


  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function row(parent, key, valueNode) {
    var r = el("div", "rqs-row");
    r.appendChild(el("span", "rqs-key", key));
    r.appendChild(valueNode);
    parent.appendChild(r);
    return r;
  }

  function Viz(mount) {
    this.mount = mount;
    mount.innerHTML = "";               // removes the .viz-fallback text
    var root = el("div", "rqs-root");

    this.list = el("ol", "rqs-stops");
    var self = this;
    this.stopBtns = STOPS.map(function (s, i) {
      var li = el("li");
      var b = el("button", "rqs-stop", String(s.n));
      b.type = "button";
      b.setAttribute("aria-label", "Stop " + s.n + ": " + s.title);
      b.addEventListener("click", function () { self.go(i); });
      li.appendChild(b);
      self.list.appendChild(li);
      return b;
    });

    this.card = el("div", "rqs-card");
    this.ttl = el("p", "rqs-title");
    this.badge = el("span", "rqs-badge");
    this.card.appendChild(this.ttl);
    this.sideRowVal = this.badge;
    this.procVal = el("span", "rqs-val");
    this.wireVal = el("span", "rqs-wire");
    this.whereVal = el("span", "rqs-val");
    row(this.card, "Active side", this.badge);
    row(this.card, "Process", this.procVal);
    row(this.card, "On the connector", this.wireVal);
    row(this.card, "File · function", this.whereVal);

    var ctrl = el("div", "rqs-ctrl");
    this.prev = el("button", "rqs-btn", "← Back");
    this.next = el("button", "rqs-btn", "Next →");
    var rst = el("button", "rqs-btn", "Reset");
    [this.prev, this.next, rst].forEach(function (b) { b.type = "button"; ctrl.appendChild(b); });
    this.prev.addEventListener("click", function () { self.go(self.i - 1); });
    this.next.addEventListener("click", function () { self.go(self.i + 1); });
    rst.addEventListener("click", function () { self.go(0); });

    this.live = el("div", "rqs-live");
    this.live.setAttribute("aria-live", "polite");

    root.appendChild(this.list);
    root.appendChild(this.card);
    root.appendChild(ctrl);
    root.appendChild(this.live);
    mount.appendChild(root);

    this.go(0, true);
  }

  Viz.prototype.go = function (i, quiet) {
    if (i < 0 || i >= STOPS.length) return;
    this.i = i;
    var s = STOPS[i];
    var col = SIDE_COLOR[s.side] || "var(--line)";
    this.card.style.setProperty("--rqs-c", col);

    this.ttl.textContent = s.n + ". " + s.title;
    this.badge.textContent = SIDE_LABEL[s.side];
    this.procVal.textContent = s.proc;
    if (s.cross) {
      this.wireVal.className = "rqs-wire";
      this.wireVal.textContent = s.cross;
    } else {
      this.wireVal.className = "rqs-none";
      this.wireVal.textContent = "nothing crosses at this stop";
    }
    this.whereVal.textContent = s.where;

    this.stopBtns.forEach(function (b, k) {
      b.style.setProperty("--rqs-c", SIDE_COLOR[STOPS[k].side] || "var(--blue)");
      if (k === i) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    this.prev.disabled = i === 0;
    this.next.disabled = i === STOPS.length - 1;

    if (!quiet) {
      this.live.textContent = "Stop " + s.n + " of " + STOPS.length + ": " + s.title
        + ". " + SIDE_LABEL[s.side] + ". "
        + (s.cross ? "On the connector: " + s.cross + "." : "Nothing crosses the connector.");
    }
  };

  function init() {
    var mounts = document.querySelectorAll('[data-viz="' + VIZ_ID + '"]');
    Array.prototype.forEach.call(mounts, function (m) { new Viz(m); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
