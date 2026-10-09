// ==============================================================================
// FOOD WASTE PERIODIC MONITORING & EARLY ANALYSIS CONTROLLER
// Supports Period Selection (Daily, Weekly, Monthly, Yearly, Custom Range),
// Period Comparisons (Prepared, Sold, Wasted, Waste %, Change),
// Automated Early Warning Detection (🟢 Normal, 🟡 Warning, 🔴 Critical),
// and Continuous Historical Data Upload without deleting records.
// ==============================================================================

const PeriodicState = {
    periodType: "weekly",
    periodValue: "26",
    startDate: "",
    endDate: "",
    options: null,
    currentAnalysis: null
};

// Initialize on dashboard load
window.initPeriodicMonitoring = async function() {
    try {
        await loadPeriodOptions();
        await runPeriodicAnalysis();
        setupPeriodEventListeners();
    } catch (err) {
        console.error("Periodic monitoring initialization error:", err);
    }
};

// ==============================================================================
// 1. LOAD AVAILABLE PERIOD OPTIONS
// ==============================================================================
async function loadPeriodOptions() {
    try {
        const res = await apiFetch("/api/periodic-monitoring/options");
        if (!res.success) return;

        PeriodicState.options = res.options;

        // 1. Populate Weeks Dropdown
        const weekSelect = document.getElementById("selectPeriodWeek");
        if (weekSelect && res.options.weeks) {
            weekSelect.innerHTML = res.options.weeks.map(w => {
                const isSelected = w.week_number === res.options.latest_week ? "selected" : "";
                return `<option value="${w.week_number}" ${isSelected}>Week ${w.week_number} (${w.month_name}) - ${w.record_count.toLocaleString()} records</option>`;
            }).join("");
            PeriodicState.periodValue = String(res.options.latest_week);
        }

        // 2. Populate Months Dropdown
        const monthSelect = document.getElementById("selectPeriodMonth");
        if (monthSelect && res.options.months) {
            monthSelect.innerHTML = res.options.months.map(m => {
                const isSelected = m.month_name === res.options.latest_month ? "selected" : "";
                return `<option value="${m.month_name}" ${isSelected}>${m.month_name} ${m.year} (${m.record_count.toLocaleString()} records)</option>`;
            }).join("");
        }

        // 3. Populate Years Dropdown
        const yearSelect = document.getElementById("selectPeriodYear");
        if (yearSelect && res.options.years) {
            yearSelect.innerHTML = res.options.years.map(y => {
                const isSelected = y.year === res.options.latest_year ? "selected" : "";
                return `<option value="${y.year}" ${isSelected}>Year ${y.year} (${y.record_count.toLocaleString()} records)</option>`;
            }).join("");
        }

        // 4. Populate Dates Dropdown (Daily)
        const dateSelect = document.getElementById("selectPeriodDate");
        if (dateSelect && res.options.dates) {
            dateSelect.innerHTML = res.options.dates.map(d => {
                const isSelected = d === res.options.latest_date ? "selected" : "";
                return `<option value="${d}" ${isSelected}>${d}</option>`;
            }).join("");
        }

        // 5. Populate Custom Range defaults
        const startInput = document.getElementById("inputPeriodStartDate");
        const endInput = document.getElementById("inputPeriodEndDate");
        if (startInput && endInput) {
            startInput.value = res.options.min_date || "2024-01-01";
            endInput.value = res.options.max_date || "2024-06-24";
            PeriodicState.startDate = startInput.value;
            PeriodicState.endDate = endInput.value;
        }

    } catch (err) {
        console.error("Failed to load period options:", err);
    }
}

// ==============================================================================
// 2. PERIOD SELECTOR SWITCHER
// ==============================================================================
window.setPeriodType = function(type) {
    PeriodicState.periodType = type;

    // Update Pill Buttons
    document.querySelectorAll(".period-selector-pill").forEach(btn => {
        if (btn.getAttribute("data-period") === type) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Toggle Value Selectors
    const weekWrap = document.getElementById("periodSelectWeekWrapper");
    const monthWrap = document.getElementById("periodSelectMonthWrapper");
    const yearWrap = document.getElementById("periodSelectYearWrapper");
    const dateWrap = document.getElementById("periodSelectDateWrapper");
    const customWrap = document.getElementById("periodSelectCustomWrapper");

    if (weekWrap) weekWrap.style.display = type === "weekly" ? "block" : "none";
    if (monthWrap) monthWrap.style.display = type === "monthly" ? "block" : "none";
    if (yearWrap) yearWrap.style.display = type === "yearly" ? "block" : "none";
    if (dateWrap) dateWrap.style.display = type === "daily" ? "block" : "none";
    if (customWrap) customWrap.style.display = type === "custom" ? "flex" : "none";

    runPeriodicAnalysis();
};

function setupPeriodEventListeners() {
    // Select change listeners for instant analysis
    const weekSelect = document.getElementById("selectPeriodWeek");
    if (weekSelect) weekSelect.addEventListener("change", (e) => {
        PeriodicState.periodValue = e.target.value;
        runPeriodicAnalysis();
    });

    const monthSelect = document.getElementById("selectPeriodMonth");
    if (monthSelect) monthSelect.addEventListener("change", (e) => {
        PeriodicState.periodValue = e.target.value;
        runPeriodicAnalysis();
    });

    const yearSelect = document.getElementById("selectPeriodYear");
    if (yearSelect) yearSelect.addEventListener("change", (e) => {
        PeriodicState.periodValue = e.target.value;
        runPeriodicAnalysis();
    });

    const dateSelect = document.getElementById("selectPeriodDate");
    if (dateSelect) dateSelect.addEventListener("change", (e) => {
        PeriodicState.periodValue = e.target.value;
        runPeriodicAnalysis();
    });

    const startInput = document.getElementById("inputPeriodStartDate");
    if (startInput) startInput.addEventListener("change", (e) => {
        PeriodicState.startDate = e.target.value;
    });

    const endInput = document.getElementById("inputPeriodEndDate");
    if (endInput) endInput.addEventListener("change", (e) => {
        PeriodicState.endDate = e.target.value;
    });

    // Continuous Upload Form
    const uploadForm = document.getElementById("continuousUploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", handleContinuousUploadSubmit);
    }
}

// ==============================================================================
// 3. RUN PERIODIC FOOD WASTE ANALYSIS & COMPARISON
// ==============================================================================
window.runPeriodicAnalysis = async function() {
    const type = PeriodicState.periodType;
    let val = "";
    let startDate = "";
    let endDate = "";

    if (type === "weekly") {
        const sel = document.getElementById("selectPeriodWeek");
        val = sel ? sel.value : (PeriodicState.periodValue || "26");
    } else if (type === "monthly") {
        const sel = document.getElementById("selectPeriodMonth");
        val = sel ? sel.value : "June";
    } else if (type === "yearly") {
        const sel = document.getElementById("selectPeriodYear");
        val = sel ? sel.value : "2024";
    } else if (type === "daily") {
        const sel = document.getElementById("selectPeriodDate");
        val = sel ? sel.value : (PeriodicState.options?.latest_date || "2024-06-24");
    } else if (type === "custom") {
        startDate = document.getElementById("inputPeriodStartDate")?.value || PeriodicState.startDate;
        endDate = document.getElementById("inputPeriodEndDate")?.value || PeriodicState.endDate;
    }

    const container = document.getElementById("periodicMonitoringContent");
    if (!container) return;

    try {
        let url = `/api/periodic-monitoring/analyze?period_type=${encodeURIComponent(type)}`;
        if (val) url += `&value=${encodeURIComponent(val)}`;
        if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
        if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;

        const res = await apiFetch(url);
        if (!res.success) {
            showToast(res.error || "Analysis failed", "error");
            return;
        }

        PeriodicState.currentAnalysis = res.analysis;
        renderPeriodicAnalysisUI(res.analysis);
    } catch (err) {
        console.error("Periodic analysis error:", err);
        showToast("Failed to compute periodic food waste comparison: " + err.message, "error");
    }
};

// ==============================================================================
// 4. RENDER ANALYSIS, PERIOD COMPARISON & EARLY WARNING UI
// ==============================================================================
function renderPeriodicAnalysisUI(analysis) {
    const cur = analysis.current_metrics;
    const prev = analysis.previous_metrics;
    const comp = analysis.comparison;
    const warn = analysis.early_warning;
    const ex = analysis.example_summary;

    // 1. Early Warning Badge & Actionable Message
    const warnBadgeElem = document.getElementById("earlyWarningBadge");
    const warnMsgElem = document.getElementById("earlyWarningMessage");
    const warnDetailsElem = document.getElementById("earlyWarningDetails");
    const warnBox = document.getElementById("earlyWarningBox");

    if (warnBadgeElem) {
        warnBadgeElem.textContent = warn.badge;
        warnBadgeElem.className = `early-warning-badge badge-${warn.color}`;
    }

    if (warnMsgElem) {
        warnMsgElem.textContent = warn.message;
    }

    if (warnDetailsElem) {
        warnDetailsElem.textContent = warn.details;
    }

    if (warnBox) {
        warnBox.className = `early-warning-container status-${warn.color}`;
    }

    // 2. Example-Format Comparison Highlight Box
    // Current [Period] Waste: 65,000 | Previous [Period] Waste: 30,000 | Change: +116.7%
    const exCurrWaste = document.getElementById("exampleCurrentWaste");
    const exPrevWaste = document.getElementById("examplePreviousWaste");
    const exChange = document.getElementById("exampleWasteChange");
    const exCurrTitle = document.getElementById("exampleCurrentTitle");
    const exPrevTitle = document.getElementById("examplePreviousTitle");

    if (exCurrTitle) exCurrTitle.textContent = ex.current_period_waste_title;
    if (exPrevTitle) exPrevTitle.textContent = ex.previous_period_waste_title;
    if (exCurrWaste) exCurrWaste.textContent = ex.current_period_waste_val;
    if (exPrevWaste) exPrevWaste.textContent = ex.previous_period_waste_val;

    if (exChange) {
        exChange.textContent = ex.change_display;
        if (comp.waste_change_pct !== null) {
            if (comp.waste_change_pct >= 15.0) {
                exChange.className = "metric-delta-tag tag-critical";
            } else if (comp.waste_change_pct >= 5.0) {
                exChange.className = "metric-delta-tag tag-warning";
            } else if (comp.waste_change_pct <= 0) {
                exChange.className = "metric-delta-tag tag-success";
            } else {
                exChange.className = "metric-delta-tag tag-neutral";
            }
        } else {
            exChange.className = "metric-delta-tag tag-neutral";
        }
    }

    // 3. Period Labels
    const curLabelElem = document.getElementById("compCurrentPeriodLabel");
    const prevLabelElem = document.getElementById("compPreviousPeriodLabel");
    if (curLabelElem) curLabelElem.textContent = analysis.current_period_label;
    if (prevLabelElem) prevLabelElem.textContent = analysis.previous_period_label;

    // 4. Comparison Cards: Food Prepared
    renderMetricComparisonRow(
        "compFoodPrepared",
        cur.food_prepared,
        prev.food_prepared,
        comp.prep_change_pct,
        "units",
        true // inverse color or standard
    );

    // 5. Food Sold
    renderMetricComparisonRow(
        "compFoodSold",
        cur.food_sold,
        prev.food_sold,
        comp.sold_change_pct,
        "orders",
        false
    );

    // 6. Food Wasted
    renderMetricComparisonRow(
        "compFoodWasted",
        cur.food_wasted,
        prev.food_wasted,
        comp.waste_change_pct,
        "units",
        true
    );

    // 7. Waste Percentage
    const curWastePctElem = document.getElementById("compCurrentWastePct");
    const prevWastePctElem = document.getElementById("compPreviousWastePct");
    const diffWastePctElem = document.getElementById("compWastePctDiff");

    if (curWastePctElem) curWastePctElem.textContent = `${cur.waste_percentage}%`;
    if (prevWastePctElem) prevWastePctElem.textContent = `${prev.waste_percentage}%`;
    if (diffWastePctElem) {
        const sign = comp.waste_pct_diff > 0 ? "+" : "";
        diffWastePctElem.textContent = `${sign}${comp.waste_pct_diff}% pts`;
        diffWastePctElem.className = comp.waste_pct_diff > 1.0 ? "text-rose" : (comp.waste_pct_diff < -1.0 ? "text-emerald" : "text-muted");
    }

    // Secondary cost & revenue metrics
    const curCostElem = document.getElementById("compCurrentWasteCost");
    const prevCostElem = document.getElementById("compPreviousWasteCost");
    if (curCostElem) curCostElem.textContent = formatCurrency(cur.waste_cost);
    if (prevCostElem) prevCostElem.textContent = formatCurrency(prev.waste_cost);
}

function renderMetricComparisonRow(prefixId, curVal, prevVal, pctChange, unit, isWasteMetric) {
    const curElem = document.getElementById(`${prefixId}Current`);
    const prevElem = document.getElementById(`${prefixId}Previous`);
    const changeElem = document.getElementById(`${prefixId}Change`);

    if (curElem) curElem.textContent = Number(curVal).toLocaleString();
    if (prevElem) prevElem.textContent = Number(prevVal).toLocaleString();

    if (changeElem) {
        if (pctChange === null || pctChange === undefined) {
            changeElem.textContent = "Baseline";
            changeElem.className = "comparison-delta delta-neutral";
        } else {
            const sign = pctChange > 0 ? "+" : "";
            changeElem.textContent = `${sign}${pctChange.toFixed(1)}%`;

            if (isWasteMetric) {
                if (pctChange >= 15.0) {
                    changeElem.className = "comparison-delta delta-danger";
                } else if (pctChange >= 5.0) {
                    changeElem.className = "comparison-delta delta-warning";
                } else if (pctChange <= 0.0) {
                    changeElem.className = "comparison-delta delta-success";
                } else {
                    changeElem.className = "comparison-delta delta-neutral";
                }
            } else {
                if (pctChange > 0.0) {
                    changeElem.className = "comparison-delta delta-success";
                } else if (pctChange < -10.0) {
                    changeElem.className = "comparison-delta delta-warning";
                } else {
                    changeElem.className = "comparison-delta delta-neutral";
                }
            }
        }
    }
}

// ==============================================================================
// 5. CONTINUOUS DATA UPLOAD (ADMIN / ANALYST ONLY)
// ==============================================================================
window.openContinuousUploadModal = function() {
    if (AppState.currentUser?.role === "Viewer") {
        showToast("Viewers have read-only access. Sign in as Admin or Analyst to upload continuous datasets.", "error");
        return;
    }
    const modal = document.getElementById("continuousUploadModal");
    if (modal) modal.classList.add("active");
};

window.closeContinuousUploadModal = function() {
    const modal = document.getElementById("continuousUploadModal");
    if (modal) modal.classList.remove("active");
    const form = document.getElementById("continuousUploadForm");
    if (form) form.reset();
};

async function handleContinuousUploadSubmit(e) {
    e.preventDefault();
    const fileInput = document.getElementById("continuousFileInput");
    const nameInput = document.getElementById("continuousNameInput");
    const cadenceSelect = document.getElementById("continuousCadenceSelect");
    const submitBtn = document.getElementById("btnSubmitContinuousUpload");

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a CSV or Excel dataset to upload.", "error");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    if (nameInput && nameInput.value.trim()) {
        formData.append("name", nameInput.value.trim());
    }
    if (cadenceSelect && cadenceSelect.value) {
        formData.append("cadence", cadenceSelect.value);
    }

    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing & Appending Data...';
        }

        const headers = {};
        if (AppState.authToken) {
            headers["Authorization"] = `Bearer ${AppState.authToken}`;
        }

        const response = await fetch("/api/periodic-monitoring/upload", {
            method: "POST",
            headers: headers,
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            showToast(`Continuous Ingestion Success! Added ${data.result.records_added.toLocaleString()} records without deleting historical data. Total records: ${data.result.total_fact_records.toLocaleString()}`, "success");
            closeContinuousUploadModal();

            // Refresh period options and trigger analysis
            await loadPeriodOptions();
            await runPeriodicAnalysis();

            // Also refresh global dashboard KPIs if loaded
            if (typeof window.loadDashboard === "function") {
                window.loadDashboard();
            }
        } else {
            showToast(data.error || "Continuous upload failed", "error");
        }
    } catch (err) {
        showToast("Continuous upload error: " + err.message, "error");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Process & Append to Warehouse';
        }
    }
}

// Convenience function to ingest pre-bundled sample continuous data
window.loadSampleContinuousFeed = async function(sampleType = "week27") {
    if (AppState.currentUser?.role === "Viewer") {
        showToast("Viewers have read-only access. Sign in as Admin or Analyst.", "error");
        return;
    }

    const btn = document.getElementById(`btnSample${sampleType === 'daily' ? 'Daily' : 'Week27'}`);
    const originalText = btn ? btn.innerHTML : "";

    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting Feed...';
        }

        const res = await apiFetch("/api/periodic-monitoring/sample-continuous", "POST", {
            sample_type: sampleType
        });

        if (res.success) {
            showToast(`Continuous Feed Ingested! +${res.result.records_added.toLocaleString()} records added to historical warehouse. Total records: ${res.result.total_fact_records.toLocaleString()}`, "success");
            closeContinuousUploadModal();

            await loadPeriodOptions();

            // If week 27 was loaded, switch to it
            if (sampleType === "week27") {
                PeriodicState.periodType = "weekly";
                PeriodicState.periodValue = "27";
                const sel = document.getElementById("selectPeriodWeek");
                if (sel) sel.value = "27";
                setPeriodType("weekly");
            } else {
                setPeriodType("daily");
            }

            await runPeriodicAnalysis();

            if (typeof window.loadDashboard === "function") {
                window.loadDashboard();
            }
        } else {
            showToast(res.error || "Sample ingestion failed", "error");
        }
    } catch (err) {
        showToast("Sample ingestion error: " + err.message, "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
};
