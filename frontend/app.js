const API_BASE = "http://127.0.0.1:8000";
if (sessionStorage.getItem("loggedIn") !== "true") {
    window.location.href = "login.html";
}
async function loadIndexData() {
    try {
        const res = await fetch(`${API_BASE}/api/index`);
        if (!res.ok) throw new Error(`API returned status ${res.status}`);
        const data = await res.json();
        console.log("Index data received:", data);

        const chartHeading = document.querySelector("#chart-section h2, #overview h2:nth-of-type(2)");
        if (chartHeading) chartHeading.textContent = `Median Fare by Route — ${data.date}`;

        renderRouteCards(data.routes);
        renderStressTable(data.routes);
        renderMedianChart(data.routes);
    } catch (err) {
        console.error("loadIndexData FAILED:", err);
        const container = document.getElementById("route-cards");
        if (container) container.innerHTML = `<p style="color:red;">Error loading index data: ${err.message}</p>`;
    }
}

function renderRouteCards(routes) {
    const container = document.getElementById("route-cards");
    if (!container) {
        console.error("renderRouteCards: #route-cards not found in DOM");
        return;
    }
    container.innerHTML = "";
    routes.forEach(r => {
        const change = r.raw_percent_change ?? 0;
        const cls = change >= 0 ? "positive" : "negative";
        container.innerHTML += `
            <div class="route-card">
                <h3>${r.route}</h3>
                <div class="stat ${cls}">${change >= 0 ? "+" : ""}${change}%</div>
                <div>Median: ₹${r.median_fare_today ?? "N/A"}</div>
                <div>Observations: ${r.n_observations_today ?? "N/A"}</div>
            </div>
        `;
    });
    console.log(`renderRouteCards: rendered ${routes.length} cards`);
}

function renderStressTable(routes) {
    const tbody = document.getElementById("stress-table-body");
    if (!tbody) {
        console.error("renderStressTable: #stress-table-body not found in DOM");
        return;
    }
    tbody.innerHTML = "";
    let rowsRendered = 0;
    routes.forEach(r => {
        if (r.raw_jevons_relative === undefined) return;
        tbody.innerHTML += `
            <tr>
                <td>${r.route}</td>
                <td>${r.matched_flights}</td>
                <td>${r.raw_percent_change}%</td>
                <td>${r.credibility_weighted_percent_change}%</td>
                <td>${r.stress_score_percent}%</td>
            </tr>
        `;
        rowsRendered++;
    });
    console.log(`renderStressTable: rendered ${rowsRendered} rows`);
}

let chartInstance = null;
function renderMedianChart(routes) {
    const canvas = document.getElementById("medianChart");
    if (!canvas) {
        console.error("renderMedianChart: #medianChart canvas not found in DOM");
        return;
    }
    const ctx = canvas.getContext("2d");
    const labels = routes.map(r => r.route);
    const medians = routes.map(r => r.median_fare_today ?? 0);

    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{ label: "Median Fare (₹)", data: medians }]
        }
    });
    console.log("renderMedianChart: chart created");
}

async function loadObservations(originDest) {
    const [origin, destination] = originDest.split("/");
    const res = await fetch(`${API_BASE}/api/observations/${origin}/${destination}`);
    const data = await res.json();
    const tbody = document.getElementById("obs-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";
    data.forEach(o => {
        tbody.innerHTML += `
            <tr>
                <td>${o.flight_number}</td>
                <td>${o.airline}</td>
                <td>${o.departure_time}</td>
                <td>₹${o.total_fare}</td>
                <td>${o.collection_timestamp}</td>
                <td>${o.source}</td>
            </tr>
        `;
    });
}

const routeSelect = document.getElementById("route-select");
if (routeSelect) {
    routeSelect.addEventListener("change", (e) => loadObservations(e.target.value));
}

let historyChartInstance = null;
async function loadMedianHistory(origin, destination) {
    const res = await fetch(`${API_BASE}/api/median-history/${origin}/${destination}`);
    const data = await res.json();
    const canvas = document.getElementById("historyChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const labels = data.map(d => d.date);
    const medians = data.map(d => d.median_fare ?? 0);

    if (historyChartInstance) historyChartInstance.destroy();
    historyChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{ label: `${origin}-${destination} Median Fare Over Time`, data: medians, fill: false, tension: 0.25 }]
        }
    });
}

let leadTimeChartInstance = null;
async function loadLeadTime(origin, destination) {
    try {
        const res = await fetch(`${API_BASE}/api/lead-time/${origin}/${destination}`);
        if (!res.ok) throw new Error("Failed to load lead-time data");
        const data = await res.json();

        const summaryDiv = document.getElementById("leadtime-summary");
        const t30 = data["T+30_median_fare"];
        const t7 = data["T+7_median_fare"];
        const increase = data.percent_increase_last_minute;

        if (summaryDiv && increase !== null && t30 !== null && t7 !== null) {
            const direction = increase >= 0 ? "higher" : "lower";
            summaryDiv.innerHTML = `<p><strong>${data.route}</strong>: T+7 fare is ${Math.abs(increase)}% ${direction} than T+30.</p>`;
        }

        const canvas = document.getElementById("leadTimeChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (leadTimeChartInstance) leadTimeChartInstance.destroy();
        leadTimeChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: ["T+30", "T+7"],
                datasets: [{ label: `${data.route} Median Fare`, data: [t30, t7], fill: false, tension: 0.25 }]
            }
        });
    } catch (err) {
        console.error("loadLeadTime FAILED:", err);
    }
}

// Initial load
loadIndexData();
loadObservations("DEL/BOM");
loadMedianHistory("DEL", "BOM");
loadLeadTime("DEL", "BOM");