const activitiesList = document.getElementById("activitiesList");
const rangePreset = document.getElementById("rangePreset");
const startInput = document.getElementById("startInput");
const endInput = document.getElementById("endInput");
const applyBtn = document.getElementById("applyBtn");
let maxHrFromApi = null;

if (activitiesList && rangePreset && startInput && endInput && applyBtn) {
  const startFromServer = activitiesList.dataset.start || "";
  const endFromServer = activitiesList.dataset.end || "";

  function parseISO(dateStr) {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
  }

  function formatISO(date) {
    return date.toISOString().slice(0, 10);
  }

  function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
  }

  function endOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0);
  }

  function applyPreset(key) {
    const today = new Date();
    let start = today;
    let end = today;
    switch (key) {
      case "last-7":
        start = new Date(today);
        start.setDate(end.getDate() - 6);
        break;
      case "last-30":
        start = new Date(today);
        start.setDate(end.getDate() - 29);
        break;
      case "last-90":
        start = new Date(today);
        start.setDate(end.getDate() - 89);
        break;
      case "this-month":
        start = startOfMonth(today);
        end = endOfMonth(today);
        break;
      case "prev-month": {
        const prev = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        start = startOfMonth(prev);
        end = endOfMonth(prev);
        break;
      }
      case "custom": {
        const s = parseISO(startInput.value);
        const e = parseISO(endInput.value);
        if (s && e) {
          start = s;
          end = e;
        }
        break;
      }
      default:
        start = new Date(today);
        start.setDate(end.getDate() - 6);
    }
    startInput.value = formatISO(start);
    endInput.value = formatISO(end);
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    if (hrs > 0) return `${hrs}h ${remMins}m`;
    return `${mins}m`;
  }

  function getZonePct(row, key) {
    const value = row?.zones?.[key];
    return Number.isFinite(value) ? value : 0;
  }

  async function fetchHrZones() {
    try {
      const resp = await fetch("/api/hr/zones");
      if (!resp.ok) return;
      const data = await resp.json();
      maxHrFromApi = data.max_hr ?? null;
    } catch (err) {
      console.error("HR zones fetch failed", err);
    }
  }

  function renderActivities(series) {
    if (!Array.isArray(series) || series.length === 0) {
      activitiesList.innerHTML = `<p>No activities in this range.</p>`;
      return;
    }

    activitiesList.innerHTML = series.map(act => {
      const distanceKm = (act.distance_m ?? 0) / 1000;
      const duration = formatDuration(act.duration_s ?? 0);
      const avgHr = act.avg_hr_bpm ?? "–";
      const maxHr = act.max_hr_bpm ?? "–";
      const z1Pct = (getZonePct(act, "z1") * 100).toFixed(1);
      const z2Pct = (getZonePct(act, "z2") * 100).toFixed(1);
      const z3Pct = (getZonePct(act, "z3") * 100).toFixed(1);
      const z4Pct = (getZonePct(act, "z4") * 100).toFixed(1);
      const z5Pct = (getZonePct(act, "z5") * 100).toFixed(1);
      const intensityRatio = maxHrFromApi ? (act.max_hr_bpm ?? 0) / maxHrFromApi : 0;
      const intensityClass =
        intensityRatio >= 0.9 ? "intensity-high"
          : intensityRatio >= 0.8 ? "intensity-med"
            : "intensity-low";

      return `
        <div class="card activity-card ${intensityClass}" style="cursor: pointer;" onclick="window.location.href='/ui/activities/details/${act.activity_id}';">
          <div class="card-content">
            <div class="is-flex is-justify-content-space-between is-align-items-center">
              <div>
                <p class="title is-5">${act.activity_name || "Activity"}</p>
                <p class="subtitle is-7 has-text-grey">${formatDate(act.start)}</p>
                <p class="is-size-7 has-text-grey">Avg HR: ${avgHr} bpm • Max HR: ${maxHr}</p>
              </div>
            </div>
            <div class="activity-metrics" style="margin-top: 0.5rem;">
              <span class="pill pill-distance">${distanceKm.toFixed(1)} km</span>
              <span class="pill pill-pace">${act.pace_mn_per_km} min/km</span>
              <span class="pill pill-duration">${duration}</span>
              <span class="pill pill-hr">${avgHr} bpm</span>
              <span class="pill pill-hr-max">Max ${maxHr}</span>
            </div>
            <div class="zone-bar">
              <div class="zone-seg zone-1" style="width:${z1Pct}%;"></div>
              <div class="zone-seg zone-2" style="width:${z2Pct}%;"></div>
              <div class="zone-seg zone-3" style="width:${z3Pct}%;"></div>
              <div class="zone-seg zone-4" style="width:${z4Pct}%;"></div>
              <div class="zone-seg zone-5" style="width:${z5Pct}%;"></div>
            </div>
          </div>
        </div>
      `;
    }).join("");
  }

  async function fetchActivities(start, end) {
    activitiesList.innerHTML = `<p>Loading…</p>`;
    const url = `/api/activities?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Activities error ${resp.status}`);
    const data = await resp.json();
    renderActivities(data.series ?? data);
  }

  function applyFilters() {
    const start = startInput.value;
    const end = endInput.value;
    if (!start || !end) {
      activitiesList.innerHTML = `<p>Please select a valid date range.</p>`;
      return;
    }
    fetchActivities(start, end).catch(err => {
      console.error(err);
      activitiesList.innerHTML = `<p>Error: ${err.message}</p>`;
    });
  }

  window.addEventListener("DOMContentLoaded", () => {
    // Initialize with server-provided defaults
    if (startFromServer) startInput.value = startFromServer;
    if (endFromServer) endInput.value = endFromServer;
    rangePreset.value = "last-7";

    rangePreset.addEventListener("change", (e) => {
      applyPreset(e.target.value);
    });

    applyBtn.addEventListener("click", (e) => {
      e.preventDefault();
      applyFilters();
    });

    fetchHrZones().finally(() => {
      applyFilters();
    });
  });
}
