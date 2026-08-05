function formatDuration(totalSeconds) {
  const neg = totalSeconds < 0;
  const abs = Math.abs(Math.floor(totalSeconds));
  const h = Math.floor(abs / 3600);
  const m = Math.floor((abs % 3600) / 60);
  const s = abs % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return (neg ? "+" : "") + `${pad(h)}:${pad(m)}:${pad(s)}`;
}

function bandFor(remainingSeconds, totalSeconds) {
  if (remainingSeconds <= 0) return "breached";
  const pct = remainingSeconds / totalSeconds;
  if (pct > 0.5) return "ok";
  if (pct > 0.15) return "warning";
  return "critical";
}

function tickClocks() {
  document.querySelectorAll("[data-clock-deadline]").forEach((el) => {
    // ── NEW: skip if the parent incident is closed/cancelled ──
    const incidentCard = el.closest(".incident-card, [data-incident-status]");
    const status = incidentCard?.dataset.incidentStatus?.toLowerCase()
                || incidentCard?.querySelector(".status-badge")?.textContent?.trim().toLowerCase();
    if (status === "closed" || status === "cancelled") {
      // Optionally freeze the bar and add a 'stopped' class
      el.classList.add("clock-stopped");
      return; // stop ticking this one
    }
    // ── END NEW ──

    const deadline = new Date(el.dataset.clockDeadline).getTime();
    const total = parseFloat(el.dataset.clockTotalSeconds);
    const now = Date.now();
    const remaining = (deadline - now) / 1000;
    const band = bandFor(remaining, total);

    const timeEl = el.querySelector(".clock-time");
    const barEl = el.querySelector(".clock-bar-fill");
    if (timeEl) timeEl.textContent = formatDuration(remaining);
    if (barEl) {
      const pct = Math.max(Math.min(remaining / total, 1), 0) * 100;
      barEl.style.width = pct + "%";
    }
    el.classList.remove("status-ok", "status-warning", "status-critical", "status-breached");
    el.classList.add("status-" + band);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  tickClocks();
  setInterval(tickClocks, 1000);
});
