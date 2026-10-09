// ==============================================================================
// PREDICTIONS & SMART INSIGHTS CONTROLLER
// ==============================================================================

window.loadPredictions = async function() {
    await Promise.all([
        loadSmartInsights(),
        runIntegratedSimulation()
    ]);
};

async function loadSmartInsights() {
    try {
        const res = await apiFetch("/api/insights/smart-summary");
        if (!res.success) return;

        const container = document.getElementById("smartInsightsContainer");
        if (!container) return;

        container.innerHTML = res.insights.insights.map(ins => `
            <div class="insight-card">
                <div>
                    <div class="insight-top">
                        <span class="badge ${ins.badge_class}">${ins.badge}</span>
                        <span style="font-size:0.76rem; color:var(--text-muted);"><i class="fa-solid ${ins.icon}"></i> ${ins.category}</span>
                    </div>
                    <h3 class="insight-title">${ins.title}</h3>
                    <div class="insight-metric">${ins.metric_value} <span style="font-size:0.76rem; font-weight:500; color:var(--text-secondary);">${ins.metric_label}</span></div>
                    <p class="insight-body">${ins.summary}</p>
                </div>
                <div class="insight-action">
                    <strong>Recommended Manager Action:</strong>
                    ${ins.action}
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.error("Failed to load smart insights:", e);
    }
}

async function runIntegratedSimulation() {
    const checkout = parseFloat(document.getElementById("simCheckoutPrice")?.value || 250);
    const base = parseFloat(document.getElementById("simBasePrice")?.value || 300);
    const emailPromo = document.getElementById("simEmailPromo")?.checked ? 1 : 0;
    const homePromo = document.getElementById("simHomePromo")?.checked ? 1 : 0;
    const centerType = document.getElementById("simCenterType")?.value || "TYPE_A";
    const category = document.getElementById("simCategory")?.value || "Rice Bowl";
    const cuisine = document.getElementById("simCuisine")?.value || "Indian";

    try {
        const res = await apiFetch("/api/predictions/forecast", {
            method: "POST",
            body: {
                checkout_price: checkout,
                base_price: base,
                emailer_for_promotion: emailPromo,
                homepage_featured: homePromo,
                center_type: centerType,
                category: category,
                cuisine: cuisine
            }
        });
        if (!res.success) return;

        const q = res.quantitative_forecast;
        const c = res.categorical_classification;

        document.getElementById("simResultDemand").textContent = `${q.forecasted_demand.toLocaleString()} units`;
        document.getElementById("simResultPrep").textContent = `${q.recommended_preparation_qty.toLocaleString()} units`;
        document.getElementById("simResultBuffer").textContent = `${q.recommended_safety_buffer_pct}% Buffer`;
        document.getElementById("simResultWaste").textContent = `${q.estimated_surplus_waste_units.toLocaleString()} units (${q.projected_waste_percentage}%)`;
        document.getElementById("simResultLoss").textContent = `$${q.estimated_waste_cost.toLocaleString()}`;
        document.getElementById("simResultRevenue").textContent = `$${q.projected_revenue.toLocaleString()}`;

        const badge = document.getElementById("simResultTierBadge");
        badge.textContent = `${c.predicted_demand_tier} DEMAND TIER`;
        badge.className = `badge ${c.predicted_demand_tier === 'HIGH' ? 'badge-success' : c.predicted_demand_tier === 'MEDIUM' ? 'badge-info' : 'badge-warning'}`;

        document.getElementById("simResultRecommendation").textContent = q.waste_optimization_note;
    } catch (e) {
        console.error("Simulation error:", e);
    }
}
