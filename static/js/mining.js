// ==============================================================================
// DATA MINING STUDIO CONTROLLER
// 5 Core Models: Classification, Regression, Clustering, Apriori, Anomaly Detection
// ==============================================================================

window.loadMining = async function() {
    initMiningTabs();
    // Default load first active tab
    await loadClassificationModel();
};

function initMiningTabs() {
    document.querySelectorAll(".mining-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".mining-tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".mining-tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetId = btn.getAttribute("data-tab");
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add("active");

            // Lazy-load model data
            if (targetId === "paneClassification") loadClassificationModel();
            else if (targetId === "paneRegression") loadRegressionModel();
            else if (targetId === "paneClustering") loadClusteringModel();
            else if (targetId === "paneApriori") loadAprioriModel();
            else if (targetId === "paneAnomaly") loadAnomalyModel();
        });
    });
}

// ==============================================================================
// 1. CLASSIFICATION MODEL
// ==============================================================================
async function loadClassificationModel() {
    try {
        const res = await apiFetch("/api/mining/classification/evaluate");
        if (!res.success) return;

        const m = res.model;
        const setEl = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        setEl("clfAccuracy", `${m.metrics.accuracy}%`);
        setEl("clfPrecision", `${m.metrics.precision}%`);
        setEl("clfRecall", `${m.metrics.recall}%`);
        setEl("clfF1", `${m.metrics.f1_score}%`);
        setEl("clfAlgorithmDesc", `${m.algorithm} (Benchmark: Decision Tree ${m.metrics.accuracy_benchmark_dt}%)`);

        // Render Confusion Matrix (3x3: Actual on Y-axis, Predicted on X-axis)
        const cm = m.confusion_matrix;
        const cmContainer = document.getElementById("clfConfusionMatrix");
        if (cmContainer && cm && cm.matrix && cm.labels) {
            const rowTotals = cm.matrix.map(row => row.reduce((a, b) => a + b, 0));
            const colTotals = cm.labels.map((_, colIdx) => cm.matrix.reduce((sum, row) => sum + row[colIdx], 0));
            const totalAll = rowTotals.reduce((a, b) => a + b, 0);

            cmContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="data-table" style="text-align:center;">
                        <thead>
                            <tr style="background: rgba(15, 23, 42, 0.9);">
                                <th style="text-align:left; color:#94a3b8; font-weight:700;">Actual (Y) \\ Predicted (X)</th>
                                ${cm.labels.map(l => `<th style="color:var(--accent-blue); font-weight:700;">Pred: ${l}</th>`).join("")}
                                <th style="color:var(--primary-light); font-weight:700;">Total Actual</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${cm.labels.map((actualLabel, rowIdx) => `
                                <tr>
                                    <td style="text-align:left; font-weight:700; color:#e2e8f0; background:rgba(15,23,42,0.5);">
                                        Actual: <span class="badge ${actualLabel === 'HIGH' ? 'badge-success' : actualLabel === 'MEDIUM' ? 'badge-info' : 'badge-warning'}">${actualLabel}</span>
                                    </td>
                                    ${cm.matrix[rowIdx].map((val, colIdx) => {
                                        const isDiagonal = rowIdx === colIdx;
                                        return `
                                            <td style="${isDiagonal ? 'background:rgba(16,185,129,0.18); font-weight:800; color:var(--primary-light); border:1px solid rgba(16,185,129,0.3); font-size:0.95rem;' : 'color:var(--text-muted);'}">
                                                ${val.toLocaleString()}
                                                ${isDiagonal ? ' <i class="fa-solid fa-check" style="font-size:0.7rem; color:var(--primary-light);" title="True Positive"></i>' : ''}
                                            </td>
                                        `;
                                    }).join("")}
                                    <td style="font-weight:700; color:#cbd5e1; background:rgba(15,23,42,0.3);">
                                        ${rowTotals[rowIdx].toLocaleString()}
                                    </td>
                                </tr>
                            `).join("")}
                            <tr style="border-top:2px solid var(--border-light); background:rgba(15,23,42,0.6);">
                                <td style="text-align:left; font-weight:700; color:var(--accent-blue);">Total Predicted</td>
                                ${colTotals.map(t => `<td style="font-weight:700; color:var(--accent-blue);">${t.toLocaleString()}</td>`).join("")}
                                <td style="font-weight:800; color:var(--primary-light);">${totalAll.toLocaleString()}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.6rem; font-size:0.75rem; color:var(--text-muted);">
                    <span><i class="fa-solid fa-square text-emerald" style="margin-right:0.25rem;"></i> Green highlighted diagonal cells indicate correct <strong>True Positive</strong> predictions.</span>
                    <span>Test Evaluation Sample: <strong>${totalAll.toLocaleString()}</strong> records</span>
                </div>
            `;
        }

        // Render Feature Importance Chart
        const ctxClf = document.getElementById("chartClfFeatureImportance");
        if (ctxClf && m.feature_importance) {
            if (AppState.charts.clfImportance) AppState.charts.clfImportance.destroy();
            AppState.charts.clfImportance = new Chart(ctxClf, {
                type: "bar",
                data: {
                    labels: m.feature_importance.map(f => f.feature.replace('_code', '').replace('_', ' ')),
                    datasets: [{
                        label: "Importance (%)",
                        data: m.feature_importance.map(f => f.importance),
                        backgroundColor: "rgba(56, 189, 248, 0.75)",
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                        y: { ticks: { color: "#e2e8f0" }, grid: { display: false } }
                    }
                }
            });
        }
    } catch (e) {
        console.error("Failed to load classification:", e);
    }
}

async function runLiveClassification() {
    const checkout = parseFloat(document.getElementById("clfInputCheckout").value) || 280;
    const base = parseFloat(document.getElementById("clfInputBase").value) || 310;
    const emailPromo = document.getElementById("clfInputEmail").checked ? 1 : 0;
    const homePromo = document.getElementById("clfInputHome").checked ? 1 : 0;
    const centerType = document.getElementById("clfInputCenterType").value;
    const category = document.getElementById("clfInputCategory").value;
    const cuisine = document.getElementById("clfInputCuisine").value;

    try {
        const res = await apiFetch("/api/mining/classification/predict", {
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

        const p = res.prediction;
        const resultBox = document.getElementById("clfPredictionResult");
        resultBox.style.display = "block";
        resultBox.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <span style="font-size:0.82rem; color:var(--text-secondary);">Predicted Demand Tier:</span>
                <span class="badge ${p.predicted_demand_tier === 'HIGH' ? 'badge-success' : p.predicted_demand_tier === 'MEDIUM' ? 'badge-info' : 'badge-warning'}" style="font-size:0.86rem; padding:0.3rem 0.8rem;">
                    ${p.predicted_demand_tier} DEMAND
                </span>
            </div>
            <div style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.5rem;">
                Confidence: High (${p.confidence_probabilities.HIGH}%), Medium (${p.confidence_probabilities.MEDIUM}%), Low (${p.confidence_probabilities.LOW}%)
            </div>
            <div class="insight-action" style="margin-top:0.5rem;">
                <strong>Waste Prevention Recommendation:</strong>
                ${p.waste_prevention_recommendation}
            </div>
        `;
    } catch (e) {
        showToast("Prediction error: " + e.message, "error");
    }
}

// ==============================================================================
// 2. REGRESSION MODEL
// ==============================================================================
async function loadRegressionModel() {
    try {
        const res = await apiFetch("/api/mining/regression/evaluate");
        if (!res.success) return;

        const m = res.model;
        document.getElementById("regR2").textContent = m.metrics.r2_score;
        document.getElementById("regR2Linear").textContent = m.metrics.r2_score_linear;
        document.getElementById("regRMSE").textContent = m.metrics.rmse;
        document.getElementById("regMAE").textContent = m.metrics.mae;
        document.getElementById("regMeanDemand").textContent = m.metrics.mean_actual_demand;

        // Actual vs Predicted Chart
        const ctxReg = document.getElementById("chartRegActualVsPred");
        if (ctxReg && m.actual_vs_predicted) {
            if (AppState.charts.regActualVsPred) AppState.charts.regActualVsPred.destroy();
            AppState.charts.regActualVsPred = new Chart(ctxReg, {
                type: "line",
                data: {
                    labels: m.actual_vs_predicted.map(d => `Sample #${d.index}`),
                    datasets: [
                        {
                            label: "Actual Sold Orders",
                            data: m.actual_vs_predicted.map(d => d.actual),
                            borderColor: "#38bdf8",
                            backgroundColor: "rgba(56, 189, 248, 0.1)",
                            tension: 0.2,
                            borderWidth: 2
                        },
                        {
                            label: "Regression Forecast",
                            data: m.actual_vs_predicted.map(d => d.predicted),
                            borderColor: "#10b981",
                            backgroundColor: "transparent",
                            borderDash: [5, 5],
                            tension: 0.2,
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: "#94a3b8" } } },
                    scales: {
                        x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
                        y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } }
                    }
                }
            });
        }
    } catch (e) {
        console.error("Failed to load regression:", e);
    }
}

async function runLiveRegression() {
    const checkout = parseFloat(document.getElementById("regInputCheckout").value) || 240;
    const base = parseFloat(document.getElementById("regInputBase").value) || 290;
    const emailPromo = document.getElementById("regInputEmail").checked ? 1 : 0;
    const homePromo = document.getElementById("regInputHome").checked ? 1 : 0;
    const centerType = document.getElementById("regInputCenterType").value;
    const category = document.getElementById("regInputCategory").value;
    const cuisine = document.getElementById("regInputCuisine").value;

    try {
        const res = await apiFetch("/api/mining/regression/predict", {
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

        const f = res.forecast;
        const resultBox = document.getElementById("regPredictionResult");
        resultBox.style.display = "block";
        resultBox.innerHTML = `
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-bottom:0.75rem;">
                <div style="background:rgba(15,23,42,0.8); padding:0.65rem; border-radius:var(--radius-sm);">
                    <div style="font-size:0.74rem; color:var(--text-muted);">Forecasted Orders:</div>
                    <div style="font-size:1.3rem; font-weight:800; color:var(--accent-blue);">${f.forecasted_demand.toLocaleString()} units</div>
                </div>
                <div style="background:rgba(15,23,42,0.8); padding:0.65rem; border-radius:var(--radius-sm);">
                    <div style="font-size:0.74rem; color:var(--text-muted);">Recommended Prep:</div>
                    <div style="font-size:1.3rem; font-weight:800; color:var(--primary-light);">${f.recommended_preparation_qty.toLocaleString()} units</div>
                </div>
            </div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:0.5rem;">
                Estimated Surplus Waste: <strong style="color:var(--accent-rose);">${f.estimated_surplus_waste_units} units</strong> (${f.projected_waste_percentage}%) · Projected Waste Cost: <strong>$${f.estimated_waste_cost.toLocaleString()}</strong>
            </div>
            <div class="insight-action">
                <strong>Inventory Strategy:</strong>
                ${f.waste_optimization_note}
            </div>
        `;
    } catch (e) {
        showToast("Regression error: " + e.message, "error");
    }
}

// ==============================================================================
// 3. CLUSTERING MODEL (K-MEANS)
// ==============================================================================
async function loadClusteringModel(k = 4) {
    try {
        const res = await apiFetch(`/api/mining/clustering/evaluate?k=${k}`);
        if (!res.success) return;

        const c = res.clustering;
        document.getElementById("clstSilhouette").textContent = c.metrics.silhouette_score;
        document.getElementById("clstDaviesBouldin").textContent = c.metrics.davies_bouldin_index;
        document.getElementById("clstInertia").textContent = c.metrics.inertia.toLocaleString();

        // Render Cluster Archetype Cards
        const cardsContainer = document.getElementById("clstArchetypeCards");
        if (cardsContainer) {
            cardsContainer.innerHTML = c.clusters.map(cl => `
                <div class="card" style="border-left: 3px solid ${getClusterColor(cl.cluster_id)};">
                    <div class="card-header" style="border:none; padding-bottom:0.25rem;">
                        <h4 style="font-size:0.95rem; color:${getClusterColor(cl.cluster_id)};">
                            Cluster #${cl.cluster_id}: ${cl.name}
                        </h4>
                        <span class="badge badge-neutral">${cl.percentage_of_catalog}% Menu</span>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:0.4rem; font-size:0.76rem; background:rgba(15,23,42,0.6); padding:0.5rem; border-radius:var(--radius-sm); margin-bottom:0.5rem;">
                        <div>Avg Sold: <strong style="color:#e2e8f0;">${cl.centroid.avg_sold_qty}</strong></div>
                        <div>Avg Waste: <strong style="color:var(--accent-rose);">${cl.centroid.avg_waste_pct}%</strong></div>
                        <div>Price: <strong style="color:var(--accent-blue);">$${cl.centroid.avg_checkout_price}</strong></div>
                    </div>
                    <div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:0.4rem;">
                        Top Categories: <em>${cl.top_categories.join(", ")}</em>
                    </div>
                    <div class="insight-action" style="font-size:0.76rem; padding:0.45rem 0.65rem;">
                        ${cl.operational_strategy}
                    </div>
                </div>
            `).join("");
        }

        // Render 2D Scatter Chart
        const ctxScatter = document.getElementById("chartClstScatter");
        if (ctxScatter && c.scatter_2d) {
            if (AppState.charts.clstScatter) AppState.charts.clstScatter.destroy();
            AppState.charts.clstScatter = new Chart(ctxScatter, {
                type: "scatter",
                data: {
                    datasets: [0, 1, 2, 3].map(cid => ({
                        label: `Cluster ${cid}`,
                        data: c.scatter_2d.filter(p => p.cluster === cid).map(p => ({ x: p.x, y: p.y, item: p.item })),
                        backgroundColor: getClusterColor(cid),
                        pointRadius: 4
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: ctx => `${ctx.raw.item} (${ctx.raw.x}, ${ctx.raw.y})`
                            }
                        },
                        legend: { labels: { color: "#94a3b8" } }
                    },
                    scales: {
                        x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                        y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } }
                    }
                }
            });
        }
    } catch (e) {
        console.error("Failed to load clustering:", e);
    }
}

function getClusterColor(cid) {
    const colors = ["#10b981", "#ef4444", "#f59e0b", "#8b5cf6"];
    return colors[cid % colors.length];
}

// ==============================================================================
// 4. ASSOCIATION RULE MINING (APRIORI)
// ==============================================================================
async function loadAprioriModel() {
    const sup = parseFloat(document.getElementById("aprioriMinSupport")?.value || 0.08);
    const conf = parseFloat(document.getElementById("aprioriMinConfidence")?.value || 0.55);
    const lift = parseFloat(document.getElementById("aprioriMinLift")?.value || 1.2);

    try {
        const res = await apiFetch(`/api/mining/association-rules/evaluate?min_support=${sup}&min_confidence=${conf}&min_lift=${lift}`);
        if (!res.success) return;

        const a = res.association_rules;
        document.getElementById("aprioriRulesCount").textContent = a.total_rules_discovered;

        const tbody = document.getElementById("aprioriRulesTableBody");
        if (!tbody) return;

        tbody.innerHTML = a.rules.map(r => `
            <tr>
                <td><strong>${r.antecedent_str}</strong></td>
                <td><i class="fa-solid fa-arrow-right text-emerald" style="margin: 0 0.3rem;"></i> <strong>${r.consequent_str}</strong></td>
                <td><span class="badge badge-neutral">${r.support_pct}%</span></td>
                <td><span class="badge badge-info">${r.confidence_pct}%</span></td>
                <td><strong style="color:var(--primary-light);">${r.lift}x</strong></td>
                <td><span style="font-size:0.76rem; color:var(--text-muted);">${r.leverage}</span></td>
                <td style="font-size:0.78rem; max-width: 320px;">${r.waste_mitigation_strategy}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load association rules:", e);
    }
}

// ==============================================================================
// 5. ANOMALY DETECTION (ISOLATION FOREST)
// ==============================================================================
async function loadAnomalyModel() {
    const contam = parseFloat(document.getElementById("anomalyContamination")?.value || 0.02);
    try {
        const res = await apiFetch(`/api/mining/anomaly-detection/evaluate?contamination=${contam}`);
        if (!res.success) return;

        const an = res.anomaly_detection;
        document.getElementById("anomalyCount").textContent = an.anomalies_detected;
        document.getElementById("anomalyRate").textContent = `${an.anomaly_rate_pct}%`;
        document.getElementById("anomalyThreshold").textContent = an.score_threshold;

        const tbody = document.getElementById("anomalyTableBody");
        if (!tbody) return;

        tbody.innerHTML = an.top_anomalies.map(a => `
            <tr>
                <td style="font-size:0.76rem; color:var(--text-muted);">#${a.fact_id}</td>
                <td>Wk ${a.week_number}</td>
                <td><strong>${a.item_name}</strong> <span style="font-size:0.72rem; color:var(--text-muted);">(${a.category})</span></td>
                <td>${a.center_name.split('(')[0]}</td>
                <td>${a.prepared_qty.toLocaleString()}</td>
                <td><span style="color:var(--accent-blue);">${a.sold_qty.toLocaleString()}</span></td>
                <td><span style="color:var(--accent-rose); font-weight:700;">${a.waste_qty.toLocaleString()}</span></td>
                <td><span class="badge badge-danger">${a.waste_percentage}%</span></td>
                <td><strong style="color:var(--accent-rose);">$${a.waste_cost.toLocaleString()}</strong></td>
                <td style="font-size:0.76rem; max-width:280px; color:#fde68a;">${a.root_cause_diagnosis}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error("Failed to load anomaly detection:", e);
    }
}
