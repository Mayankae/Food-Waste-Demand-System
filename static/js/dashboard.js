// ==============================================================================
// DASHBOARD CONTROLLER & CHARTS
// ==============================================================================

window.loadDashboard = async function() {
    try {
        const [kpiRes, chartsRes] = await Promise.all([
            apiFetch("/api/dashboard/kpis"),
            apiFetch("/api/dashboard/charts")
        ]);

        if (kpiRes.success) renderKPIs(kpiRes.kpis);
        if (chartsRes.success) renderCharts(chartsRes.charts);
    } catch (err) {
        console.error("Dashboard load failed:", err);
    }
};

function renderKPIs(kpis) {
    document.getElementById("kpiTotalPrepared").textContent = formatNumber(kpis.total_food_prepared);
    document.getElementById("kpiTotalSold").textContent = formatNumber(kpis.total_food_sold);
    document.getElementById("kpiTotalWasted").textContent = formatNumber(kpis.total_food_wasted);
    document.getElementById("kpiWastePercentage").textContent = `${kpis.overall_waste_percentage}%`;
    document.getElementById("kpiWasteCost").textContent = formatCurrency(kpis.total_waste_cost);
    document.getElementById("kpiTotalRevenue").textContent = formatCurrency(kpis.total_revenue);
    document.getElementById("kpiActiveCenters").textContent = kpis.active_fulfillment_centers;
    document.getElementById("kpiMenuItems").textContent = kpis.monitored_menu_items;
}

function renderCharts(charts) {
    // 1. Monthly Demand vs Waste Timeline
    const timelineData = charts.monthly_timeline || [];
    const ctxTimeline = document.getElementById("chartMonthlyDemandWaste");
    if (ctxTimeline) {
        if (AppState.charts.timeline) AppState.charts.timeline.destroy();
        AppState.charts.timeline = new Chart(ctxTimeline, {
            type: "bar",
            data: {
                labels: timelineData.map(d => d.month_name),
                datasets: [
                    {
                        label: "Food Sold (Orders)",
                        data: timelineData.map(d => d.demand_sold),
                        backgroundColor: "rgba(56, 189, 248, 0.75)",
                        borderRadius: 4
                    },
                    {
                        label: "Food Wasted (Units)",
                        data: timelineData.map(d => d.food_wasted),
                        backgroundColor: "rgba(244, 63, 94, 0.8)",
                        borderRadius: 4
                    },
                    {
                        type: "line",
                        label: "Waste % Rate",
                        data: timelineData.map(d => d.waste_pct),
                        borderColor: "#f59e0b",
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: "y1"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } } }
                },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y1: {
                        position: "right",
                        ticks: { color: "#f59e0b", callback: v => v + "%" },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    // 2. Top Wasted Items Horizontal Bar
    const topWasted = charts.top_wasted_items || [];
    const ctxTopWasted = document.getElementById("chartTopWasted");
    if (ctxTopWasted) {
        if (AppState.charts.topWasted) AppState.charts.topWasted.destroy();
        AppState.charts.topWasted = new Chart(ctxTopWasted, {
            type: "bar",
            data: {
                labels: topWasted.map(d => d.item_name),
                datasets: [{
                    label: "Wasted Units",
                    data: topWasted.map(d => d.total_waste_units),
                    backgroundColor: "rgba(239, 68, 68, 0.75)",
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#e2e8f0", font: { size: 11 } }, grid: { display: false } }
                }
            }
        });
    }

    // 3. Cuisine Waste Doughnut Chart
    const cuisineData = charts.cuisine_breakdown || [];
    const ctxCuisine = document.getElementById("chartCuisineWaste");
    if (ctxCuisine) {
        if (AppState.charts.cuisine) AppState.charts.cuisine.destroy();
        AppState.charts.cuisine = new Chart(ctxCuisine, {
            type: "doughnut",
            data: {
                labels: cuisineData.map(d => d.cuisine),
                datasets: [{
                    data: cuisineData.map(d => d.waste),
                    backgroundColor: [
                        "rgba(16, 185, 129, 0.8)",
                        "rgba(56, 189, 248, 0.8)",
                        "rgba(245, 158, 11, 0.8)",
                        "rgba(168, 85, 247, 0.8)"
                    ],
                    borderColor: "#1e293b",
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } } }
                }
            }
        });
    }

    // 4. Center Type Performance
    const centerData = charts.center_performance || [];
    const ctxCenter = document.getElementById("chartCenterPerformance");
    if (ctxCenter) {
        if (AppState.charts.center) AppState.charts.center.destroy();
        AppState.charts.center = new Chart(ctxCenter, {
            type: "bar",
            data: {
                labels: centerData.map(d => d.center_type),
                datasets: [
                    {
                        label: "Average Waste %",
                        data: centerData.map(d => d.waste_pct),
                        backgroundColor: "rgba(245, 158, 11, 0.75)",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
                    y: { ticks: { color: "#94a3b8", callback: v => v + "%" }, grid: { color: "rgba(255,255,255,0.05)" } }
                }
            }
        });
    }
}

// Helpers
function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(2) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return (num || 0).toLocaleString();
}
function formatCurrency(val) {
    if (val >= 1000000000) return "$" + (val / 1000000000).toFixed(2) + "B";
    if (val >= 1000000) return "$" + (val / 1000000).toFixed(2) + "M";
    if (val >= 1000) return "$" + (val / 1000).toFixed(1) + "K";
    return "$" + (val || 0).toLocaleString();
}
