/* dbo-timeline.js - interactive DBO (dual-batch overlap) timeline.
 *
 * Mounts into <x-viz id="dbo-timeline">. Vanilla JS, no libraries, no network.
 * The reader picks the number of decoder layers N (2..6) and steps through the
 * send / yield / FFN compute / receive events of one step. Two lanes
 * (attention and FFN) and two stages show where the two ubatches overlap.
 *
 * Real rules copied from the code (afd-plugin at the pinned commit):
 *   - DBO splits a step into exactly two stages (ubatches)
 *     (afd_plugin/validation.py:126-131; afd_plugin/v1/worker/ubatch_wrapper.py:28-29)
 *   - the attention proxy sends, then yields, then receives, per layer and stage
 *     (afd_plugin/model_executor/models/deepseek_v2.py:146-158)
 *   - the DBO yield hands control to the other ubatch thread
 *     (afd_plugin/v1/worker/dbo.py:12-24, :52-54)
 *   - the FFN side answers each stage: recv_attn_output, compute, send_ffn_output
 *     (afd_plugin/v1/worker/ffn_model_runner.py:222-269)
 *   - sampling runs once per step, after the last layer, on the attention side
 *     (vllm/v1/worker/gpu/model_runner.py:2048-2050)
 *
 * Left out (and said on the page): real timing and kernel durations, the control
 * plane publish before the loop, CUDA graph replay, the per-peer split, and the
 * rank mapping. Times here are ILLUSTRATIVE, not measured. The event order is
 * copied from the code; the overlap is a simplified model. The model is fully
 * determined by N and the event index, so every reader sees the same result;
 * Reset returns to N=3, layer 0, event 0.
 *
 * Rules (STYLE.md section 10): IIFE scope; classes prefixed dbt- and scoped under
 * the mount in assets/viz/viz.css (no injected <style>); colours from site.css
 * custom properties (dark mode works); real <button> elements (min 40 px);
 * Tab + Enter/Space; aria-live region; works at 390 px width.
 */
(function () {
  "use strict";

  var VIZ_ID = "dbo-timeline";
  var DEFAULTS = { N: 3 };
  var N_LIMITS = [2, 6];
  var EVENTS_PER_LAYER = 7;

  // Tracks (grid rows) and time columns.
  var TRACKS = [
    { key: "a0", label: "attention · stage 0", role: "attn" },
    { key: "a1", label: "attention · stage 1", role: "attn" },
    { key: "f0", label: "FFN · stage 0", role: "ffn" },
    { key: "f1", label: "FFN · stage 1", role: "ffn" },
  ];
  var COLS = 4; // t1..t4

  // For the current layer, which cell each event fills: [trackIndex, col, phase].
  // Event 1 is the DBO yield: no new cell.
  var FILLS = {
    0: [0, 0, "send"],
    2: [1, 1, "send"],
    3: [2, 1, "ffn"],
    4: [3, 2, "ffn"],
    5: [0, 2, "recv"],
    6: [1, 3, "recv"],
  };

  var PHASE_TEXT = [
    "Stage 0: send hidden states (deepseek_v2.py:146).",
    "DBO yield: hand control to the stage 1 thread (dbo.py).",
    "Stage 1: send hidden states while stage 0 waits.",
    "FFN stage 0: receive, compute, send back. Overlaps attention stage 1.",
    "FFN stage 1: receive, compute, send back.",
    "Stage 0: receive the FFN output (deepseek_v2.py:155).",
    "Stage 1: receive the FFN output. The layer is done.",
  ];

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function Viz(mount) {
    this.mount = mount;
    mount.innerHTML = "";
    this.state = { N: DEFAULTS.N, idx: 0 }; // idx = global event index; -1 none yet handled as 0

    var root = el("div", "dbt-root");

    // controls
    var ctrls = el("div", "dbt-ctrls");
    var self = this;

    var grp = el("div", "dbt-step");
    grp.appendChild(el("span", "dbt-step-label", "decoder layers (N)"));
    var nc = el("div", "dbt-step-ctrl");
    var minus = el("button", "dbt-btn dbt-btn-step", "−");
    this.nval = el("span", "dbt-step-val", String(this.state.N));
    var plus = el("button", "dbt-btn dbt-btn-step", "+");
    minus.type = "button"; plus.type = "button";
    minus.setAttribute("aria-label", "decrease the number of layers");
    plus.setAttribute("aria-label", "increase the number of layers");
    minus.addEventListener("click", function () { self.bumpN(-1); });
    plus.addEventListener("click", function () { self.bumpN(1); });
    nc.appendChild(minus); nc.appendChild(this.nval); nc.appendChild(plus);
    grp.appendChild(nc);
    ctrls.appendChild(grp);

    var acts = el("div", "dbt-acts");
    this.stepBtn = el("button", "dbt-btn dbt-btn-primary", "Step");
    this.stepBtn.type = "button";
    this.stepBtn.addEventListener("click", function () { self.step(); });
    var reset = el("button", "dbt-btn dbt-btn-reset", "Reset");
    reset.type = "button";
    reset.addEventListener("click", function () { self.reset(); });
    acts.appendChild(this.stepBtn); acts.appendChild(reset);
    ctrls.appendChild(acts);
    root.appendChild(ctrls);

    // status
    this.status = el("div", "dbt-status");
    root.appendChild(this.status);

    // grid
    this.gridWrap = el("div", "dbt-gridwrap");
    root.appendChild(this.gridWrap);

    // phase line
    this.phase = el("div", "dbt-phase");
    root.appendChild(this.phase);

    // note
    root.appendChild(el("p", "dbt-note",
      "Illustrative timing: real kernel durations are not shown. The event order is from the code; the overlap is a simplified model."));

    // live region
    this.live = el("div", "dbt-live");
    this.live.setAttribute("aria-live", "polite");
    root.appendChild(this.live);

    mount.appendChild(root);
    this.render(true);
  }

  Viz.prototype.totalEvents = function () { return this.state.N * EVENTS_PER_LAYER; };

  Viz.prototype.bumpN = function (d) {
    this.state.N = clamp(this.state.N + d, N_LIMITS[0], N_LIMITS[1]);
    this.state.idx = 0;
    this.nval.textContent = String(this.state.N);
    this.render(false);
  };

  Viz.prototype.step = function () {
    // idx ranges 0 .. totalEvents (totalEvents == finished / sampling state)
    if (this.state.idx < this.totalEvents()) this.state.idx += 1;
    this.render(false);
  };

  Viz.prototype.reset = function () {
    this.state = { N: DEFAULTS.N, idx: 0 };
    this.nval.textContent = String(DEFAULTS.N);
    this.render(false);
  };

  Viz.prototype.render = function (quiet) {
    var N = this.state.N;
    var idx = this.state.idx;
    var total = this.totalEvents();
    var finished = idx >= total;

    // which layer / event are we at? idx is "events completed"; the current
    // (active) event is idx-1 within the layer, or none at idx 0.
    var activeGlobal = idx - 1; // -1 means nothing yet
    var layer = finished ? N - 1 : Math.floor(Math.max(activeGlobal, 0) / EVENTS_PER_LAYER);
    var evInLayer = activeGlobal < 0 ? -1 : (activeGlobal % EVENTS_PER_LAYER);

    // status line
    this.gridWrap.innerHTML = "";
    if (finished) {
      this.status.textContent = "Step complete. Sampling runs once, on the attention side.";
    } else if (activeGlobal < 0) {
      this.status.textContent = "Ready. Layer 1 of " + N + ". Press Step.";
    } else {
      this.status.textContent = "Layer " + (layer + 1) + " of " + N + " · event " +
        (evInLayer + 1) + " of " + EVENTS_PER_LAYER + ".";
    }

    // build the grid for the current layer up to evInLayer
    var filled = {}; // "track,col" -> phase
    if (!finished) {
      for (var e = 0; e <= evInLayer; e++) {
        if (FILLS[e]) {
          var f = FILLS[e];
          filled[f[0] + "," + f[1]] = f[2];
        }
      }
    }
    var activeCell = (!finished && evInLayer >= 0 && FILLS[evInLayer])
      ? (FILLS[evInLayer][0] + "," + FILLS[evInLayer][1]) : null;

    var table = el("table", "dbt-table");
    var thead = el("thead");
    var hr = el("tr");
    hr.appendChild(el("th", "dbt-th dbt-th-track", "track"));
    for (var c = 0; c < COLS; c++) hr.appendChild(el("th", "dbt-th", "t" + (c + 1)));
    thead.appendChild(hr);
    table.appendChild(thead);
    var tb = el("tbody");
    for (var t = 0; t < TRACKS.length; t++) {
      var tr = el("tr");
      var th = el("th", "dbt-td-track dbt-" + TRACKS[t].role, TRACKS[t].label);
      tr.appendChild(th);
      for (var col = 0; col < COLS; col++) {
        var key = t + "," + col;
        var phase = filled[key];
        var td = el("td", "dbt-cell");
        if (phase) {
          var chip = el("span", "dbt-chip dbt-" + phase, phaseLabel(phase));
          td.appendChild(chip);
          if (key === activeCell) td.className = "dbt-cell dbt-cell-active";
        }
        tr.appendChild(td);
      }
      tb.appendChild(tr);
    }
    table.appendChild(tb);
    this.gridWrap.appendChild(table);

    // phase text
    if (finished) {
      this.phase.textContent = "After the last layer, the attention side computes logits and samples the token.";
    } else if (evInLayer < 0) {
      this.phase.textContent = "Each layer runs two stages. Watch t2 and t3: attention and FFN work overlap there.";
    } else {
      this.phase.textContent = PHASE_TEXT[evInLayer];
    }

    this.stepBtn.disabled = finished;

    if (!quiet) {
      this.live.textContent = this.status.textContent + " " + this.phase.textContent;
    }
  };

  function phaseLabel(phase) {
    if (phase === "send") return "send";
    if (phase === "recv") return "recv";
    if (phase === "ffn") return "compute";
    return phase;
  }

  function init() {
    var mounts = document.querySelectorAll('[data-viz="' + VIZ_ID + '"]');
    Array.prototype.forEach.call(mounts, function (m) { new Viz(m); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
