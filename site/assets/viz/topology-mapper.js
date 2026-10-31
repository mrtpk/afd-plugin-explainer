/* topology-mapper.js - interactive AFD rank/topology mapper for concepts/topology.
 *
 * Mounts into <x-viz id="topology-mapper">. Vanilla JS, no libraries, no network.
 * The reader sets num_attention_ranks (A), num_ffn_ranks (F) and an optional
 * attention tensor-parallel size (TP). The visual then shows the AFD world order,
 * each rank's role rank, the P2P data-plane subgroups, and which ranks send/receive
 * DP metadata on the control plane.
 *
 * Real rules copied from the code (afd-plugin at the pinned commit):
 *   - the P2P world is ordered [F0, F1, ..., A0, A1, ...]: FFN ranks first
 *     (afd_plugin/distributed/topology.py:16-23)
 *   - world_rank: FFN = role_rank; attention = ffn_size + role_rank
 *     (afd_plugin/distributed/topology.py:135, :143)
 *   - the attention rank a joins the subgroup of FFN rank a*F//A
 *     (afd_plugin/distributed/topology.py:136); a subgroup's FFN rank is
 *     subgroup rank 0 (afd_plugin/distributed/topology.py:153-160)
 *   - num_attention_ranks >= num_ffn_ranks is required; otherwise the code raises
 *     (afd_plugin/distributed/topology.py:52-58)
 *   - DP-metadata senders are the first min_size attention ranks; each sends to
 *     FFN ranks role_rank, role_rank+min_size, ... < ffn_size, with
 *     min_size = min(F, A) (afd_plugin/distributed/topology.py:164-170); the FFN
 *     side receives one payload per step (afd_plugin/v1/worker/ffn_worker.py:176)
 *   - role_rank = (dp_rank*pcp + pcp_rank)*tp + tp_rank
 *     (afd_plugin/distributed/topology.py:92); here pcp = 1
 *
 * Left out: PCP, the NCCL communicators and process groups, the actual tensors,
 * and the per-stage token counts. DP and TP are folded into the role rank. The
 * model is fully determined by A, F and TP, so every reader sees the same result
 * for the same inputs; Reset returns to A=2, F=2, TP=1.
 *
 * Rules (STYLE.md section 10): IIFE scope; classes prefixed tpm- and scoped under
 * the mount in assets/viz/viz.css (no injected <style>); colours from site.css
 * custom properties (dark mode works); real <button> elements (min 40 px);
 * Tab + Enter/Space; aria-live region; works at 390 px width.
 */
(function () {
  "use strict";

  var VIZ_ID = "topology-mapper";
  var DEFAULTS = { A: 2, F: 2, TP: 1 };
  var LIMITS = { A: [1, 16], F: [1, 8], TP: [1, 8] };

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  // --- rules copied from the code -----------------------------------------
  function subgroupIndex(a, A, F) { return Math.floor((a * F) / A); }

  function dpDestinations(a, A, F) {
    // topology.py:164-170, with min_size = min(F, A).
    var minSize = Math.min(F, A);
    var worldRank = F + a;
    var dests = [];
    if (F <= worldRank && worldRank < F + minSize) {
      var dest = worldRank - F;
      while (dest < F) { dests.push(dest); dest += minSize; }
    }
    return dests;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function Viz(mount) {
    this.mount = mount;
    mount.innerHTML = "";
    this.state = { A: DEFAULTS.A, F: DEFAULTS.F, TP: DEFAULTS.TP };

    var root = el("div", "tpm-root");

    // controls
    var ctrls = el("div", "tpm-ctrls");
    this.steppers = {};
    var self = this;
    [["A", "attention ranks (A)"], ["F", "FFN ranks (F)"], ["TP", "attention TP"]].forEach(function (pair) {
      var key = pair[0];
      var grp = el("div", "tpm-step");
      grp.appendChild(el("span", "tpm-step-label", pair[1]));
      var controls = el("div", "tpm-step-ctrl");
      var minus = el("button", "tpm-btn tpm-btn-step", "−");
      var val = el("span", "tpm-step-val", String(self.state[key]));
      var plus = el("button", "tpm-btn tpm-btn-step", "+");
      minus.type = "button"; plus.type = "button";
      minus.setAttribute("aria-label", "decrease " + pair[1]);
      plus.setAttribute("aria-label", "increase " + pair[1]);
      minus.addEventListener("click", function () { self.bump(key, -1); });
      plus.addEventListener("click", function () { self.bump(key, 1); });
      controls.appendChild(minus); controls.appendChild(val); controls.appendChild(plus);
      grp.appendChild(controls);
      ctrls.appendChild(grp);
      self.steppers[key] = val;
    });
    var reset = el("button", "tpm-btn tpm-btn-reset", "Reset");
    reset.type = "button";
    reset.addEventListener("click", function () { self.reset(); });
    ctrls.appendChild(reset);
    root.appendChild(ctrls);

    // world row
    root.appendChild(el("h4", "tpm-h", "AFD world order"));
    this.world = el("div", "tpm-world");
    root.appendChild(this.world);

    // message (e.g. A < F rejection)
    this.msg = el("div", "tpm-msg");
    root.appendChild(this.msg);

    // subgroup table
    this.tableWrap = el("div", "tpm-tablewrap");
    root.appendChild(this.tableWrap);

    // live region
    this.live = el("div", "tpm-live");
    this.live.setAttribute("aria-live", "polite");
    root.appendChild(this.live);

    mount.appendChild(root);
    this.render(true);
  }

  Viz.prototype.bump = function (key, d) {
    var lim = LIMITS[key];
    this.state[key] = clamp(this.state[key] + d, lim[0], lim[1]);
    this.steppers[key].textContent = String(this.state[key]);
    this.render(false);
  };

  Viz.prototype.reset = function () {
    this.state = { A: DEFAULTS.A, F: DEFAULTS.F, TP: DEFAULTS.TP };
    this.steppers.A.textContent = String(DEFAULTS.A);
    this.steppers.F.textContent = String(DEFAULTS.F);
    this.steppers.TP.textContent = String(DEFAULTS.TP);
    this.render(false);
  };

  Viz.prototype.render = function (quiet) {
    var A = this.state.A, F = this.state.F, TP = this.state.TP;

    // world row: FFN first, then attention
    this.world.innerHTML = "";
    var w;
    for (w = 0; w < F; w++) this.world.appendChild(this.chip("F" + w, "ffn", w));
    for (w = 0; w < A; w++) this.world.appendChild(this.chip("A" + w, "attn", F + w));

    // validation (matches validate_p2p_topology)
    this.tableWrap.innerHTML = "";
    if (A < F) {
      this.msg.className = "tpm-msg tpm-msg-bad";
      this.msg.textContent = "Rejected: num_attention_ranks (" + A + ") < num_ffn_ranks (" + F +
        "). The P2P connector requires A >= F (topology.py:52-58).";
      if (!quiet) this.live.textContent = "Invalid: A is less than F. The code raises here.";
      return;
    }
    this.msg.className = "tpm-msg";
    this.msg.textContent = "";

    // per-FFN subgroups (data plane) + DP-metadata source
    var minSize = Math.min(F, A);
    var table = el("table", "tpm-table");
    var thead = el("thead");
    var hr = el("tr");
    ["FFN rank", "subgroup (data plane)", "DP-metadata from"].forEach(function (h) {
      hr.appendChild(el("th", null, h));
    });
    thead.appendChild(hr);
    table.appendChild(thead);
    var tb = el("tbody");
    var f;
    for (f = 0; f < F; f++) {
      var peers = [];
      for (var a = 0; a < A; a++) if (subgroupIndex(a, A, F) === f) peers.push("A" + a);
      // which attention ranks send DP metadata to this FFN rank
      var srcs = [];
      for (var aa = 0; aa < A; aa++) if (dpDestinations(aa, A, F).indexOf(f) !== -1) srcs.push("A" + aa);
      var tr = el("tr");
      tr.appendChild(this.cell("F" + f, "ffn"));
      var mem = el("td", "tpm-td");
      mem.appendChild(el("span", "tpm-tag tpm-ffn", "F" + f));
      peers.forEach(function (p) { mem.appendChild(el("span", "tpm-tag tpm-attn", p)); });
      tr.appendChild(mem);
      var src = el("td", "tpm-td");
      srcs.forEach(function (s) { src.appendChild(el("span", "tpm-tag tpm-attn", s)); });
      tr.appendChild(src);
      tb.appendChild(tr);
    }
    table.appendChild(tb);
    this.tableWrap.appendChild(table);

    // attention rank detail
    var senders = Math.min(minSize, A);
    var note = el("p", "tpm-note");
    var tpNote = (TP > 1 && A % TP === 0)
      ? " TP=" + TP + ": attention rank a has dp_rank=a//" + TP + ", tp_rank=a%" + TP + "."
      : (TP > 1 ? " (TP " + TP + " does not divide A, so the dp/tp split is not shown.)" : "");
    note.textContent = "World size = " + (F + A) + ". DP-metadata senders: the first " + senders +
      " attention rank(s) (A0.." + "A" + (senders - 1) + "); each sends to one FFN rank. min_size = " +
      minSize + "." + tpNote;
    this.tableWrap.appendChild(note);

    if (!quiet) {
      this.live.textContent = A + " attention ranks and " + F + " FFN ranks. " +
        F + " subgroups. " + senders + " attention ranks send DP metadata.";
    }
  };

  Viz.prototype.chip = function (label, role, worldRank) {
    var c = el("div", "tpm-chip tpm-" + role);
    c.appendChild(el("span", "tpm-chip-name", label));
    c.appendChild(el("span", "tpm-chip-w", "w" + worldRank));
    return c;
  };

  Viz.prototype.cell = function (label, role) {
    var td = el("td", "tpm-td");
    td.appendChild(el("span", "tpm-tag tpm-" + role, label));
    return td;
  };

  function init() {
    var mounts = document.querySelectorAll('[data-viz="' + VIZ_ID + '"]');
    Array.prototype.forEach.call(mounts, function (m) { new Viz(m); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
