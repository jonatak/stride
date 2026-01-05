const rangeSelect = document.getElementById("rangeSelect");

if (rangeSelect) {
  const startFromServer = rangeSelect.dataset.start || "";
  const endFromServer = rangeSelect.dataset.end || "";

  function paceToSeconds(paceStr) {
    const [minStr, secStr] = paceStr.split(":");
    const minutes = Number(minStr);
    const seconds = Number(secStr);

    if (Number.isNaN(minutes) || Number.isNaN(seconds)) {
      throw new Error(`Invalid pace value: ${paceStr}`);
    }

    return minutes * 60 + seconds;
  }

  function secondsToPace(totalSeconds) {
    const mins = Math.floor(totalSeconds / 60);
    const secs = Math.round(totalSeconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")} min/km`;
  }

  function formatMinutes(mins) {
    if (!Number.isFinite(mins)) return "";
    const totalMinutes = Math.round(mins);
    const hours = Math.floor(totalMinutes / 60);
    const remainingMins = totalMinutes % 60;
    if (hours === 0) return `${remainingMins} min`;
    return `${hours}h ${remainingMins.toString().padStart(2, "0")}m`;
  }

  const today = new Date();

  function startOfYear(year) {
    return new Date(year, 0, 1);
  }

  function endOfYear(year) {
    return new Date(year, 11, 31);
  }

  function startOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
  }

  function endOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0);
  }

  function addMonths(date, delta) {
    const d = new Date(date);
    d.setMonth(d.getMonth() + delta);
    return d;
  }

  function toISO(date) {
    return date.toISOString().slice(0, 10);
  }

  function resolveRange(key) {
    const currentYear = today.getFullYear();
    switch (key) {
      case "current-year":
        return { start: toISO(startOfYear(currentYear)), end: toISO(endOfYear(currentYear)) };
      case "previous-year":
        return { start: toISO(startOfYear(currentYear - 1)), end: toISO(endOfYear(currentYear - 1)) };
      case "last-6-months": {
        const end = endOfMonth(today);
        const start = startOfMonth(addMonths(today, -5));
        return { start: toISO(start), end: toISO(end) };
      }
      case "last-12-months": {
        const end = endOfMonth(today);
        const start = startOfMonth(addMonths(today, -11));
        return { start: toISO(start), end: toISO(end) };
      }
      case "last-24-months": {
        const end = endOfMonth(today);
        const start = startOfMonth(addMonths(today, -23));
        return { start: toISO(start), end: toISO(end) };
      }
      default:
        return { start: startFromServer, end: endFromServer };
    }
  }

  async function loadMonthly(range) {
    const url = `/api/pace/monthly?start=${encodeURIComponent(range.start)}&end=${encodeURIComponent(range.end)}`;
    const resp = await fetch(url);

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`API error ${resp.status}: ${txt}`);
    }

    const payload = await resp.json();
    // depending on your API shape: { series: [...] } or [...]
    const series = payload.series ?? payload;

    if (!Array.isArray(series) || series.length === 0) {
      throw new Error("No data returned from API");
    }

    return series;
  }

  async function loadVo2Max(range) {
    const url = `/api/vo2max?start=${encodeURIComponent(range.start)}&end=${encodeURIComponent(range.end)}`;
    const resp = await fetch(url);

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`VO2 Max API error ${resp.status}: ${txt}`);
    }

    const payload = await resp.json();
    return payload.series ?? payload;
  }

  async function loadBodyComposition(range) {
    const url = `/api/bodycomposition/daily?start=${encodeURIComponent(range.start)}&end=${encodeURIComponent(range.end)}`;
    const resp = await fetch(url);

    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`Body composition API error ${resp.status}: ${txt}`);
    }

    const payload = await resp.json();
    return payload.series ?? payload;
  }

  let paceChartInstance = null;
  let combinedChartInstance = null;
  let vo2MaxChartInstance = null;
  let weightChartInstance = null;

  function renderPaceChart(series) {
    const labels = series.map(r => r.period_start);
    const paces = series.map(r => paceToSeconds(r.mn_per_km));

    const canvas = document.getElementById("paceChart");
    if (!canvas) throw new Error("Missing canvas#paceChart");

    const ctx = canvas.getContext("2d");

    if (paceChartInstance) {
      paceChartInstance.destroy();
    }

    paceChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Pace (min/km)",
          data: paces,
          borderColor: "#485fc7",
          backgroundColor: "#485fc7",
          fill: false,
          tension: 0.25,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        interaction: {
          mode: "index",
          intersect: false
        },
        onClick: (_, elements) => {
          if (!elements || elements.length === 0) return;
          const idx = elements[0].index;
          const label = labels[idx];
          if (!label) return;
          const start = new Date(label);
          if (isNaN(start.getTime())) return;
          const end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
          const startStr = start.toISOString().slice(0, 10);
          const endStr = end.toISOString().slice(0, 10);
          window.location.href = `/ui/activities?start=${encodeURIComponent(startStr)}&end=${encodeURIComponent(endStr)}`;
        },
        scales: {
          y: {
            beginAtZero: false,
            reverse: true,
            ticks: {
              callback: (value) => secondsToPace(value)
            },
            title: {
              display: true,
              text: "Pace (min/km)"
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                const pace = secondsToPace(context.parsed.y);
                return `${context.dataset.label}: ${pace}`;
              }
            }
          },
          legend: {
            display: true
          }
        }
      }
    });
  }

  function renderCombinedChart(series) {
    const labels = series.map(r => r.period_start);
    const totalMins = series.map(r => (paceToSeconds(r.mn_per_km) * r.distance_km) / 60);
    const distances = series.map(r => r.distance_km);
    const counts = series.map(r => r.count_activities ?? 0);

    const zones = ["z1", "z2", "z3", "z4", "z5"];
    const colors = [
      "rgba(46, 204, 113, 0.6)",
      "rgba(52, 152, 219, 0.6)",
      "rgba(155, 89, 182, 0.6)",
      "rgba(241, 196, 15, 0.6)",
      "rgba(231, 76, 60, 0.6)"
    ];

    const zoneValue = (row, zKey) => {
      const value = row.zones?.[zKey];
      return Number.isFinite(value) ? value : 0;
    };

    const zoneDatasets = zones.map((zKey, idx) => ({
      label: `Zone ${idx + 1}`,
      data: series.map((row, rowIdx) => totalMins[rowIdx] * zoneValue(row, zKey)),
      backgroundColor: colors[idx],
      stack: "zones",
      borderWidth: 1,
      yAxisID: "yMinutes",
      type: "bar",
    }));

    const distanceDataset = {
      label: "Distance (km)",
      data: distances,
      borderColor: "#485fc7",
      backgroundColor: "rgba(72, 95, 199, 0.15)",
      type: "line",
      yAxisID: "yDistance",
      tension: 0.25,
      pointRadius: 3,
      fill: false,
    };

    const canvas = document.getElementById("combinedChart");
    if (!canvas) throw new Error("Missing canvas#combinedChart");

    const ctx = canvas.getContext("2d");

    if (combinedChartInstance) {
      combinedChartInstance.destroy();
    }

    combinedChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [...zoneDatasets, distanceDataset],
      },
      options: {
        responsive: true,
        interaction: { mode: "index", intersect: false },
        onClick: (_, elements) => {
          if (!elements || elements.length === 0) return;
          const idx = elements[0].index;
          const label = labels[idx];
          if (!label) return;
          const start = new Date(label);
          if (isNaN(start.getTime())) return;
          const end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
          const startStr = start.toISOString().slice(0, 10);
          const endStr = end.toISOString().slice(0, 10);
          window.location.href = `/ui/activities?start=${encodeURIComponent(startStr)}&end=${encodeURIComponent(endStr)}`;
        },
        scales: {
          x: { stacked: true },
          yMinutes: {
            stacked: true,
            beginAtZero: true,
            title: { display: true, text: "Minutes" },
            ticks: {
              callback: (value) => `${Math.round(value)} min`
            }
          },
          yDistance: {
            position: "right",
            beginAtZero: true,
            grid: { drawOnChartArea: false },
            title: { display: true, text: "Distance (km)" }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                const ds = context.dataset;
                if (ds.stack === "zones") {
                  return `${ds.label}: ${formatMinutes(context.parsed.y)}`;
                }
                if (ds.label === "Distance (km)") {
                  return `${ds.label}: ${context.parsed.y.toFixed(1)} km`;
                }
                return `${ds.label}: ${context.parsed.y}`;
              },
              footer: (items) => {
                // Sum only zone stacks for total minutes
                const totalMinutes = items
                  .filter(item => item.dataset.stack === "zones")
                  .reduce((sum, item) => sum + item.parsed.y, 0);
                const activityCount = counts[items[0].dataIndex] ?? 0;
                const footerLines = [];
                if (totalMinutes > 0) {
                  footerLines.push(`Total time: ${formatMinutes(totalMinutes)}`);
                }
                footerLines.push(`Activities: ${activityCount}`);
                return footerLines.join("\n");
              }
            }
          },
          legend: { display: true }
        }
      }
    });
  }

  function renderVo2MaxChart(series) {
    const canvas = document.getElementById("vo2maxChart");
    const emptyMessage = document.getElementById("vo2maxEmpty");
    if (!canvas || !emptyMessage) return;

    if (!Array.isArray(series) || series.length === 0) {
      if (vo2MaxChartInstance) {
        vo2MaxChartInstance.destroy();
        vo2MaxChartInstance = null;
      }
      emptyMessage.textContent = "No VO2 Max data available for this range.";
      return;
    }

    emptyMessage.textContent = "";

    const labels = series.map(r => r.period_start);
    const values = series.map(r => r.vo2_max);

    const ctx = canvas.getContext("2d");

    if (vo2MaxChartInstance) {
      vo2MaxChartInstance.destroy();
    }

    vo2MaxChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "VO2 Max",
          data: values,
          borderColor: "#2ecc71",
          backgroundColor: "rgba(46, 204, 113, 0.2)",
          fill: true,
          tension: 0.25,
          pointRadius: 2,
          pointHoverRadius: 4
        }]
      },
      options: {
        responsive: true,
        interaction: {
          mode: "index",
          intersect: false
        },
        scales: {
          x: {
            ticks: {
              autoSkip: true,
              maxTicksLimit: 10
            }
          },
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: "VO2 Max"
            }
          }
        },
        plugins: {
          legend: {
            display: true
          }
        }
      }
    });
  }

  function renderWeightChart(series) {
    const canvas = document.getElementById("weightChart");
    const emptyMessage = document.getElementById("weightEmpty");
    if (!canvas || !emptyMessage) return;

    if (!Array.isArray(series) || series.length === 0) {
      if (weightChartInstance) {
        weightChartInstance.destroy();
        weightChartInstance = null;
      }
      emptyMessage.textContent = "No weight data available for this range.";
      return;
    }

    emptyMessage.textContent = "";

    const parsed = series
      .map((row) => {
        const label = row.period_start ?? row.date ?? row.day ?? row.time;
        const rawWeight =
          row.weight ??
          row.weight_kg ??
          row.weightKg ??
          row.body?.weight ??
          row.body?.weight_kg ??
          row.body?.weightKg;
        const value = Number(rawWeight);
        if (!label || !Number.isFinite(value)) return null;
        return { label, value };
      })
      .filter(Boolean);

    if (parsed.length === 0) {
      if (weightChartInstance) {
        weightChartInstance.destroy();
        weightChartInstance = null;
      }
      emptyMessage.textContent = "No weight data available for this range.";
      return;
    }

    const labels = parsed.map(r => r.label);
    const values = parsed.map(r => r.value);

    const ctx = canvas.getContext("2d");

    if (weightChartInstance) {
      weightChartInstance.destroy();
    }

    weightChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Weight",
          data: values,
          borderColor: "#f39c12",
          backgroundColor: "rgba(243, 156, 18, 0.2)",
          fill: true,
          tension: 0.25,
          pointRadius: 2,
          pointHoverRadius: 4
        }]
      },
      options: {
        responsive: true,
        interaction: {
          mode: "index",
          intersect: false
        },
        scales: {
          x: {
            ticks: {
              autoSkip: true,
              maxTicksLimit: 10
            }
          },
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: "Weight (kg)"
            }
          }
        },
        plugins: {
          legend: {
            display: true
          }
        }
      }
    });
  }

  async function refreshForRange(rangeKey) {
    const range = resolveRange(rangeKey);
    try {
      const [monthlyResult, vo2Result, weightResult] = await Promise.allSettled([
        loadMonthly(range),
        loadVo2Max(range),
        loadBodyComposition(range),
      ]);

      if (monthlyResult.status === "fulfilled") {
        renderPaceChart(monthlyResult.value);
        renderCombinedChart(monthlyResult.value);
      } else {
        throw monthlyResult.reason;
      }

      if (vo2Result.status === "fulfilled") {
        renderVo2MaxChart(vo2Result.value);
      } else {
        const emptyMessage = document.getElementById("vo2maxEmpty");
        if (emptyMessage) {
          emptyMessage.textContent = "Unable to load VO2 Max data.";
        }
      }

      if (weightResult.status === "fulfilled") {
        renderWeightChart(weightResult.value);
      } else {
        const emptyMessage = document.getElementById("weightEmpty");
        if (emptyMessage) {
          emptyMessage.textContent = "Unable to load weight data.";
        }
      }
    } catch (err) {
      console.error(err);
      const emptyMessage = document.getElementById("vo2maxEmpty");
      if (emptyMessage) {
        emptyMessage.textContent = "Unable to load VO2 Max data.";
      }
      const weightMessage = document.getElementById("weightEmpty");
      if (weightMessage) {
        weightMessage.textContent = "Unable to load weight data.";
      }
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    rangeSelect.addEventListener("change", (e) => {
      refreshForRange(e.target.value);
    });

    refreshForRange(rangeSelect.value);
  });
}
