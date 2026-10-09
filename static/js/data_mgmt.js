// ==============================================================================
// DATA MANAGEMENT & DATASET SOURCES CONTROLLER
// Includes External Sources, Dataset Catalog, Upload/Import, and ETL status
// ==============================================================================

let currentDataPage = 1;
let currentSearchTerm = "";

window.loadDataManagement = async function() {
    await Promise.all([
        loadDatasetCatalog(),
        loadDataSources(),
        loadRawDataSample(1),
        loadETLStatus()
    ]);
};

// ==============================================================================
// 1. DATASET CATALOG (Upload, View, Delete, Distinguish from Processed)
// ==============================================================================
async function loadDatasetCatalog() {
    try {
        const res = await apiFetch("/api/datasets");
        if (!res.success) return;

        const tbody = document.getElementById("datasetCatalogTableBody");
        if (!tbody) return;

        const isViewer = AppState.currentUser?.role === "Viewer";
        const uploadBtn = document.getElementById("btnOpenUploadDatasetModal");
        if (uploadBtn) {
            uploadBtn.style.display = isViewer ? "none" : "inline-flex";
        }

        if (res.datasets.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:1.5rem; color:var(--text-muted);">No datasets available.</td></tr>`;
            return;
        }

        tbody.innerHTML = res.datasets.map(ds => {
            const isBenchmark = ds.source_type === "EXTERNAL_BENCHMARK";
            const typeBadge = isBenchmark 
                ? `<span class="badge badge-info" style="font-size:0.7rem;"><i class="fa-solid fa-cloud-arrow-down"></i> External Source</span>`
                : `<span class="badge badge-warning" style="font-size:0.7rem;"><i class="fa-solid fa-upload"></i> User Upload</span>`;

            const statusBadge = ds.processing_status === "PROCESSED_IN_WAREHOUSE"
                ? `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> In Warehouse</span>`
                : `<span class="badge badge-neutral"><i class="fa-solid fa-clock"></i> Ready for ETL</span>`;

            let actionBtn = "";
            if (ds.is_deletable) {
                if (!isViewer) {
                    actionBtn = `
                        <button class="btn btn-danger btn-icon" style="width:28px; height:28px; font-size:0.75rem;" title="Delete Dataset" onclick="confirmDeleteDataset(${ds.dataset_id}, '${escapeHtml(ds.name)}')">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    `;
                } else {
                    actionBtn = `<span style="font-size:0.7rem; color:var(--text-muted);">Read-only</span>`;
                }
            } else {
                actionBtn = `<span class="badge badge-neutral" style="font-size:0.68rem;" title="Core benchmark dataset">Core Benchmark</span>`;
            }

            return `
                <tr>
                    <td>
                        <div style="display:flex; align-items:center; gap:0.5rem;">
                            <i class="fa-solid ${isBenchmark ? 'fa-database text-blue' : 'fa-file-csv text-emerald'}"></i>
                            <div>
                                <strong style="color:var(--text-primary); font-size:0.86rem;">${ds.name}</strong>
                                <div style="font-size:0.72rem; color:var(--text-muted);">${ds.file_size_kb ? ds.file_size_kb + ' KB' : 'Benchmark'}</div>
                            </div>
                        </div>
                    </td>
                    <td>${typeBadge}</td>
                    <td style="font-size:0.8rem; color:var(--text-secondary);">${ds.provider_source}</td>
                    <td><strong style="color:var(--primary-light);">${ds.record_count.toLocaleString()}</strong></td>
                    <td style="font-size:0.76rem; color:var(--text-muted); max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${ds.columns.join(', ')}">
                        ${ds.columns.slice(0, 5).join(", ")}${ds.columns.length > 5 ? '...' : ''} <span style="color:var(--accent-blue);">(${ds.column_count} cols)</span>
                    </td>
                    <td style="font-size:0.78rem; color:var(--text-secondary);">${ds.import_date}</td>
                    <td>${statusBadge}</td>
                    <td style="text-align:right;">${actionBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Failed to load dataset catalog:", e);
    }
}

function openUploadDatasetModal() {
    if (AppState.currentUser?.role === "Viewer") {
        showToast("Viewers have read-only permissions. Sign in as Analyst or Admin to upload datasets.", "error");
        return;
    }
    const modal = document.getElementById("uploadDatasetModal");
    if (modal) modal.classList.add("active");
}

function closeUploadDatasetModal() {
    const modal = document.getElementById("uploadDatasetModal");
    if (modal) modal.classList.remove("active");
    const form = document.getElementById("uploadDatasetForm");
    if (form) form.reset();
}

async function handleUploadDatasetSubmit(e) {
    e.preventDefault();
    const fileInput = document.getElementById("datasetFileInput");
    const nameInput = document.getElementById("datasetNameInput");
    const uploadBtn = document.getElementById("btnSubmitUploadDataset");

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showToast("Please select a CSV or Excel file to upload.", "error");
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    if (nameInput && nameInput.value.trim()) {
        formData.append("name", nameInput.value.trim());
    }

    try {
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & Parsing...';
        }

        const headers = {};
        if (AppState.authToken) {
            headers["Authorization"] = `Bearer ${AppState.authToken}`;
        }

        const response = await fetch("/api/datasets/upload", {
            method: "POST",
            headers: headers,
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            showToast(`Dataset '${data.dataset.name}' uploaded successfully (${data.dataset.record_count.toLocaleString()} rows)!`, "success");
            closeUploadDatasetModal();
            await loadDatasetCatalog();
        } else {
            showToast(data.error || "Upload failed", "error");
        }
    } catch (err) {
        showToast("Upload error: " + err.message, "error");
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fa-solid fa-upload"></i> Upload Dataset';
        }
    }
}

async function confirmDeleteDataset(datasetId, datasetName) {
    if (AppState.currentUser?.role === "Viewer") {
        showToast("Viewers cannot delete datasets.", "error");
        return;
    }
    if (!confirm(`Are you sure you want to delete dataset '${datasetName}'?`)) {
        return;
    }

    try {
        const res = await apiFetch(`/api/datasets/${datasetId}`, { method: "DELETE" });
        if (res.success) {
            showToast(`Dataset '${datasetName}' deleted successfully.`, "success");
            await loadDatasetCatalog();
        } else {
            showToast(res.error || "Delete failed", "error");
        }
    } catch (err) {
        showToast("Delete failed: " + err.message, "error");
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ==============================================================================
// 2. DATA SOURCES CITATIONS & PROVENANCE
// ==============================================================================
async function loadDataSources() {
    try {
        const res = await apiFetch("/api/data/sources");
        if (!res.success) return;

        const container = document.getElementById("dataSourcesContainer");
        if (!container) return;

        container.innerHTML = res.summary.sources.map(src => `
            <div class="card" style="border-top: 3px solid var(--accent-blue);">
                <div class="card-header" style="border:none; padding-bottom: 0.25rem;">
                    <div>
                        <span class="badge badge-info" style="margin-bottom: 0.35rem;">${src.source_type}</span>
                        <h3 style="font-size: 1.05rem;">${src.name}</h3>
                    </div>
                    <a href="${src.url}" target="_blank" rel="noopener" class="btn btn-secondary btn-icon" title="View Source">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    </a>
                </div>
                <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
                    ${src.description}
                </p>
                <div style="background: rgba(15,23,42,0.6); padding: 0.65rem; border-radius: var(--radius-sm); font-size: 0.78rem;">
                    <div style="display:flex; justify-content:space-between; margin-bottom: 0.2rem;">
                        <span style="color:var(--text-muted);">Provider:</span>
                        <strong style="color:var(--text-primary);">${src.provider}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom: 0.2rem;">
                        <span style="color:var(--text-muted);">Original Records:</span>
                        <span style="color:var(--primary-light); font-weight:600;">${src.original_records}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:var(--text-muted);">Warehouse Dest:</span>
                        <code style="color:var(--accent-blue);">${src.warehouse_destination}</code>
                    </div>
                </div>
            </div>
        `).join("");
    } catch (e) {
        console.error("Failed to load sources:", e);
    }
}

// ==============================================================================
// 3. RAW DATA SAMPLE TABLE WITH PAGINATION & SEARCH
// ==============================================================================
async function loadRawDataSample(page = 1, search = "") {
    currentDataPage = page;
    currentSearchTerm = search;
    try {
        const res = await apiFetch(`/api/data/raw-sample?page=${page}&limit=12&search=${encodeURIComponent(search)}`);
        if (!res.success) return;

        const tbody = document.getElementById("rawDataTableBody");
        if (!tbody) return;

        if (res.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding: 2rem; color: var(--text-muted);">No records found matching search query.</td></tr>`;
            return;
        }

        tbody.innerHTML = res.data.map(r => `
            <tr>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: var(--text-muted);">#${r.original_record_id}</td>
                <td>Wk ${r.week_number} (${r.month_name})</td>
                <td><strong>${r.item_name}</strong> <span style="font-size:0.72rem; color:var(--text-muted);">(${r.cuisine})</span></td>
                <td>${r.category}</td>
                <td style="font-size:0.78rem;">${r.center_name.split('(')[0]}</td>
                <td>$${r.checkout_price.toFixed(2)}</td>
                <td><span style="font-weight:600; color:var(--accent-blue);">${r.sold_qty.toLocaleString()}</span></td>
                <td>${r.prepared_qty.toLocaleString()}</td>
                <td><span style="color:var(--accent-rose); font-weight:600;">${r.waste_qty.toLocaleString()}</span></td>
                <td>
                    <span class="badge ${r.waste_percentage > 14 ? 'badge-danger' : r.waste_percentage > 9 ? 'badge-warning' : 'badge-success'}">
                        ${r.waste_percentage}%
                    </span>
                </td>
            </tr>
        `).join("");

        // Update pagination labels
        const pageInfo = document.getElementById("dataPaginationInfo");
        if (pageInfo) pageInfo.textContent = `Page ${res.page} of ${res.total_pages} (${res.total_records.toLocaleString()} records)`;
        const prevBtn = document.getElementById("btnPrevPage");
        if (prevBtn) prevBtn.disabled = res.page <= 1;
        const nextBtn = document.getElementById("btnNextPage");
        if (nextBtn) nextBtn.disabled = res.page >= res.total_pages;
    } catch (e) {
        console.error("Failed to load raw data:", e);
    }
}

// ==============================================================================
// 4. ETL STATUS
// ==============================================================================
async function loadETLStatus() {
    try {
        const res = await apiFetch("/api/etl/status");
        if (!res.success) return;

        const st = res.status;
        const badge = document.getElementById("etlStatusBadge");
        if (badge) {
            badge.textContent = st.warehouse_status;
            badge.className = `badge ${st.warehouse_status === 'ONLINE' ? 'badge-success' : 'badge-warning'}`;
        }
        const recordsEl = document.getElementById("etlFactRecords");
        if (recordsEl) recordsEl.textContent = st.fact_records.toLocaleString();

        const logContainer = document.getElementById("etlLogContainer");
        if (logContainer && st.recent_logs) {
            logContainer.innerHTML = st.recent_logs.map(l => `
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); font-size: 0.8rem;">
                    <div>
                        <span class="badge ${l.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}" style="margin-right:0.5rem;">${l.step_name}</span>
                        <span>${l.details}</span>
                    </div>
                    <div style="color:var(--text-muted); font-size:0.74rem;">
                        ${l.execution_time_sec}s · ${l.run_timestamp}
                    </div>
                </div>
            `).join("");
        }
    } catch (e) {
        console.error("Failed to load ETL status:", e);
    }
}

// Event Listeners for search, upload, pagination
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("dataSearchInput");
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadRawDataSample(1, e.target.value.trim());
            }, 300);
        });
    }

    const btnPrev = document.getElementById("btnPrevPage");
    if (btnPrev) {
        btnPrev.addEventListener("click", () => {
            if (currentDataPage > 1) loadRawDataSample(currentDataPage - 1, currentSearchTerm);
        });
    }

    const btnNext = document.getElementById("btnNextPage");
    if (btnNext) {
        btnNext.addEventListener("click", () => {
            loadRawDataSample(currentDataPage + 1, currentSearchTerm);
        });
    }

    const btnRunETL = document.getElementById("btnRunETL");
    if (btnRunETL) {
        btnRunETL.addEventListener("click", async () => {
            if (AppState.currentUser?.role === "Viewer") {
                showToast("Viewers have read-only access. Sign in as Admin or Analyst to trigger ETL.", "error");
                return;
            }
            btnRunETL.disabled = true;
            btnRunETL.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running ETL...';
            try {
                const res = await apiFetch("/api/etl/run", {
                    method: "POST",
                    body: { record_count: 75000 }
                });
                if (res.success) {
                    showToast(`ETL Completed: Loaded ${res.result.records_loaded} records in ${res.result.durations.total_sec}s!`, "success");
                    await loadETLStatus();
                    await loadRawDataSample(1);
                    await loadDatasetCatalog();
                }
            } catch (err) {
                showToast("ETL execution failed: " + err.message, "error");
            } finally {
                btnRunETL.disabled = false;
                btnRunETL.innerHTML = '<i class="fa-solid fa-rotate"></i> Re-Run ETL Pipeline';
            }
        });
    }

    const uploadForm = document.getElementById("uploadDatasetForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", handleUploadDatasetSubmit);
    }
});
