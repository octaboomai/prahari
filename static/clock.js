// Ticks every countdown clock on the page once a second, client-side --
// no polling, no page reloads. Mirrors the same urgency banding the
// server uses in app/compliance.py::_band so the two never disagree.

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
