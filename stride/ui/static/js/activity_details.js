const activitySummary = document.getElementById("activitySummary");
const chartsContainer = document.getElementById("chartsContainer");
const errorContainer = document.getElementById("errorContainer");
const hrPaceCanvasEl = document.getElementById("hrPaceChart");
const elevationCanvasEl = document.getElementById("elevationChart");

if (activitySummary && chartsContainer && errorContainer && hrPaceCanvasEl && elevationCanvasEl) {
  const activityIdRaw = activitySummary.dataset.activityId || "";
  const ACTIVITY_ID = Number(activityIdRaw);

  let hrPaceChart = null;
  let elevationChart = null;
  let hrZones = null;

  const zoneColors = {
    1: "#4e73df",  // Zone 1 - Light blue
    2: "#36a2eb",  // Zone 2 - Medium blue
    3: "#2ecc71",  // Zone 3 - Green
    4: "#f39c12",  // Zone 4 - Orange
    5: "#e74c3c",  // Zone 5 - Red
  };

  const zoneNames = {
    1: "Zone 1 (50-60%)",
    2: "Zone 2 (60-70%)",
    3: "Zone 3 (70-80%)",
    4: "Zone 4 (80-90%)",
    5: "Zone 5 (90-100%)",
  };

  function getHRZone(hr) {
    if (!hrZones || !Array.isArray(hrZones.zones)) return null;
    for (const zone of hrZones.zones) {
      if (hr >= zone.min_bpm && hr <= zone.max_bpm) {
        return zone.zone;
      }
    }
    return null;
  }

  function getZoneColor(zone) {
    return zoneColors[zone] || "#999";
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

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  async function fetchActivityDetails() {
    try {
      const resp = await fetch(`/api/activities/details/${ACTIVITY_ID}`);
      if (!resp.ok) throw new Error(`Failed to fetch activity details: ${resp.status}`);
      return await resp.json();
    } catch (error) {
      console.error("Error fetching activity details:", error);
      throw error;
    }
  }

  async function fetchHRZones() {
    try {
      const resp = await fetch("/api/hr/zones");
      if (!resp.ok) throw new Error(`Failed to fetch HR zones: ${resp.status}`);
      return await resp.json();
    } catch (error) {
      console.error("Error fetching HR zones:", error);
      return null;
    }
  }

  function renderActivitySummary(data, activityInfo) {
    if (!data || !Array.isArray(data.series)) {
      activitySummary.innerHTML = '<div class="error-message">No activity data available</div>';
      return;
    }

    if (!activityInfo) {
      activitySummary.innerHTML = '<div class="error-message">No activity summary available</div>';
      return;
    }

    // Use summary data for distance, duration, and HR
    const totalDistance = (activityInfo.distance_m || 0) / 1000;
    const totalDuration = activityInfo.duration_s || 0;
    const avgHR = activityInfo.avg_hr_bpm || 0;
    const maxHR = activityInfo.max_hr_bpm || 0;

    // Find max altitude from series for elevation gain
    const maxAltitude = Math.max(...data.series.map(p => p.altitude || 0));
    const minAltitude = Math.min(...data.series.map(p => p.altitude || Infinity));
    const elevationGain = Math.max(0, maxAltitude - minAltitude);

    const summaryHTML = `
      <div style="margin-bottom: 1.5rem;">
        <h2 class="subtitle" style="margin-bottom: 0.5rem;">${activityInfo?.activity_name || "Activity"}</h2>
        <p class="has-text-grey">${formatDate(activityInfo?.start || new Date().toISOString())}</p>
      </div>

      <div class="activity-summary">
        <div class="summary-card primary">
          <div class="summary-label">Distance</div>
          <div class="summary-value">${totalDistance.toFixed(2)}</div>
          <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">km</div>
        </div>

        <div class="summary-card info">
          <div class="summary-label">Duration</div>
          <div class="summary-value">${formatDuration(totalDuration)}</div>
        </div>

        <div class="summary-card success">
          <div class="summary-label">Average HR</div>
          <div class="summary-value">${Math.round(avgHR)}</div>
          <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">bpm</div>
        </div>

        <div class="summary-card danger">
          <div class="summary-label">Max HR</div>
          <div class="summary-value">${Math.round(maxHR)}</div>
          <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">bpm</div>
        </div>

        <div class="summary-card warning">
          <div class="summary-label">Pace</div>
          <div class="summary-value">${activityInfo?.pace_mn_per_km || "–"}</div>
          <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">min/km</div>
        </div>

        <div class="summary-card">
          <div class="summary-label">Elevation Gain</div>
          <div class="summary-value">${Math.round(elevationGain)}</div>
          <div style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">m</div>
        </div>
      </div>
    `;

    activitySummary.innerHTML = summaryHTML;
  }

  function renderZoneLegend() {
    const legendEl = document.getElementById("zoneLegend");
    if (!hrZones || !Array.isArray(hrZones.zones)) return;

    legendEl.innerHTML = hrZones.zones.map(zone => `
      <div class="zone-legend-item">
        <div class="zone-legend-color" style="background-color: ${getZoneColor(zone.zone)};"></div>
        <span>Zone ${zone.zone}: ${zone.min_bpm}-${zone.max_bpm} bpm</span>
      </div>
    `).join("");
  }

  function createHRPaceChart(data) {
    if (!Array.isArray(data.series)) return;

    // Filter points with distance > 0 and HR data
    const points = data.series.filter(p =>
      p.distance_m && p.distance_m > 0 && p.hr && p.hr > 0
    );

    if (points.length === 0) {
      hrPaceCanvasEl.parentElement.innerHTML = '<p class="has-text-grey">No HR data available</p>';
      return;
    }

    const distances = points.map(p => (p.distance_m / 1000).toFixed(2));
    const hrValues = points.map(p => p.hr);
    const paceValues = points.map(p => {
      if (p.pace_mn_per_km) {
        const parts = p.pace_mn_per_km.split(":");
        const mins = parseInt(parts[0]);
        const secs = parseInt(parts[1]);
        return (mins * 60 + secs) / 60; // Divide by 60 for chart
      }
      return 0;
    });

    // Create color array based on HR zones
    const backgroundColor = hrValues.map(hr => {
      const zone = getHRZone(hr);
      return getZoneColor(zone) + "40";  // Add transparency
    });

    const borderColor = hrValues.map(hr => {
      const zone = getHRZone(hr);
      return getZoneColor(zone);
    });

    if (hrPaceChart) {
      hrPaceChart.destroy();
    }

    // Plugin to draw HR zone background shading
    const zoneBackgroundPlugin = {
      id: 'zoneBackground',
      afterDatasetsDraw(chart) {
        const ctx = chart.ctx;
        const yScale = chart.scales.y;
        const chartArea = chart.chartArea;

        if (!hrZones || !Array.isArray(hrZones.zones)) return;

        hrZones.zones.forEach(zone => {
          const minPixel = yScale.getPixelForValue(zone.min_bpm);
          const maxPixel = yScale.getPixelForValue(zone.max_bpm);
          const color = getZoneColor(zone.zone);

          ctx.fillStyle = color + "15"; // Very light transparency
          ctx.fillRect(chartArea.left, maxPixel, chartArea.width, minPixel - maxPixel);
        });
      }
    };

    hrPaceChart = new Chart(hrPaceCanvasEl, {
      type: "line",
      data: {
        labels: distances,
        datasets: [
          {
            label: "Heart Rate (bpm)",
            data: hrValues,
            borderColor: "#e74c3c",
            backgroundColor: "rgba(231, 76, 60, 0.15)",
            borderWidth: 2,
            pointRadius: 0,
            pointBackgroundColor: "#e74c3c",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            tension: 0.2,
            yAxisID: "y",
          },
          {
            label: "Pace (min/km)",
            data: paceValues,
            borderColor: "#4e73df",
            backgroundColor: "rgba(78, 115, 223, 0.15)",
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 0,
            tension: 0.2,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
          filler: {
            propagate: true,
          },
          tooltip: {
            propagate: true,
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                if (context.datasetIndex === 0) {
                  const hr = context.parsed.y;
                  return `Heart Rate: ${hr} bpm`;
                } else if (context.datasetIndex === 1) {
                  const pointIndex = context.dataIndex;
                  const pace = points[pointIndex].pace_mn_per_km;
                  return `Pace: ${pace}`;
                }
              },
              afterLabel: function (context) {
                if (context.datasetIndex === 0) {
                  const hr = context.parsed.y;
                  const zone = getHRZone(hr);
                  return zone ? `Zone ${zone}` : "";
                }
              },
            },
          },
        },
        scales: {
          y: {
            type: "linear",
            display: true,
            position: "left",
            title: {
              display: true,
              text: "Heart Rate (bpm)",
              color: "#e74c3c",
            },
            ticks: {
              color: "#e74c3c",
            },
            grid: {
              color: "rgba(231, 76, 60, 0.1)",
            },
          },
          y1: {
            type: "linear",
            display: true,
            position: "right",
            reverse: true,
            title: {
              display: true,
              text: "Pace (min/km)",
              color: "#4e73df",
            },
            ticks: {
              color: "#4e73df",
            },
            grid: {
              drawOnChartArea: false,
            },
          },
          x: {
            title: {
              display: true,
              text: "Distance (km)",
            },
          },
        },
      },
      plugins: [zoneBackgroundPlugin],
    });
  }

  function createElevationChart(data) {
    if (!Array.isArray(data.series)) return;

    // Filter points with distance and altitude data
    const points = data.series.filter(p =>
      p.distance_m && p.distance_m > 0 && p.altitude != null
    );

    if (points.length === 0) {
      elevationCanvasEl.parentElement.innerHTML = '<p class="has-text-grey">No elevation data available</p>';
      return;
    }

    const distances = points.map(p => (p.distance_m / 1000).toFixed(2));
    const altitudes = points.map(p => Math.round(p.altitude));

    if (elevationChart) {
      elevationChart.destroy();
    }

    elevationChart = new Chart(elevationCanvasEl, {
      type: "line",
      data: {
        labels: distances,
        datasets: [
          {
            label: "Altitude (m)",
            data: altitudes,
            borderColor: "#36a2eb",
            backgroundColor: "rgba(54, 162, 235, 0.1)",
            borderWidth: 2,
            fill: true,
            pointRadius: 2,
            pointBackgroundColor: "#36a2eb",
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: "top",
          },
        },
        scales: {
          y: {
            title: {
              display: true,
              text: "Altitude (m)",
            },
          },
          x: {
            title: {
              display: true,
              text: "Distance (km)",
            },
          },
        },
      },
    });
  }

  function createActivityMap(data) {
    console.log("createActivityMap called", { hasData: !!data, seriesLength: data?.series?.length });

    if (!Array.isArray(data.series)) {
      console.warn("No series data in activity data");
      return;
    }

    // Check if Leaflet is loaded
    if (typeof L === 'undefined') {
      console.error("Leaflet library not loaded");
      document.getElementById("mapContainer").innerHTML = '<p class="has-text-grey">Leaflet library not loaded</p>';
      return;
    }

    // Filter points with location data
    const points = data.series.filter(p =>
      p.latitude != null && p.longitude != null
    );

    // Further filter for points with HR data for HR zone coloring
    const pointsWithHR = points.filter(p => p.hr != null && p.hr > 0);

    console.log(`Total points: ${data.series.length}, Points with location: ${points.length}, Points with HR: ${pointsWithHR.length}`);

    if (points.length === 0) {
      console.warn("No points with location data");
      document.getElementById("mapContainer").innerHTML = '<p class="has-text-grey">No location data available for this activity</p>';
      return;
    }

    // Use points with HR if available for better coloring, otherwise use all points with location
    const displayPoints = pointsWithHR.length > 0 ? pointsWithHR : points;
    console.log(`Using ${displayPoints.length} points for display`);

    // Calculate map bounds
    const latitudes = displayPoints.map(p => p.latitude);
    const longitudes = displayPoints.map(p => p.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLon = Math.min(...longitudes);
    const maxLon = Math.max(...longitudes);

    console.log(`Map bounds: lat [${minLat}, ${maxLat}], lon [${minLon}, ${maxLon}]`);

    // Create map
    try {
      console.log("Initializing Leaflet map...");
      const mapContainer = document.getElementById('mapContainer');

      if (!mapContainer) {
        console.error("Map container not found!");
        return;
      }

      const map = L.map('mapContainer').fitBounds([
        [minLat, minLon],
        [maxLat, maxLon]
      ], { padding: [50, 50] });

      console.log("Map created, adding tile layer...");
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(map);

      console.log(`Drawing ${displayPoints.length - 1} polyline segments...`);
      // Draw trace with color coding by HR zone
      for (let i = 0; i < displayPoints.length - 1; i++) {
        const p1 = displayPoints[i];
        const p2 = displayPoints[i + 1];
        const zone = p1.hr ? getHRZone(p1.hr) : null;
        const color = getZoneColor(zone);

        L.polyline([
          [p1.latitude, p1.longitude],
          [p2.latitude, p2.longitude]
        ], {
          color: color,
          weight: 6,
          opacity: 1,
          className: zone ? `zone-${zone}` : "zone-unknown"
        }).addTo(map);
      }

      console.log("Adding start/end markers...");
      // Add start and end markers
      L.circleMarker([displayPoints[0].latitude, displayPoints[0].longitude], {
        radius: 8,
        fillColor: '#2ecc71',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8,
        title: 'Start'
      }).addTo(map).bindPopup('Activity Start');

      L.circleMarker([displayPoints[displayPoints.length - 1].latitude, displayPoints[displayPoints.length - 1].longitude], {
        radius: 8,
        fillColor: '#e74c3c',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8,
        title: 'End'
      }).addTo(map).bindPopup('Activity End');

      console.log("Rendering map legend...");
      // Render map legend
      const mapZoneLegendEl = document.getElementById("mapZoneLegend");
      if (hrZones && Array.isArray(hrZones.zones)) {
        mapZoneLegendEl.innerHTML = hrZones.zones.map(zone => `
          <div class="zone-legend-item">
            <div class="zone-legend-color" style="background-color: ${getZoneColor(zone.zone)};"></div>
            <span>Zone ${zone.zone}: ${zone.min_bpm}-${zone.max_bpm} bpm</span>
          </div>
        `).join("");
      }
      console.log("Map created successfully!");
    } catch (err) {
      console.error("Error creating map:", err, err.stack);
      document.getElementById("mapContainer").innerHTML = '<p class="has-text-grey">Error loading map: ' + err.message + '</p>';
    }
  }

  async function initPage() {
    try {
      // Fetch data in parallel
      const [activityData, zones, activityInfo] = await Promise.all([
        fetchActivityDetails(),
        fetchHRZones(),
        fetch(`/api/activities/${ACTIVITY_ID}`)
          .then(r => r.json())
          .then(d => d.activity),
      ]);

      hrZones = zones;

      // Render summary
      renderActivitySummary(activityData, activityInfo);

      // Render zone legend
      renderZoneLegend();

      // Create charts and map
      createHRPaceChart(activityData);
      createElevationChart(activityData);

      // Map creation - Leaflet is now guaranteed to be loaded from base template
      if (typeof L !== 'undefined') {
        console.log("Leaflet loaded, creating map...");
        createActivityMap(activityData);
      } else {
        console.warn("Leaflet still not available, will retry...");
        setTimeout(() => createActivityMap(activityData), 200);
      }

    } catch (error) {
      console.error("Error initializing page:", error);
      errorContainer.innerHTML = `
        <div class="error-message">
          <strong>Error:</strong> ${error.message}
        </div>
      `;
    }
  }

  // Wait for DOM and Leaflet script to load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }
}
