(function () {
  "use strict";

  var form = document.getElementById("verify-form");
  if (!form) { return; }

  var input = document.getElementById("guide-url");
  var submit = document.getElementById("verify-submit");
  var statusEl = document.getElementById("verify-status");
  var errorEl = document.getElementById("verify-error");
  var results = document.getElementById("verify-results");
  var headline = document.getElementById("verify-headline");
  var compact = document.getElementById("verify-compact");
  var findingsEl = document.getElementById("verify-findings");
  var jsonEl = document.getElementById("verify-json");
  var downloadBtn = document.getElementById("verify-download");

  var lastJson = null;

  function show(el) { el.hidden = false; }
  function hide(el) { el.hidden = true; }

  function setBusy(busy) {
    submit.disabled = busy;
    input.disabled = busy;
    submit.textContent = busy ? "Verifying..." : "Verify";
  }

  function reset() {
    hide(errorEl);
    hide(results);
    hide(statusEl);
    errorEl.textContent = "";
    statusEl.textContent = "";
  }

  function showError(message) {
    errorEl.textContent = message;
    show(errorEl);
  }

  function plural(n, word) {
    return n + " " + word + (n === 1 ? "" : "s");
  }

  function renderFindings(findings) {
    findingsEl.textContent = "";
    if (!findings || findings.length === 0) {
      var none = document.createElement("p");
      none.className = "verify-none";
      none.textContent = "No findings reported.";
      findingsEl.appendChild(none);
      return;
    }
    var table = document.createElement("table");
    table.className = "verify-table";
    var thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Severity</th><th>ID</th><th>Message</th></tr>";
    table.appendChild(thead);
    var tbody = document.createElement("tbody");
    findings.forEach(function (finding) {
      var row = document.createElement("tr");

      var sevCell = document.createElement("td");
      sevCell.className = "sev";
      var sev = String(finding.severity || "info");
      var tag = document.createElement("span");
      tag.className = "sev-tag " + sev;
      tag.textContent = sev;
      sevCell.appendChild(tag);

      var idCell = document.createElement("td");
      var code = document.createElement("code");
      code.textContent = finding.id || "";
      idCell.appendChild(code);

      var msgCell = document.createElement("td");
      msgCell.textContent = finding.message || "";
      if (finding.remediation) {
        var fix = document.createElement("div");
        fix.className = "verify-none";
        fix.textContent = "Fix: " + finding.remediation;
        msgCell.appendChild(fix);
      }

      row.appendChild(sevCell);
      row.appendChild(idCell);
      row.appendChild(msgCell);
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    findingsEl.appendChild(table);
  }

  function renderResult(data) {
    lastJson = data;
    var guide = data.guide || {};
    var summary = data.summary || {};
    var blocking = summary.blocking_findings || 0;
    var pass = blocking === 0;

    headline.className = "verify-headline " + (pass ? "is-pass" : "is-fail");
    headline.textContent = pass
      ? "Achieved Level " + (guide.achieved_level || 0) + " · no blocking findings"
      : "Not conformant · " + plural(blocking, "blocking finding");

    compact.textContent = data.compact_report || "";
    renderFindings(data.findings);
    jsonEl.textContent = JSON.stringify(data, null, 2);
    show(results);
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    reset();

    var url = input.value.trim();
    if (!url) {
      showError("Enter a guide URL.");
      return;
    }
    if (!/^https:\/\//i.test(url)) {
      showError("The guide URL must use https.");
      return;
    }

    setBusy(true);
    statusEl.textContent = "Fetching and verifying the guide...";
    show(statusEl);

    fetch("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url })
    }).then(function (response) {
      return response.json().catch(function () {
        return null;
      }).then(function (body) {
        return { ok: response.ok, status: response.status, body: body };
      });
    }).then(function (res) {
      hide(statusEl);
      if (res.body && res.body.error) {
        showError(res.body.error.message || "The guide could not be verified.");
        return;
      }
      if (!res.ok || !res.body) {
        showError("The verifier returned an unexpected response (HTTP " + res.status + ").");
        return;
      }
      renderResult(res.body);
    }).catch(function () {
      hide(statusEl);
      showError("Could not reach the verifier. Check your connection and try again.");
    }).then(function () {
      setBusy(false);
    });
  });

  downloadBtn.addEventListener("click", function () {
    if (!lastJson) { return; }
    var blob = new Blob([JSON.stringify(lastJson, null, 2)], { type: "application/json" });
    var href = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = href;
    link.download = "guidecheck-verifier-output.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(href);
  });
})();
