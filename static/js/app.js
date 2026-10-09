// ==============================================================================
// SMART FOOD & WASTE INTELLIGENCE SYSTEM
// Core Application Router & Authentication State Manager
// ==============================================================================

const AppState = {
    currentUser: null,
    authToken: localStorage.getItem("smartfood_token") || null,
    currentRoute: "dashboard",
    pendingOtpEmail: null,
    charts: {}
};

// Toast notification helper
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "fa-circle-check text-emerald" :
                 type === "error" ? "fa-circle-exclamation text-rose" : "fa-circle-info text-blue";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Router
function navigateTo(routeId) {
    if (!AppState.authToken) {
        showAuthScreen();
        return;
    }

    // Role-based route guard
    if (routeId === "admin" && AppState.currentUser?.role !== "Admin") {
        showToast("Access Denied: Only Admin role can access system administration.", "error");
        return;
    }

    // Hide all pages
    document.querySelectorAll(".page-section").forEach(sec => sec.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));

    // Activate selected section
    const target = document.getElementById(`page-${routeId}`);
    if (target) {
        target.classList.add("active");
        AppState.currentRoute = routeId;
        window.location.hash = routeId;

        // Highlight nav item
        const navItem = document.querySelector(`.nav-item[data-route="${routeId}"]`);
        if (navItem) navItem.classList.add("active");

        // Trigger page-specific data load
        loadPageData(routeId);
    }
}

function loadPageData(routeId) {
    if (routeId === "dashboard") {
        if (window.loadDashboard) window.loadDashboard();
        if (window.initPeriodicMonitoring) window.initPeriodicMonitoring();
    } else if (routeId === "data-management") {
        if (window.loadDataManagement) window.loadDataManagement();
    } else if (routeId === "mining") {
        if (window.loadMining) window.loadMining();
    } else if (routeId === "predictions") {
        if (window.loadPredictions) window.loadPredictions();
    } else if (routeId === "dwm-analysis") {
        if (window.loadDWMAnalysis) window.loadDWMAnalysis();
    } else if (routeId === "reports") {
        if (window.loadReports) window.loadReports();
    } else if (routeId === "admin") {
        if (window.loadAdmin) window.loadAdmin();
    }
}

// API fetch wrapper with Auth header
async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (AppState.authToken) {
        headers["Authorization"] = `Bearer ${AppState.authToken}`;
    }
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }
    options.headers = headers;

    try {
        const response = await fetch(url, options);
        if (response.status === 401) {
            // Token expired or invalid
            AppState.authToken = null;
            AppState.currentUser = null;
            localStorage.removeItem("smartfood_token");
            showAuthScreen();
            throw new Error("Authentication session expired. Please sign in.");
        }
        return await response.json();
    } catch (err) {
        console.error("API error:", err);
        throw err;
    }
}

// ==============================================================================
// AUTHENTICATION & GATING SCREEN CONTROLLER
// ==============================================================================

function showAuthScreen() {
    const mainApp = document.getElementById("mainAppContainer");
    const authScreen = document.getElementById("authLandingScreen");
    if (mainApp) mainApp.style.display = "none";
    if (authScreen) authScreen.style.display = "flex";
    resetAuthForms();
}

function showMainApp() {
    const mainApp = document.getElementById("mainAppContainer");
    const authScreen = document.getElementById("authLandingScreen");
    if (authScreen) authScreen.style.display = "none";
    if (mainApp) mainApp.style.display = "block";
    updateUserUI();
    const hash = window.location.hash.replace("#", "") || "dashboard";
    navigateTo(hash === "warehouse" ? "dashboard" : hash);
}

function resetAuthForms() {
    // Show login step 1, hide OTP step 2
    const loginWrapper = document.getElementById("loginFormWrapper");
    const otpWrapper = document.getElementById("otpFormWrapper");
    const regWrapper = document.getElementById("registerFormWrapper");
    if (loginWrapper) loginWrapper.style.display = "block";
    if (otpWrapper) otpWrapper.style.display = "none";
    if (regWrapper) regWrapper.style.display = "none";

    // Reset tab buttons
    document.querySelectorAll(".auth-tab-btn").forEach(b => b.classList.remove("active"));
    const signinTab = document.getElementById("tabBtnSignIn");
    if (signinTab) signinTab.classList.add("active");
}

function switchAuthTab(tab) {
    const loginWrapper = document.getElementById("loginFormWrapper");
    const otpWrapper = document.getElementById("otpFormWrapper");
    const regWrapper = document.getElementById("registerFormWrapper");
    document.querySelectorAll(".auth-tab-btn").forEach(b => b.classList.remove("active"));

    if (tab === "signin") {
        document.getElementById("tabBtnSignIn")?.classList.add("active");
        if (loginWrapper) loginWrapper.style.display = "block";
        if (otpWrapper) otpWrapper.style.display = "none";
        if (regWrapper) regWrapper.style.display = "none";
    } else if (tab === "register") {
        document.getElementById("tabBtnRegister")?.classList.add("active");
        if (loginWrapper) loginWrapper.style.display = "none";
        if (otpWrapper) otpWrapper.style.display = "none";
        if (regWrapper) regWrapper.style.display = "block";
    }
}

// User Profile & Navigation Role UI Updates
function updateUserUI() {
    const userBadge = document.getElementById("navUserBadge");
    const userName = document.getElementById("navUserName");
    const adminNavItem = document.querySelector('.nav-item[data-route="admin"]');

    if (AppState.currentUser) {
        if (userBadge) {
            userBadge.className = `role-badge role-${AppState.currentUser.role}`;
            userBadge.textContent = AppState.currentUser.role;
        }
        if (userName) {
            userName.textContent = AppState.currentUser.full_name;
        }

        // Show/hide admin nav depending on role
        if (adminNavItem) {
            adminNavItem.style.display = AppState.currentUser.role === "Admin" ? "flex" : "none";
        }

        // Manage Continuous Data Upload button display for Admin/Analyst vs Viewer
        const contUploadBtn = document.getElementById("btnContinuousUploadTrigger");
        if (contUploadBtn) {
            contUploadBtn.style.display = AppState.currentUser.role === "Viewer" ? "none" : "inline-flex";
        }
    }
}

// Check session on initial page load
async function checkAuthSession() {
    if (AppState.authToken) {
        try {
            const res = await apiFetch("/api/auth/me");
            if (res.success) {
                AppState.currentUser = res.user;
                showMainApp();
                return;
            }
        } catch (e) {
            console.warn("Session check failed:", e);
        }
    }
    // Not authenticated -> show authentication screen
    showAuthScreen();
}

// Logout handler
function logout() {
    AppState.authToken = null;
    AppState.currentUser = null;
    AppState.pendingOtpEmail = null;
    localStorage.removeItem("smartfood_token");
    window.location.hash = "";
    showToast("Signed out successfully. Please sign in to continue.", "info");
    showAuthScreen();
}

// Evaluation Quick-Switch Persona helper
async function demoSwitchRole(role) {
    try {
        const res = await fetch("/api/auth/demo-switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role: role })
        });
        const data = await res.json();
        if (data.success) {
            AppState.authToken = data.token;
            AppState.currentUser = data.user;
            localStorage.setItem("smartfood_token", data.token);
            closeAuthModal();
            showMainApp();
            showToast(`Signed in as ${role} (${data.user.email})`, "success");
        } else {
            showToast(data.error || "Sign-in failed", "error");
        }
    } catch (e) {
        showToast("Role switch failed: " + e.message, "error");
    }
}

function openAuthModal() {
    const modal = document.getElementById("authModalOverlay");
    if (modal) modal.classList.add("active");
}

function closeAuthModal() {
    const modal = document.getElementById("authModalOverlay");
    if (modal) modal.classList.remove("active");
}

// Fill login fields with demo credentials
function fillDemoCredentials(email, pwd) {
    switchAuthTab("signin");
    const emailInput = document.getElementById("loginEmail");
    const pwdInput = document.getElementById("loginPassword");
    if (emailInput) emailInput.value = email;
    if (pwdInput) pwdInput.value = pwd;
}

// ==============================================================================
// DOM EVENT LISTENERS & FORM SUBMISSIONS
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // Nav click handlers
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const route = item.getAttribute("data-route");
            if (route) navigateTo(route);
        });
    });

    // 1. Step 1: Login Form Submit
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value.trim();
            const submitBtn = document.getElementById("btnLoginSubmit");

            if (!email || !password) {
                showToast("Please provide both email and password.", "error");
                return;
            }

            try {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
                }

                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();

                if (data.step === "OTP_REQUIRED") {
                    AppState.pendingOtpEmail = data.email;
                    // Transition to Step 2: OTP screen
                    document.getElementById("loginFormWrapper").style.display = "none";
                    document.getElementById("registerFormWrapper").style.display = "none";
                    const otpWrapper = document.getElementById("otpFormWrapper");
                    otpWrapper.style.display = "block";

                    document.getElementById("otpTargetEmailDisplay").textContent = data.email;
                    const demoHintEl = document.getElementById("otpDemoCodeHint");
                    if (demoHintEl && data.demo_otp) {
                        demoHintEl.innerHTML = `<i class="fa-solid fa-key text-amber"></i> Verification Code (Test/Demo): <strong>${data.demo_otp}</strong>`;
                    }

                    const otpInput = document.getElementById("otpCodeInput");
                    if (otpInput) {
                        otpInput.value = "";
                        otpInput.focus();
                    }
                    showToast(data.message, "info");
                } else if (data.step === "AUTHENTICATED") {
                    // Fallback direct login
                    AppState.authToken = data.token;
                    AppState.currentUser = data.user;
                    localStorage.setItem("smartfood_token", data.token);
                    showMainApp();
                    showToast(`Welcome back, ${data.user.full_name}!`, "success");
                } else {
                    showToast(data.error || "Authentication failed", "error");
                }
            } catch (err) {
                showToast("Connection error: " + err.message, "error");
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right"></i> Continue to 2-Step OTP';
                }
            }
        });
    }

    // 2. Step 2: OTP Verification Form Submit
    const otpForm = document.getElementById("otpVerifyForm");
    if (otpForm) {
        otpForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const otpCode = document.getElementById("otpCodeInput").value.trim();
            const verifyBtn = document.getElementById("btnVerifyOtpSubmit");

            if (!otpCode || otpCode.length < 6) {
                showToast("Please enter the 6-digit OTP code.", "error");
                return;
            }

            try {
                if (verifyBtn) {
                    verifyBtn.disabled = true;
                    verifyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying Code...';
                }

                const res = await fetch("/api/auth/verify-otp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: AppState.pendingOtpEmail,
                        otp_code: otpCode
                    })
                });
                const data = await res.json();

                if (data.success && data.token) {
                    AppState.authToken = data.token;
                    AppState.currentUser = data.user;
                    localStorage.setItem("smartfood_token", data.token);
                    showMainApp();
                    showToast(`2-Step Verification Complete! Signed in as ${data.user.role}.`, "success");
                } else {
                    showToast(data.error || "OTP verification failed", "error");
                }
            } catch (err) {
                showToast("Verification error: " + err.message, "error");
            } finally {
                if (verifyBtn) {
                    verifyBtn.disabled = false;
                    verifyBtn.innerHTML = '<i class="fa-solid fa-shield-check"></i> Verify OTP & Enter System';
                }
            }
        });
    }

    // 3. Register / Create User Form Submit
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const fullName = document.getElementById("regFullName").value.trim();
            const email = document.getElementById("regEmail").value.trim();
            const password = document.getElementById("regPassword").value.trim();
            const role = document.getElementById("regRole").value;
            const regBtn = document.getElementById("btnRegisterSubmit");

            if (!fullName || !email || !password) {
                showToast("Please fill in all required fields.", "error");
                return;
            }

            try {
                if (regBtn) {
                    regBtn.disabled = true;
                    regBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';
                }

                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        full_name: fullName,
                        email: email,
                        password: password,
                        role: role
                    })
                });
                const data = await res.json();

                if (data.success) {
                    showToast(data.message, "success");
                    // Pre-fill login email and switch to sign in tab
                    fillDemoCredentials(email, password);
                } else {
                    showToast(data.error || "Account creation failed", "error");
                }
            } catch (err) {
                showToast("Registration error: " + err.message, "error");
            } finally {
                if (regBtn) {
                    regBtn.disabled = false;
                    regBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';
                }
            }
        });
    }

    // Check session on start
    checkAuthSession();
});

// Admin Panel dynamic user listing
window.loadAdmin = async function() {
    try {
        const res = await apiFetch("/api/admin/users");
        if (!res.success) return;
        const tbody = document.getElementById("adminUsersTableBody");
        if (!tbody) return;
        tbody.innerHTML = res.users.map(u => `
            <tr>
                <td>#${u.user_id}</td>
                <td><strong>${escapeHtml(u.full_name)}</strong></td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="badge role-${u.role}">${u.role}</span></td>
            </tr>
        `).join("");
    } catch (e) {
        console.warn("Failed to load admin users:", e);
    }
};

function escapeHtml(text) {
    if (!text) return "";
    return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
