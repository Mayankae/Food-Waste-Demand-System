import urllib.request
import urllib.error
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:5000"

def get_token(role="Analyst"):
    req = urllib.request.Request(
        f"{BASE}/api/auth/demo-switch",
        data=json.dumps({"role": role}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))["token"]

def test_periodic_feature():
    print("=" * 60)
    print("TESTING FOOD WASTE PERIODIC MONITORING & EARLY ANALYSIS")
    print("=" * 60)

    analyst_token = get_token("Analyst")
    viewer_token = get_token("Viewer")
    admin_token = get_token("Admin")

    # 1. PERIOD OPTIONS
    print("\n[TEST 1] Period Selector Options API...")
    req_opts = urllib.request.Request(
        f"{BASE}/api/periodic-monitoring/options",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    with urllib.request.urlopen(req_opts) as res:
        opts_res = json.loads(res.read().decode("utf-8"))
    assert opts_res.get("success") is True
    opts = opts_res.get("options", {})
    assert len(opts.get("weeks", [])) >= 26
    assert len(opts.get("months", [])) >= 6
    assert opts.get("latest_week") is not None
    print(f" -> Options verified: {len(opts['weeks'])} weeks, {len(opts['months'])} months, latest week: {opts['latest_week']}")

    # 2. PERIOD COMPARISON FOR ALL CADENCES
    print("\n[TEST 2] Period Comparison Analysis across Cadences...")
    cadences = [
        ("Weekly (Week 26)", "weekly", "26", None, None),
        ("Monthly (June)", "monthly", "June", None, None),
        ("Daily (2024-06-24)", "daily", "2024-06-24", None, None),
        ("Yearly (2024)", "yearly", "2024", None, None),
        ("Custom Date Range", "custom", None, "2024-02-01", "2024-02-28")
    ]

    for label, p_type, p_val, s_date, e_date in cadences:
        url = f"{BASE}/api/periodic-monitoring/analyze?period_type={p_type}"
        if p_val: url += f"&value={p_val}"
        if s_date: url += f"&start_date={s_date}"
        if e_date: url += f"&end_date={e_date}"

        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {analyst_token}"})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
        assert data.get("success") is True
        an = data.get("analysis", {})

        cur = an["current_metrics"]
        prev = an["previous_metrics"]
        comp = an["comparison"]
        ex = an["example_summary"]
        warn = an["early_warning"]

        # Assert all required fields
        assert "food_prepared" in cur and "food_sold" in cur and "food_wasted" in cur and "waste_percentage" in cur
        assert "food_prepared" in prev and "food_sold" in prev and "food_wasted" in prev and "waste_percentage" in prev
        assert "waste_change_qty" in comp and "waste_change_display" in comp
        assert warn["status"] in ["NORMAL", "WARNING", "CRITICAL"]

        print(f" -> {label:22s}: {ex['current_period_waste_title']} = {ex['current_period_waste_val']} | {ex['previous_period_waste_title']} = {ex['previous_period_waste_val']} | Change = {ex['change_display']} [{warn['badge']}]")

    # 3. EARLY WARNING SPIKE DETECTION
    print("\n[TEST 3] Automated Early Warning Detection (Week 5 Spike)...")
    req_w5 = urllib.request.Request(
        f"{BASE}/api/periodic-monitoring/analyze?period_type=weekly&value=5",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    with urllib.request.urlopen(req_w5) as res:
        w5_data = json.loads(res.read().decode("utf-8"))["analysis"]

    w5_warn = w5_data["early_warning"]
    w5_ex = w5_data["example_summary"]
    assert w5_warn["status"] == "CRITICAL", f"Expected CRITICAL, got {w5_warn['status']}"
    assert "🔴 Critical" in w5_warn["badge"]
    assert "Food waste has increased significantly compared with the previous period. Immediate review is recommended." in w5_warn["message"]
    assert float(w5_data["comparison"]["waste_change_pct"]) > 100.0

    print(f" -> Early Warning correctly triggered:")
    print(f"    Current Week Waste:  {w5_ex['current_period_waste_val']}")
    print(f"    Previous Week Waste: {w5_ex['previous_period_waste_val']}")
    print(f"    Change:              {w5_ex['change_display']}")
    print(f"    Status:              {w5_warn['badge']}")
    print(f"    Action Message:      '{w5_warn['message']}'")

    # 4. CONTINUOUS DATA UPLOAD (WITHOUT DELETING PREVIOUS RECORDS)
    print("\n[TEST 4] Continuous Data Ingestion (Append without Deleting)...")
    
    # Check baseline count before upload
    req_kpi_before = urllib.request.Request(f"{BASE}/api/dashboard/kpis", headers={"Authorization": f"Bearer {analyst_token}"})
    with urllib.request.urlopen(req_kpi_before) as res:
        before_records = json.loads(res.read().decode("utf-8"))["kpis"]["total_records"]
    print(f" -> Warehouse record count before continuous upload: {before_records:,}")

    # Prepare sample continuous upload CSV
    csv_content = (
        "id,week,center_id,meal_id,checkout_price,base_price,emailer_for_promotion,homepage_featured,num_orders\n"
        "3000001,28,55,1885,140.0,155.0,0,0,120\n"
        "3000002,28,55,1993,125.0,140.0,0,0,95\n"
        "3000003,28,55,2539,180.0,200.0,1,0,210\n"
        "3000004,28,55,1248,110.0,120.0,0,0,80\n"
        "3000005,28,55,2631,160.0,175.0,0,0,150\n"
    )
    boundary = "----ContinuousUploadTestBoundary123"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="name"\r\n\r\n'
        f"Week 28 Incremental Operational Feed\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="cadence"\r\n\r\n'
        f"weekly\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="week28_incremental.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
        + csv_content +
        f"\r\n--{boundary}--\r\n"
    ).encode("utf-8")

    # Viewer should be blocked (RBAC)
    try:
        up_viewer = urllib.request.Request(
            f"{BASE}/api/periodic-monitoring/upload",
            data=body,
            headers={"Authorization": f"Bearer {viewer_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        urllib.request.urlopen(up_viewer)
        assert False, "Viewer should not be able to upload continuous data"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(" -> Viewer restricted from continuous upload (403 Forbidden).")

    # Analyst uploads continuous dataset
    up_req = urllib.request.Request(
        f"{BASE}/api/periodic-monitoring/upload",
        data=body,
        headers={"Authorization": f"Bearer {analyst_token}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(up_req) as res:
        up_data = json.loads(res.read().decode("utf-8"))
    assert up_data.get("success") is True
    res_obj = up_data.get("result", {})
    assert res_obj["records_added"] == 5
    assert res_obj["total_fact_records"] == before_records + 5
    print(f" -> Continuous upload succeeded: +{res_obj['records_added']} records added. New total: {res_obj['total_fact_records']:,}")

    # Check warehouse count after upload
    with urllib.request.urlopen(req_kpi_before) as res:
        after_records = json.loads(res.read().decode("utf-8"))["kpis"]["total_records"]
    assert after_records == before_records + 5, f"Expected {before_records + 5}, got {after_records}"
    print(f" -> VERIFIED: All historical records preserved ({before_records:,}), new records appended seamlessly ({after_records:,}).")

    # Check that newly uploaded Week 28 can now be analyzed in the Period Selector!
    req_w28 = urllib.request.Request(
        f"{BASE}/api/periodic-monitoring/analyze?period_type=weekly&value=28",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    with urllib.request.urlopen(req_w28) as res:
        w28_an = json.loads(res.read().decode("utf-8"))["analysis"]
    assert w28_an["current_metrics"]["record_count"] == 5
    assert w28_an["current_period_label"] == "Week 28"
    print(f" -> Newly ingested Week 28 immediately analyzed: {w28_an['current_metrics']['record_count']} records, Food Prepared: {w28_an['current_metrics']['food_prepared']}, Food Wasted: {w28_an['current_metrics']['food_wasted']}")

    print("\n" + "=" * 60)
    print("ALL PERIODIC MONITORING & CONTINUOUS UPLOAD TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_periodic_feature()
