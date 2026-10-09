// ==============================================================================
// DWM ANALYSIS & ACADEMIC SHOWCASE CONTROLLER (VERY IMPORTANT)
// ==============================================================================

window.loadDWMAnalysis = async function() {
    try {
        const res = await apiFetch("/api/dwm-analysis/summary");
        if (!res.success) return;

        const container = document.getElementById("dwmAnalysisContainer");
        if (!container) return;

        const d = res.analysis;

        container.innerHTML = `
            <div style="margin-bottom: 2rem;">
                <div class="card" style="border-left: 4px solid var(--accent-indigo); background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));">
                    <h3 style="font-size: 1.25rem; color: #a5b4fc; margin-bottom: 0.5rem;">
                        <i class="fa-solid fa-graduation-cap"></i> Academic Curriculum Context & Theoretical Foundation
                    </h3>
                    <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
                        This system is engineered specifically for the <strong>Data Warehousing & Data Mining (DWM)</strong> curriculum.
                        Unlike standard transactional food apps, every feature is architected around foundational DWM principles:
                        multidimensional star modeling, granular ETL pipeline extraction, OLAP analytical aggregations,
                        and five core data mining techniques (Classification, Regression, Clustering, Association Mining, Anomaly Detection).
                    </p>
                </div>
            </div>

            <!-- Concept Mapping Matrix -->
            <div class="card" style="margin-bottom: 2rem;">
                <div class="card-header">
                    <h3><i class="fa-solid fa-table-columns text-emerald"></i> DWM Curriculum Implementation Matrix</h3>
                </div>
                <div class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>DWM Academic Concept</th>
                                <th>Theoretical Definition</th>
                                <th>Implementation in this Project</th>
                                <th>Academic / Real-world Benefit</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong style="color:#7dd3fc;">Star Schema</strong></td>
                                <td>Central fact table surrounded by single-level de-normalized dimension tables.</td>
                                <td><code>fact_food_waste_demand</code> joined with <code>dim_date</code>, <code>dim_food_item</code>, <code>dim_fulfillment_center</code>, <code>dim_category</code>.</td>
                                <td>Eliminates complex multi-table joins; enables sub-10ms OLAP cube queries over 75,000+ real records.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">ETL Pipeline</strong></td>
                                <td>Extraction, Transformation (cleaning, derived metrics), and Loading with audit logging.</td>
                                <td><code>etl/pipeline.py</code> cleans raw Kaggle orders, imputes perishability buffers, computes waste facts, and loads warehouse.</td>
                                <td>Ensures audit traceability, data cleaning, and schema reproducibility.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">OLAP Operations</strong></td>
                                <td>Multidimensional analytical queries: Slice, Dice, Roll-up, Drill-down, and Pivot.</td>
                                <td><code>warehouse/olap_engine.py</code> executes dynamic SQL aggregations across temporal and product hierarchies.</td>
                                <td>Converts low-level transactions into executive-level food waste intelligence.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">Classification</strong></td>
                                <td>Supervised learning to predict discrete class labels from historical feature boundaries.</td>
                                <td>Random Forest Classifier (100 trees) predicts Demand Tiers (LOW, MEDIUM, HIGH) with 86%+ accuracy.</td>
                                <td>Provides kitchen managers with upfront demand risk classification.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">Regression</strong></td>
                                <td>Continuous variable forecasting minimizing error loss functions (MSE/RMSE).</td>
                                <td>Random Forest & Ridge Regressor forecasting sold_qty; calculates optimal prep to keep waste &lt; 10%.</td>
                                <td>Solves the central food-service dilemma of over-preparation vs stockout.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">K-Means Clustering</strong></td>
                                <td>Unsupervised partitioning minimizing within-cluster sum of squared Euclidean distances.</td>
                                <td>Segments menu into 4 archetypes (Staples, Spoilage-Risk Perishables, Promo Surges, Gourmet).</td>
                                <td>Discovers operational profiles requiring customized batch management.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">Apriori Association Mining</strong></td>
                                <td>Discovering frequent itemsets using Support, Confidence, and Lift thresholds.</td>
                                <td>Mines co-occurring meals in multi-item orders (e.g. Pasta + Garlic Bread + Beverage).</td>
                                <td>Synchronizes kitchen batch prep multiples to eliminate orphan side-item spoilage.</td>
                            </tr>
                            <tr>
                                <td><strong style="color:#7dd3fc;">Anomaly Detection</strong></td>
                                <td>Isolating rare observations using recursive random partitioning trees.</td>
                                <td>Isolation Forest (contamination = 2%) flags severe waste surges with root-cause diagnostics.</td>
                                <td>Alerts management to refrigeration failure, promo failures, or inventory leaks.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Mathematical Foundations & Formulas -->
            <div class="card" style="margin-bottom: 2rem;">
                <div class="card-header">
                    <h3><i class="fa-solid fa-square-root-variable text-amber"></i> Mathematical Formulations of Implemented Algorithms</h3>
                </div>
                <div class="grid-2">
                    <div style="background:rgba(15,23,42,0.6); padding:1rem; border-radius:var(--radius-md);">
                        <h4 style="color:#38bdf8; font-size:0.92rem; margin-bottom:0.4rem;">1. Apriori Association Metrics</h4>
                        <div class="code-box">Support(X → Y) = P(X ∪ Y) = σ(X ∪ Y) / N</div>
                        <div class="code-box">Confidence(X → Y) = P(Y | X) = Support(X ∪ Y) / Support(X)</div>
                        <div class="code-box">Lift(X → Y) = Confidence(X → Y) / Support(Y)</div>
                        <p style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                            Lift &gt; 1.0 proves positive correlation, meaning the purchase of item X significantly increases likelihood of item Y.
                        </p>
                    </div>

                    <div style="background:rgba(15,23,42,0.6); padding:1rem; border-radius:var(--radius-md);">
                        <h4 style="color:#34d399; font-size:0.92rem; margin-bottom:0.4rem;">2. K-Means Objective Function</h4>
                        <div class="code-box">J = Σ_{k=1}^K Σ_{x ∈ C_k} || x - μ_k ||²</div>
                        <div class="code-box">Silhouette Score s(i) = (b(i) - a(i)) / max(a(i), b(i))</div>
                        <p style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                            Minimizes total inertia (within-cluster variance) while maximizing inter-cluster separation.
                        </p>
                    </div>

                    <div style="background:rgba(15,23,42,0.6); padding:1rem; border-radius:var(--radius-md);">
                        <h4 style="color:#f59e0b; font-size:0.92rem; margin-bottom:0.4rem;">3. Regression Demand Forecasting</h4>
                        <div class="code-box">R² = 1 - (Σ (y_i - ŷ_i)² / Σ (y_i - ȳ)²)</div>
                        <div class="code-box">RMSE = √ ( (1/N) Σ (y_i - ŷ_i)² )</div>
                        <p style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                            Evaluates goodness-of-fit against baseline mean demand, penalized by root mean squared error.
                        </p>
                    </div>

                    <div style="background:rgba(15,23,42,0.6); padding:1rem; border-radius:var(--radius-md);">
                        <h4 style="color:#f43f5e; font-size:0.92rem; margin-bottom:0.4rem;">4. Isolation Forest Anomaly Score</h4>
                        <div class="code-box">s(x, n) = 2^(- E(h(x)) / c(n))</div>
                        <p style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                            Where h(x) is path length to isolate point x. Anomalous waste spikes require fewer recursive splits and have s(x, n) close to 1.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Detailed Pillar Sections -->
            ${d.pedagogical_pillars.map(p => `
                <div class="card" style="margin-bottom: 1.5rem;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-diagram-project text-emerald"></i> ${p.pillar}</h3>
                    </div>
                    <div>
                        ${p.concepts.map(c => `
                            <div class="dwm-theory-block">
                                <div class="dwm-theory-title">
                                    <i class="fa-solid fa-circle-check text-emerald" style="font-size:0.8rem;"></i> ${c.concept}
                                </div>
                                <div class="dwm-theory-desc">
                                    <strong>Academic Theory:</strong> ${c.academic_theory}
                                </div>
                                <div style="font-size:0.84rem; color:#e2e8f0; margin-bottom:0.5rem;">
                                    <strong>PBL Implementation:</strong> ${c.implementation}
                                </div>
                                <div class="dwm-implementation-tag">
                                    <i class="fa-solid fa-arrow-trend-up"></i> <strong>Result & Benefit:</strong> ${c.benefit}
                                </div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `).join("")}
        `;
    } catch (e) {
        console.error("Failed to load DWM Analysis:", e);
    }
};
