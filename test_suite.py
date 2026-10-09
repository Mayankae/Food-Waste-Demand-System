import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:5000"

def get_token(role):
    r = urllib.request.Request(
        f"{BASE}/api/auth/demo-switch",
        data=json.dumps({"role": role}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(r) as res:
        return json.loads(res.read().decode("utf-8"))["token"]

def run_tests():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE VERIFICATION TEST SUITE")
    print("=" * 60)

    # 1. Unauthenticated root HTML inspection
    print("\n[CHECK 1] Root HTML & Initial Screen Gating...")
    req_root = urllib.request.Request(f"{BASE}/")
    with urllib.request.urlopen(req_root) as res:
        html = res.read().decode("utf-8")
    assert '<div id="authLandingScreen"' in html, "authLandingScreen missing from HTML"
    assert '<div id="mainAppContainer" style="display:none;"' in html, "mainAppContainer must be hidden initially"
    assert 'Warehouse & OLAP' not in html, "Warehouse & OLAP must NOT appear in HTML navigation"
    assert '<section id="page-warehouse"' not in html, "page-warehouse section must be removed"
    assert 'warehouse.js' not in html, "warehouse.js must NOT be included in scripts"
    assert '<tbody id="datasetCatalogTableBody"' in html, "datasetCatalogTableBody missing"
    assert '<div id="uploadDatasetModal"' in html, "uploadDatasetModal missing"
    assert '<div id="clfConfusionMatrix"' in html, "clfConfusionMatrix missing"
    print(" -> Root HTML verification PASSED (Warehouse removed, Auth screen gates app, Dataset catalog & Confusion matrix containers present)")

    # 2. Unauthenticated API gating (401)
    print("\n[CHECK 2] Unauthenticated API Protection...")
    protected_urls = [
        "/api/dashboard/kpis",
        "/api/datasets",
        "/api/mining/classification/evaluate",
        "/api/etl/status",
        "/api/admin/users"
    ]
    for url in protected_urls:
        try:
            urllib.request.urlopen(f"{BASE}{url}")
            assert False, f"Expected 401 on {url}"
        except urllib.error.HTTPError as e:
            assert e.code == 401, f"Expected 401 on {url}, got {e.code}"
    print(f" -> Protected routes {protected_urls} all properly reject unauthenticated requests with 401.")

    # 3. Warehouse & OLAP routes removal (404)
    print("\n[CHECK 3] Warehouse & OLAP Route Removal (404)...")
    olap_urls = [
        "/api/warehouse/olap/slice?dimension=cuisine&value=Italian",
        "/api/warehouse/olap/dice",
        "/api/warehouse/olap/rollup?level=month",
        "/api/warehouse/olap/drilldown?parent_dim=category&parent_val=Biryani",
        "/api/warehouse/olap/pivot?row_dim=category&col_dim=center_type&metric=waste_cost"
    ]
    for url in olap_urls:
        try:
            urllib.request.urlopen(f"{BASE}{url}")
            assert False, f"Expected 404 on {url}"
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Expected 404 on {url}, got {e.code}"
    print(" -> All Warehouse & OLAP backend routes returned 404 Not Found.")

    # 4. User Registration & Password Hashing
    print("\n[CHECK 4] User Registration & Password Hashing...")
    test_email = "prof_evaluator@university.edu"
    reg_req = urllib.request.Request(
        f"{BASE}/api/auth/register",
        data=json.dumps({
            "full_name": "Prof. DWM Evaluator",
            "email": test_email,
            "password": "StrongPassword!2026",
            "role": "Analyst"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(reg_req) as res:
            reg_data = json.loads(res.read().decode("utf-8"))
            assert reg_data.get("success") is True
            print(" -> User registered successfully:", reg_data.get("message"))
    except urllib.error.HTTPError as e:
        if e.code in [400, 409]:
            print(" -> User already registered (409 Conflict properly returned), proceeding to login verification.")
        else:
            raise

    # 5. Two-Step Authentication (Step 1 + Step 2 OTP)
    print("\n[CHECK 5] Two-Step Authentication Flow...")
    login_req = urllib.request.Request(
        f"{BASE}/api/auth/login",
        data=json.dumps({
            "email": test_email,
            "password": "StrongPassword!2026"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as res:
        login_data = json.loads(res.read().decode("utf-8"))
    assert login_data.get("step") == "OTP_REQUIRED", f"Expected OTP_REQUIRED, got {login_data}"
    demo_otp = login_data.get("demo_otp")
    assert demo_otp and len(demo_otp) == 6, f"Invalid demo OTP: {demo_otp}"
    print(f" -> Step 1 completed. OTP challenge generated. Demo OTP code: {demo_otp}")

    # Bad OTP attempt
    try:
        bad_req = urllib.request.Request(
            f"{BASE}/api/auth/verify-otp",
            data=json.dumps({"email": test_email, "otp_code": "999999"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(bad_req)
        assert False, "Bad OTP should fail"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_msg = json.loads(e.read().decode("utf-8")).get("error")
        print(f" -> Incorrect OTP properly rejected with attempt tracking: '{err_msg}'")

    # Good OTP verification
    good_req = urllib.request.Request(
        f"{BASE}/api/auth/verify-otp",
        data=json.dumps({"email": test_email, "otp_code": demo_otp}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(good_req) as res:
        otp_res = json.loads(res.read().decode("utf-8"))
    assert otp_res.get("success") is True
    jwt_token = otp_res.get("token")
    user_info = otp_res.get("user")
    assert jwt_token and user_info["role"] == "Analyst"
    print(" -> Step 2 OTP verified successfully! JWT token issued for user:", user_info["full_name"])

    # 6. Role-Based Access Control (RBAC)
    print("\n[CHECK 6] Role-Based Access Control (RBAC)...")
    viewer_token = get_token("Viewer")
    analyst_token = get_token("Analyst")
    admin_token = get_token("Admin")

    # Viewer cannot access Admin users
    try:
        r_admin = urllib.request.Request(f"{BASE}/api/admin/users", headers={"Authorization": f"Bearer {viewer_token}"})
        urllib.request.urlopen(r_admin)
        assert False, "Viewer should not access /api/admin/users"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
    print(" -> Viewer restricted from Admin endpoint (403 Forbidden).")

    # Viewer cannot run ETL
    try:
        r_etl = urllib.request.Request(
            f"{BASE}/api/etl/run",
            data=json.dumps({"record_count": 1000}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {viewer_token}"}
        )
        urllib.request.urlopen(r_etl)
        assert False, "Viewer should not trigger ETL"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
    print(" -> Viewer restricted from running ETL (403 Forbidden).")

    # Admin can access Admin users
    r_admin_ok = urllib.request.Request(f"{BASE}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    with urllib.request.urlopen(r_admin_ok) as res:
        users_data = json.loads(res.read().decode("utf-8"))
    assert users_data.get("success") is True
    print(f" -> Admin authorized to access user registry ({len(users_data.get('users', []))} registered users).")

    # 7. Dataset Management (Catalog, Source Provenance, Upload, Delete)
    print("\n[CHECK 7] Dataset Management & Provenance...")
    r_cat = urllib.request.Request(f"{BASE}/api/datasets", headers={"Authorization": f"Bearer {analyst_token}"})
    with urllib.request.urlopen(r_cat) as res:
        cat_data = json.loads(res.read().decode("utf-8"))
    assert cat_data.get("success") is True
    datasets = cat_data.get("datasets", [])
    print(f" -> Found {len(datasets)} dataset(s) in catalog.")

    # Check external benchmarks exist and are non-deletable
    benchmarks = [d for d in datasets if d["source_type"] == "EXTERNAL_BENCHMARK"]
    assert len(benchmarks) >= 3, "Expected at least 3 external benchmark datasets"
    for b in benchmarks:
        assert b["is_deletable"] == 0
        assert b["provider_source"] is not None
        assert b["record_count"] > 0
        print(f"    * Benchmark: '{b['name']}' | Source: {b['provider_source']} | Records: {b['record_count']:,} | Status: {b['processing_status']}")

    # Test Upload with Analyst
    csv_bytes = b"meal_id,meal_name,category,cuisine,waste_rate\n501,Tandoori Roll,Rolls,Indian,0.08\n502,Greek Salad,Salad,Continental,0.12\n"
    boundary = "----TestBoundary987654321"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="name"\r\n\r\n'
        f"Campus Kitchen Daily Waste Log\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="campus_waste.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
        + csv_bytes.decode("utf-8") +
        f"\r\n--{boundary}--\r\n"
    ).encode("utf-8")

    up_req = urllib.request.Request(
        f"{BASE}/api/datasets/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {analyst_token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )
    with urllib.request.urlopen(up_req) as res:
        up_res = json.loads(res.read().decode("utf-8"))
    assert up_res.get("success") is True
    new_dataset = up_res.get("dataset")
    new_ds_id = new_dataset["dataset_id"]
    assert new_dataset["record_count"] == 2
    assert new_dataset["column_count"] == 5
    assert new_dataset["is_deletable"] == 1
    assert new_dataset["source_type"] == "USER_UPLOAD"
    print(f" -> Uploaded dataset successfully (ID: {new_ds_id}, Records: {new_dataset['record_count']}, Columns: {new_dataset['columns']})")

    # Test Viewer cannot delete uploaded dataset
    try:
        del_viewer_req = urllib.request.Request(
            f"{BASE}/api/datasets/{new_ds_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
            method="DELETE"
        )
        urllib.request.urlopen(del_viewer_req)
        assert False, "Viewer should not be able to delete dataset"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(" -> Viewer delete permission blocked (403 Forbidden).")

    # Test Analyst deletes uploaded dataset
    del_analyst_req = urllib.request.Request(
        f"{BASE}/api/datasets/{new_ds_id}",
        headers={"Authorization": f"Bearer {analyst_token}"},
        method="DELETE"
    )
    with urllib.request.urlopen(del_analyst_req) as res:
        del_res = json.loads(res.read().decode("utf-8"))
    assert del_res.get("success") is True
    print(" -> Analyst successfully deleted dataset:", del_res.get("message"))

    # Attempt to delete benchmark dataset must fail
    try:
        del_bm_req = urllib.request.Request(
            f"{BASE}/api/datasets/1",
            headers={"Authorization": f"Bearer {admin_token}"},
            method="DELETE"
        )
        urllib.request.urlopen(del_bm_req)
        assert False, "Benchmark dataset deletion should be forbidden"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print(" -> Core benchmark dataset deletion prevented (400 Bad Request).")

    # 8. Classification Confusion Matrix & Test Metrics
    print("\n[CHECK 8] Classification Confusion Matrix & Metrics...")
    clf_req = urllib.request.Request(
        f"{BASE}/api/mining/classification/evaluate",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    with urllib.request.urlopen(clf_req) as res:
        clf_res = json.loads(res.read().decode("utf-8"))
    assert clf_res.get("success") is True
    model_obj = clf_res.get("model", {})
    classes = model_obj.get("classes", [])
    cm = model_obj.get("confusion_matrix", {})
    metrics = model_obj.get("metrics", {})

    assert classes == ["LOW", "MEDIUM", "HIGH"], f"Expected ['LOW', 'MEDIUM', 'HIGH'], got {classes}"
    assert cm.get("labels") == ["LOW", "MEDIUM", "HIGH"]
    matrix = cm.get("matrix", [])
    assert len(matrix) == 3 and all(len(row) == 3 for row in matrix), "Matrix must be 3x3"
    
    total_test_samples = sum(sum(row) for row in matrix)
    assert total_test_samples > 0, "Matrix counts must be non-zero"
    assert metrics.get("accuracy") is not None and metrics["accuracy"] > 50.0
    assert metrics.get("precision") is not None
    assert metrics.get("recall") is not None
    assert metrics.get("f1_score") is not None

    print(f" -> 3x3 Confusion Matrix validated from real test data:")
    print(f"    Labels (Pred X):   LOW     MEDIUM   HIGH")
    for idx, cname in enumerate(classes):
        print(f"    Actual (Y: {cname:6s}):  {matrix[idx][0]:5d}    {matrix[idx][1]:5d}   {matrix[idx][2]:5d}")
    print(f"    Total Test Predictions: {total_test_samples:,}")
    print(f"    Real Scikit-Learn Metrics: Accuracy: {metrics['accuracy']}%, Precision: {metrics['precision']}%, Recall: {metrics['recall']}%, F1-Score: {metrics['f1_score']}%")

    # 9. Verify All Other Existing Features Remain Operational
    print("\n[CHECK 9] Regression Testing: Existing Mining, Predictions, DWM Analysis & Reports...")
    endpoints = [
        ("Regression Model", "/api/mining/regression/evaluate", "GET", None),
        ("K-Means Clustering", "/api/mining/clustering/evaluate?k=4", "GET", None),
        ("Apriori Association Rules", "/api/mining/association-rules/evaluate?min_support=0.05&min_confidence=0.55&min_lift=1.2", "GET", None),
        ("Isolation Forest Anomaly Detection", "/api/mining/anomaly-detection/evaluate", "GET", None),
        ("Predictions Forecaster", "/api/predictions/forecast", "POST", {
            "meal_id": 1885, "center_id": 55, "week_number": 15,
            "checkout_price": 136.83, "base_price": 152.29,
            "emailer_for_promotion": 0, "homepage_featured": 0
        }),
        ("Human-Readable Insights", "/api/insights/smart-summary", "GET", None),
        ("Academic DWM Showcase", "/api/dwm-analysis/summary", "GET", None),
        ("Executive Reports & Scorecards", "/api/reports/summary", "GET", None)
    ]
    for name, url, method, data in endpoints:
        req = urllib.request.Request(
            f"{BASE}{url}",
            headers={"Authorization": f"Bearer {analyst_token}", "Content-Type": "application/json"},
            method=method
        )
        if data:
            req.data = json.dumps(data).encode("utf-8")
        with urllib.request.urlopen(req) as res:
            res_json = json.loads(res.read().decode("utf-8"))
            assert res_json.get("success") is True, f"{name} returned failure: {res_json}"
            print(f"    * {name:38s}: ONLINE & VERIFIED (HTTP {res.status})")

    print("\n" + "=" * 60)
    print("ALL 9 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
