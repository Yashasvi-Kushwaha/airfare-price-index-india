const API_BASE = "http://127.0.0.1:8000";

async function loadIndexData() {
    const res = await fetch(`${API_BASE}/api/index`);
    const data = await res.json();
    document.querySelector("#chart-section h2").textContent = `Median Fare by Route — ${data.date}`;
    renderRouteCards(data.routes);
    renderStressTable(data.routes);
    renderMedianChart(data.routes);
}

function renderRouteCards(routes) {
    const container = document.getElementById("route-cards");
    container.innerHTML = "";
    routes.forEach(r => {
        const change = r.raw_percent_change ?? 0;
        const cls = change >= 0 ? "positive" : "negative";
        container.innerHTML += `
            <div class="route-card">
                <h3>${r.route}</h3>
                <div class="stat ${cls}">${change >= 0 ? "+" : ""}${change}%</div>
                <div>Median: ₹${r.median_fare_today ?? "N/A"}</div>
                <div>Observations: ${r.n_observations_today}</div>
            </div>
        `;
    });
}

function renderStressTable(routes) {
    const tbody = document.getElementById("stress-table-body");
    tbody.innerHTML = "";
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
    });
}

let chartInstance = null;
function renderMedianChart(routes) {
    const ctx = document.getElementById("medianChart").getContext("2d");
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
}

async function loadObservations(originDest) {
    const [origin, destination] = originDest.split("/");
    const res = await fetch(`${API_BASE}/api/observations/${origin}/${destination}`);
    const data = await res.json();
    const tbody = document.getElementById("obs-table-body");
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

document.getElementById("route-select").addEventListener("change", (e) => {
    loadObservations(e.target.value);
});



let historyChartInstance = null;
async function loadMedianHistory(origin, destination) {
    const res = await fetch(`${API_BASE}/api/median-history/${origin}/${destination}`);
    const data = await res.json();

    const ctx = document.getElementById("historyChart").getContext("2d");
    const labels = data.map(d => d.date);
    const medians = data.map(d => d.median_fare ?? 0);

    if (historyChartInstance) historyChartInstance.destroy();
    historyChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{ label: `${origin}-${destination} Median Fare Over Time`, data: medians }]
        }
    });
}


loadIndexData();
loadObservations("DEL/BOM");
loadMedianHistory("DEL", "BOM");