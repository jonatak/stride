const hrTableBody = document.getElementById("hrTableBody");
const yearlySummaryStats = document.getElementById("yearlySummaryStats");
const yearSelect = document.getElementById("yearSelect");
const yearlyTitle = document.getElementById("yearlyTitle");
const recentActivities = document.getElementById("recentActivities");
let maxHrFromApi = null;

if (hrTableBody && yearlySummaryStats && yearSelect && recentActivities && yearlyTitle) {
  const startFromServer = recentActivities.dataset.start || "";
  const endFromServer = recentActivities.dataset.end || "";

  const zoneColors = {
    1: "is-success",
    2: "is-info",
    3: "is-link",
    4: "is-warning",
    5: "is-danger",
  };

  function paceToSeconds(paceStr) {
    const [minStr, secStr] = paceStr.split(":");
    const minutes = Number(minStr);
    const seconds = Number(secStr);
    if (Number.isNaN(minutes) || Number.isNaN(seconds)) return 0;
    return minutes * 60 + seconds;
  }

  function secondsToPace(totalSeconds) {
    if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) return "–";
    const mins = Math.floor(totalSeconds / 60);
    const secs = Math.round(totalSeconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")} min/km`;
  }

  function getZonePct(row, key) {
    const value = row?.zones?.[key];
    return Number.isFinite(value) ? value : 0;
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    if (hrs > 0) {
      return `${hrs}h ${remMins}m`;
    }
    return `${mins}m`;
  }

  function renderHrZones(data) {
    if (!data || !Array.isArray(data.zones)) {
      hrTableBody.innerHTML = `<tr><td colspan="3">No HR zone data</td></tr>`;
      return;
    }
    maxHrFromApi = data.max_hr ?? null;
    hrTableBody.innerHTML = data.zones.map(z => `
      <tr>
        <td>
          <span class="tag ${zoneColors[z.zone] ?? ""}">Zone ${z.zone}</span>
        </td>
        <td>${z.min_bpm}</td>
        <td>${z.max_bpm}</td>
      </tr>
    `).join("");
  }

  function renderYearlySummary(series, year) {
    yearlyTitle.textContent = `Yearly Summary (${year})`;
    if (!Array.isArray(series) || series.length === 0) {
      yearlySummaryStats.innerHTML = `<p>No data</p>`;
      return;
    }

    const totalDistance = series.reduce((sum, row) => sum + (row.distance_km ?? 0), 0);
    const totalActivities = series.reduce((sum, row) => sum + (row.count_activities ?? 0), 0);
    const weightedPaceSeconds = series.reduce((sum, row) => sum + paceToSeconds(row.mn_per_km) * (row.distance_km ?? 0), 0);
    const avgPaceSeconds = totalDistance > 0 ? weightedPaceSeconds / totalDistance : 0;
    const totalMinutes = series.reduce((sum, row) => sum + ((paceToSeconds(row.mn_per_km) * (row.distance_km ?? 0)) / 60), 0);
    const z3Minutes = series.reduce((sum, row) => sum + ((paceToSeconds(row.mn_per_km) * (row.distance_km ?? 0)) / 60) * getZonePct(row, "z3"), 0);
    const aerobicPct = totalMinutes > 0 ? (z3Minutes / totalMinutes) * 100 : 0;

    yearlySummaryStats.innerHTML = `
      <div class="columns is-multiline is-mobile">
        <div class="column is-half-tablet is-full-mobile">
          <div class="notification is-primary is-light stat-card">
            <p class="heading">Total Distance</p>
            <p class="title is-4 stat-value">${totalDistance.toFixed(1)} km</p>
          </div>
        </div>
        <div class="column is-half-tablet is-full-mobile">
          <div class="notification is-link is-light stat-card">
            <p class="heading">Avg Pace</p>
            <p class="title is-4 stat-value">${secondsToPace(avgPaceSeconds)}</p>
          </div>
        </div>
        <div class="column is-half-tablet is-full-mobile">
          <div class="notification is-info is-light stat-card">
            <p class="heading">Activities</p>
            <p class="title is-4 stat-value">${totalActivities}</p>
          </div>
        </div>
        <div class="column is-half-tablet is-full-mobile">
          <div class="notification is-success is-light stat-card">
            <p class="heading">Time in Zone 3</p>
            <p class="title is-4 stat-value">${aerobicPct.toFixed(1)}%</p>
          </div>
        </div>
      </div>
    `;
  }

  async function fetchHrZones() {
    hrTableBody.innerHTML = `<tr><td colspan="3">Loading…</td></tr>`;
    const resp = await fetch("/api/hr/zones");
    if (!resp.ok) throw new Error(`HR zones error ${resp.status}`);
    const data = await resp.json();
    renderHrZones(data.info ?? data);
  }

  async function fetchYearlySummary(year) {
    yearlySummaryStats.innerHTML = `<p>Loading…</p>`;
    const resp = await fetch(`/api/summary/yearly/${year}`);
    if (!resp.ok) throw new Error(`Yearly summary error ${resp.status}`);
    const data = await resp.json();
    renderYearlySummary(data.series ?? data, year);
  }

  function dateRangeLastDays(days) {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - (days - 1));
    const toISO = (d) => d.toISOString().slice(0, 10);
    return { start: toISO(start), end: toISO(end) };
  }

  function renderRecentActivities(series) {
    if (!Array.isArray(series) || series.length === 0) {
      recentActivities.innerHTML = `<p>No activities in the last 7 days.</p>`;
      return;
    }

    recentActivities.innerHTML = series.map(act => {
      const distanceKm = (act.distance_m ?? 0) / 1000;
      const duration = formatDuration(act.duration_s ?? 0);
      const z3Pct = (getZonePct(act, "z3") * 100).toFixed(1);
      const z1Pct = (getZonePct(act, "z1") * 100).toFixed(1);
      const z2Pct = (getZonePct(act, "z2") * 100).toFixed(1);
      const z4Pct = (getZonePct(act, "z4") * 100).toFixed(1);
      const z5Pct = (getZonePct(act, "z5") * 100).toFixed(1);
      const maxHr = act.max_hr_bpm ?? "–";
      const avgHr = act.avg_hr_bpm ?? "–";
      const intensityRatio = maxHrFromApi ? (act.max_hr_bpm ?? 0) / maxHrFromApi : 0;
      const intensityClass =
        intensityRatio >= 0.9 ? "intensity-high"
          : intensityRatio >= 0.8 ? "intensity-med"
            : "intensity-low";
      const zoneBar = `
        <div class="zone-bar">
          <div class="zone-seg zone-1" style="width:${z1Pct}%;"></div>
          <div class="zone-seg zone-2" style="width:${z2Pct}%;"></div>
          <div class="zone-seg zone-3" style="width:${z3Pct}%;"></div>
          <div class="zone-seg zone-4" style="width:${z4Pct}%;"></div>
          <div class="zone-seg zone-5" style="width:${z5Pct}%;"></div>
        </div>
      `;

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
            </div>
            ${zoneBar}
          </div>
        </div>
      `;
    }).join("");
  }

  async function fetchRecentActivities() {
    recentActivities.innerHTML = `<p>Loading…</p>`;
    const start = startFromServer || dateRangeLastDays(7).start;
    const end = endFromServer || dateRangeLastDays(7).end;
    const resp = await fetch(`/api/activities?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
    if (!resp.ok) throw new Error(`Activities error ${resp.status}`);
    const data = await resp.json();
    renderRecentActivities(data.series ?? data);
  }

  function populateYearSelect() {
    const currentYear = new Date().getFullYear();
    const years = Array.from({ length: 5 }, (_, i) => currentYear - i); // current year and 4 previous
    yearSelect.innerHTML = years.map(y => `<option value="${y}">${y}</option>`).join("");
    yearSelect.value = currentYear;
  }

  window.addEventListener("DOMContentLoaded", () => {
    populateYearSelect();

    yearSelect.addEventListener("change", (e) => {
      fetchYearlySummary(e.target.value).catch(err => {
        console.error(err);
        yearlySummaryStats.innerHTML = `<p>Error: ${err.message}</p>`;
      });
    });

    fetchHrZones().catch(err => {
      console.error(err);
      hrTableBody.innerHTML = `<tr><td colspan="3">Error: ${err.message}</td></tr>`;
    });

    fetchYearlySummary(yearSelect.value).catch(err => {
      console.error(err);
      yearlySummaryStats.innerHTML = `<p>Error: ${err.message}</p>`;
    });

    fetchRecentActivities().catch(err => {
      console.error(err);
      recentActivities.innerHTML = `<p>Error: ${err.message}</p>`;
    });
  });
}
