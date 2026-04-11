function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatEur(value) {
    const amount = Number(value) || 0;
    return new Intl.NumberFormat("de-DE", {
        style: "currency",
        currency: "EUR",
        maximumFractionDigits: 2,
    }).format(amount);
}

function formatNumber(value) {
    return new Intl.NumberFormat("de-DE").format(Number(value) || 0);
}

async function fetchJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`Request failed for ${url}`);
    }
    return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
    const chartCanvas = document.getElementById("pulse-chart");
    const topList = document.getElementById("pulse-top-list");
    const platformBreakdown = document.getElementById("pulse-platform-breakdown");
    const latestBody = document.getElementById("pulse-latest-body");
    const liveBody = document.getElementById("pulse-live-body");
    const queryBody = document.getElementById("pulse-query-body");
    const liveStatus = document.getElementById("pulse-live-status");
    const queryStatus = document.getElementById("pulse-query-status");
    const totalRevenue = document.getElementById("pulse-total-revenue");
    const todayRevenue = document.getElementById("pulse-today-revenue");
    const activeCreators = document.getElementById("pulse-active-creators");
    const recordCount = document.getElementById("pulse-record-count");
    const collectorStatus = document.getElementById("pulse-collector-status");
    const queryForm = document.getElementById("pulse-query-form");
    const resetButton = document.getElementById("pulse-query-reset");
    const platformTabs = Array.from(document.querySelectorAll(".pulse-tab"));

    if (
        !chartCanvas ||
        !topList ||
        !platformBreakdown ||
        !latestBody ||
        !liveBody ||
        !queryBody ||
        !liveStatus ||
        !queryStatus ||
        !totalRevenue ||
        !todayRevenue ||
        !activeCreators ||
        !recordCount ||
        !collectorStatus ||
        !queryForm ||
        !resetButton
    ) {
        return;
    }

    let revenueChart = null;

    function renderTableRows(target, rows, columns) {
        if (!Array.isArray(rows) || rows.length === 0) {
            target.innerHTML = `<tr><td colspan="${columns.length}">Keine Daten vorhanden.</td></tr>`;
            return;
        }

        target.innerHTML = rows
            .map((row) => {
                const cells = columns
                    .map((column) => {
                        const value = column.render ? column.render(row) : row[column.key];
                        const className = column.className ? ` class="${column.className}"` : "";
                        return `<td${className}>${value}</td>`;
                    })
                    .join("");
                return `<tr>${cells}</tr>`;
            })
            .join("");
    }

    function renderKpis(summary) {
        totalRevenue.textContent = formatEur(summary.total_revenue);
        todayRevenue.textContent = formatEur(summary.today_revenue);
        activeCreators.textContent = formatNumber(summary.active_creators);
        recordCount.textContent = formatNumber(summary.record_count);
        collectorStatus.textContent =
            summary.collector_status === "active"
                ? "Collector aktiv und mit Feed verbunden"
                : "Collector bereit, aber noch ohne Datensaetze";
    }

    function renderChart(summary) {
        if (typeof Chart === "undefined") {
            return;
        }

        if (revenueChart) {
            revenueChart.destroy();
        }

        revenueChart = new Chart(chartCanvas.getContext("2d"), {
            type: "line",
            data: {
                labels: summary.labels,
                datasets: [
                    {
                        label: "Revenue (EUR)",
                        data: summary.values,
                        borderColor: "#00ff9f",
                        backgroundColor: "rgba(0, 255, 159, 0.14)",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: "#f6f7fb",
                        },
                    },
                },
                scales: {
                    x: {
                        ticks: { color: "#98a2b3" },
                        grid: { color: "rgba(255,255,255,0.05)" },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: "#98a2b3" },
                        grid: { color: "rgba(255,255,255,0.05)" },
                    },
                },
            },
        });
    }

    function renderTopCreators(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            topList.innerHTML = '<div class="pulse-empty">Noch keine Creator-Daten vorhanden.</div>';
            return;
        }

        topList.innerHTML = rows
            .map(
                (row) => `
                    <div class="pulse-ranking-item">
                        <div class="pulse-ranking-name">${escapeHtml(row.name)}</div>
                        <div class="pulse-ranking-value">${formatEur(row.sum)}</div>
                    </div>
                `,
            )
            .join("");
    }

    function renderPlatformBreakdown(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            platformBreakdown.innerHTML = '<div class="pulse-empty">Noch keine Plattform-Daten vorhanden.</div>';
            return;
        }

        platformBreakdown.innerHTML = rows
            .map(
                (row) => `
                    <div class="pulse-breakdown-item">
                        <div class="pulse-breakdown-name">${escapeHtml(row.platform)}</div>
                        <div class="pulse-breakdown-value">${formatEur(row.total)}</div>
                    </div>
                `,
            )
            .join("");
    }

    function renderLatest(rows) {
        renderTableRows(latestBody, rows, [
            { key: "zeitpunkt", render: (row) => escapeHtml(row.zeitpunkt) },
            { key: "platform", render: (row) => escapeHtml(row.platform || "-") },
            { key: "quelle", render: (row) => escapeHtml(row.quelle || "-") },
            { key: "betrag", render: (row) => formatEur(row.betrag), className: "pulse-table-amount" },
            { key: "details", render: (row) => escapeHtml(row.details || "-") },
        ]);
    }

    async function loadSummary() {
        const summary = await fetchJson("/api/einnahmen/summary");
        renderKpis(summary);
        renderChart(summary);
        renderTopCreators(summary.top_gifter);
        renderPlatformBreakdown(summary.platform_totals);
        renderLatest(summary.latest);
        queryStatus.textContent = `Summary geladen: ${formatNumber(summary.record_count)} Records verfuegbar.`;
    }

    async function loadLive(platform) {
        liveStatus.textContent = `Lade ${platform} Feed...`;
        const rows = await fetchJson(`/api/live/${platform}`);
        renderTableRows(liveBody, rows, [
            { key: "zeitpunkt", render: (row) => escapeHtml(row.zeitpunkt) },
            { key: "quelle", render: (row) => escapeHtml(row.quelle || "-") },
            { key: "typ", render: (row) => escapeHtml(row.typ || "-") },
            { key: "betrag", render: (row) => formatEur(row.betrag), className: "pulse-table-amount" },
        ]);
        liveStatus.textContent = rows.length
            ? `${rows.length} Eintraege fuer ${platform} geladen.`
            : `Keine Eintraege fuer ${platform} gefunden.`;
    }

    async function runQuery() {
        queryStatus.textContent = "Query laeuft...";
        const formData = new FormData(queryForm);
        const payload = Object.fromEntries(formData.entries());

        const rows = await fetchJson("/api/einnahmen/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        renderTableRows(queryBody, rows, [
            { key: "zeitpunkt", render: (row) => escapeHtml(row.zeitpunkt) },
            { key: "quelle", render: (row) => escapeHtml(row.quelle || "-") },
            { key: "typ", render: (row) => escapeHtml(row.typ || "-") },
            { key: "betrag", render: (row) => formatEur(row.betrag), className: "pulse-table-amount" },
            { key: "details", render: (row) => escapeHtml(row.details || "-") },
        ]);

        queryStatus.textContent = rows.length
            ? `${rows.length} Query-Treffer geladen.`
            : "Keine Treffer fuer die aktuelle Query.";
    }

    platformTabs.forEach((button) => {
        button.addEventListener("click", async () => {
            platformTabs.forEach((tab) => tab.classList.toggle("is-active", tab === button));
            try {
                await loadLive(button.dataset.platform);
            } catch {
                liveStatus.textContent = "Live-Feed konnte nicht geladen werden.";
            }
        });
    });

    queryForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await runQuery();
        } catch {
            queryStatus.textContent = "Query konnte nicht geladen werden.";
        }
    });

    resetButton.addEventListener("click", async () => {
        queryForm.reset();
        queryBody.innerHTML = '<tr><td colspan="5">Noch keine Query ausgefuehrt.</td></tr>';
        queryStatus.textContent = "Filter zurueckgesetzt.";
        try {
            await loadSummary();
        } catch {
            queryStatus.textContent = "Summary konnte nach Reset nicht geladen werden.";
        }
    });

    Promise.all([loadSummary(), loadLive("tiktok")]).catch(() => {
        liveStatus.textContent = "Initiale Pulse-Daten konnten nicht geladen werden.";
        queryStatus.textContent = "Initiale Pulse-Daten konnten nicht geladen werden.";
    });
});
