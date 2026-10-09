// ==============================================================================
// REPORTS & AUDIT CONTROLLER
// ==============================================================================

window.loadReports = async function() {
    try {
        const res = await apiFetch("/api/reports/summary");
        if (!res.success) return;

        const r = res.report;

        document.getElementById("reportTotalLoss").textContent = `$${r.total_waste_cost.toLocaleString()}`;
        document.getElementById("reportTargetSavings").textContent = `$${r.projected_savings_target.toLocaleString()}`;
        document.getElementById("reportCategoriesAudited").textContent = r.total_categories_audited;

        // Render Category Scorecard Table
        const tbody = document.getElementById("reportScorecardTableBody");
        if (tbody && r.category_scorecard) {
            tbody.innerHTML = r.category_scorecard.map(c => `
                <tr>
                    <td><strong>${c.category_name}</strong></td>
                    <td>${c.food_group}</td>
                    <td><span class="badge badge-neutral">${c.spoilage_sensitivity}</span></td>
                    <td>${c.prepared_units.toLocaleString()}</td>
                    <td><span style="color:var(--accent-blue);">${c.sold_units.toLocaleString()}</span></td>
                    <td><span style="color:var(--accent-rose); font-weight:700;">${c.wasted_units.toLocaleString()}</span></td>
                    <td>
                        <span class="badge ${c.waste_percentage > 14 ? 'badge-danger' : c.waste_percentage > 10 ? 'badge-warning' : 'badge-success'}">
                            ${c.waste_percentage}%
                        </span>
                    </td>
                    <td><strong>$${c.waste_cost_dollars.toLocaleString()}</strong></td>
                    <td>$${c.revenue_dollars.toLocaleString()}</td>
                    <td>
                        <span class="badge ${c.efficiency_rating === 'URGENT INTERVENTION' ? 'badge-danger' : c.efficiency_rating === 'ATTENTION NEEDED' ? 'badge-warning' : 'badge-success'}">
                            ${c.efficiency_rating}
                        </span>
                    </td>
                </tr>
            `).join("");
        }

        // Render Top Waste Centers
        const centerTbody = document.getElementById("reportCentersTableBody");
        if (centerTbody && r.top_waste_centers) {
            centerTbody.innerHTML = r.top_waste_centers.map(fc => `
                <tr>
                    <td>#${fc.center_id}</td>
                    <td><strong>${fc.center_name}</strong></td>
                    <td><span class="badge badge-neutral">${fc.center_type}</span></td>
                    <td>${fc.op_area} km²</td>
                    <td><span style="color:var(--accent-rose); font-weight:700;">${fc.wasted_units.toLocaleString()}</span></td>
                    <td>${fc.waste_percentage}%</td>
                    <td><strong>$${fc.waste_cost_dollars.toLocaleString()}</strong></td>
                </tr>
            `).join("");
        }
    } catch (e) {
        console.error("Failed to load reports:", e);
    }
};

window.exportWarehouseCSV = function() {
    window.location.href = "/api/reports/export-csv";
};
