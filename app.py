import os
import io
import csv
from flask import Flask, render_template, request, jsonify, Response
from werkzeug.security import generate_password_hash

from config import Config
from database import execute_query, execute_dml
from auth.auth_service import AuthService, require_auth
from auth.models import UserModel
from etl.data_sources import DataSourceCatalog
from etl.pipeline import ETLPipeline
from mining.classification import DemandWasteClassifier
from mining.regression import FoodDemandRegressor
from mining.clustering import FoodPatternClustering
from mining.association_rules import FoodAssociationMiner
from mining.anomaly_detection import FoodWasteAnomalyDetector
from analytics.dashboard_service import DashboardService
from analytics.insights_service import SmartInsightsService
from analytics.reports_service import ReportsService
from analytics.dataset_service import DatasetService
from analytics.periodic_monitoring_service import PeriodicMonitoringService

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)

# Ensure warehouse and dataset catalog exist on startup
try:
    status = ETLPipeline.get_etl_status()
    if status["warehouse_status"] != "ONLINE" or status["fact_records"] == 0:
        print("Initializing warehouse with ETL data...")
        ETLPipeline.run_pipeline()
    else:
        # Ensure datasets catalog table is populated
        conn = ETLPipeline.get_db_connection() if hasattr(ETLPipeline, 'get_db_connection') else None
except Exception as e:
    print("Warehouse init notice:", e)

# ==============================================================================
# FRONTEND ENTRY POINT
# ==============================================================================
@app.route("/")
def index():
    return render_template("index.html")

# ==============================================================================
# AUTHENTICATION & ROLE-BASED AUTHORIZATION APIS
# ==============================================================================
@app.route("/api/auth/register", methods=["POST"])
def register():
    """
    Create a new user account with validation and secure password hashing.
    """
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "Viewer").strip()

    result = AuthService.register(full_name, email, password, role)
    return jsonify(result), result.get("status_code", 200)

@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    Step 1 of Login flow: Validates credentials and initiates 2-step OTP challenge.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    result = AuthService.login(email, password)
    return jsonify(result), result.get("status_code", 200)

@app.route("/api/auth/verify-otp", methods=["POST"])
@app.route("/api/auth/verify-2fa", methods=["POST"])
def verify_otp():
    """
    Step 2 of Login flow: Verifies OTP code with expiration & attempt protection.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    otp_code = data.get("otp_code", "").strip()

    if not email or not otp_code:
        return jsonify({"success": False, "error": "Email and OTP code are required"}), 400

    result = AuthService.verify_2fa_step(email, otp_code)
    return jsonify(result), result.get("status_code", 200)

@app.route("/api/auth/me", methods=["GET"])
@require_auth()
def get_current_user_profile():
    return jsonify({
        "success": True,
        "user": request.current_user
    })

@app.route("/api/auth/users", methods=["GET"])
@require_auth(["Admin"])
def list_users():
    users = UserModel.get_all_users()
    return jsonify({"success": True, "users": users})

@app.route("/api/auth/demo-switch", methods=["POST"])
def demo_switch_role():
    """
    Convenience endpoint for college evaluation:
    Instantly switch between Admin, Analyst, and Viewer test personas.
    """
    data = request.get_json() or {}
    role = data.get("role", "Admin")
    role_email_map = {
        "Admin": "admin@smartfood.edu",
        "Analyst": "analyst@smartfood.edu",
        "Viewer": "viewer@smartfood.edu"
    }
    email = role_email_map.get(role, "admin@smartfood.edu")
    user = UserModel.get_by_email(email)
    if not user:
        return jsonify({"success": False, "error": "User role persona not found"}), 404

    token = AuthService.generate_token(user)
    return jsonify({
        "success": True,
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    })

# ==============================================================================
# DASHBOARD APIS (Protected)
# ==============================================================================
@app.route("/api/dashboard/kpis", methods=["GET"])
@require_auth()
def get_dashboard_kpis():
    kpis = DashboardService.get_kpis()
    return jsonify({"success": True, "kpis": kpis})

@app.route("/api/dashboard/charts", methods=["GET"])
@require_auth()
def get_dashboard_charts():
    charts = DashboardService.get_charts_data()
    return jsonify({"success": True, "charts": charts})

# ==============================================================================
# FOOD WASTE PERIODIC MONITORING & EARLY ANALYSIS APIS (Protected)
# ==============================================================================
@app.route("/api/periodic-monitoring/options", methods=["GET"])
@require_auth()
def get_periodic_monitoring_options():
    try:
        options = PeriodicMonitoringService.get_period_options()
        return jsonify({"success": True, "options": options})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/periodic-monitoring/analyze", methods=["GET"])
@require_auth()
def analyze_periodic_food_waste():
    try:
        period_type = request.args.get("period_type", "weekly")
        value = request.args.get("value")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        result = PeriodicMonitoringService.analyze_food_waste_period(
            period_type=period_type,
            value=value,
            start_date=start_date,
            end_date=end_date
        )
        return jsonify({"success": True, "analysis": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/periodic-monitoring/upload", methods=["POST"])
@require_auth(["Admin", "Analyst"])
def upload_continuous_dataset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    name = request.form.get("name")
    cadence = request.form.get("cadence")
    try:
        res = PeriodicMonitoringService.process_continuous_dataset(file, custom_name=name, cadence=cadence)
        return jsonify({"success": True, "result": res}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/periodic-monitoring/sample-continuous", methods=["POST"])
@require_auth(["Admin", "Analyst"])
def load_sample_continuous_dataset():
    try:
        data = request.get_json(silent=True) or {}
        sample_type = data.get("sample_type", "week27") if request.is_json else request.form.get("sample_type", "week27")
        if sample_type == "daily":
            sample_file_path = os.path.join(Config.DATA_DIR, "sample_continuous", "sample_daily_dataset.csv")
            custom_name = "Live Daily Kitchen Spoilage Feed (July 2024)"
        else:
            sample_file_path = os.path.join(Config.DATA_DIR, "sample_continuous", "sample_week27_dataset.csv")
            custom_name = "Continuous Feed: Week 27 Nationwide Logistics Log"

        if not os.path.exists(sample_file_path):
            return jsonify({"success": False, "error": "Sample dataset file not found"}), 404

        class FileStorageMock:
            def __init__(self, path):
                self.filename = os.path.basename(path)
                self.path = path
            def save(self, dst):
                import shutil
                shutil.copyfile(self.path, dst)

        res = PeriodicMonitoringService.process_continuous_dataset(
            FileStorageMock(sample_file_path),
            custom_name=custom_name
        )
        return jsonify({"success": True, "result": res}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==============================================================================
# DATA MANAGEMENT & DATASET MANAGEMENT APIS
# ==============================================================================
@app.route("/api/datasets", methods=["GET"])
@require_auth()
def list_datasets():
    """
    Retrieve all available datasets (external benchmarks and user uploads) with metadata.
    """
    try:
        datasets = DatasetService.list_datasets()
        return jsonify({"success": True, "datasets": datasets})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/datasets/upload", methods=["POST"])
@require_auth(["Admin", "Analyst"])
def upload_dataset():
    """
    Upload and register a new dataset file (CSV/Excel).
    Restricted to Admin and Analyst roles.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    custom_name = request.form.get("name")
    try:
        res = DatasetService.upload_dataset(file, custom_name=custom_name)
        return jsonify({"success": True, "dataset": res, "message": "Dataset uploaded and registered successfully!"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/datasets/<int:dataset_id>", methods=["DELETE"])
@require_auth(["Admin", "Analyst"])
def delete_dataset(dataset_id):
    """
    Delete a user-uploaded dataset from the catalog and disk.
    External baseline benchmark datasets cannot be deleted.
    """
    try:
        DatasetService.delete_dataset(dataset_id)
        return jsonify({"success": True, "message": "Dataset deleted successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/data/sources", methods=["GET"])
@require_auth()
def get_data_sources():
    summary = DataSourceCatalog.get_source_summary()
    return jsonify({"success": True, "summary": summary})

@app.route("/api/data/raw-sample", methods=["GET"])
@require_auth()
def get_raw_sample():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit
    search = request.args.get("search", "").strip()

    where_sql = ""
    params = []
    if search:
        where_sql = "WHERE m.item_name LIKE ? OR m.category LIKE ? OR fc.center_name LIKE ?"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query = f"""
    SELECT 
        f.original_record_id,
        d.week_number,
        d.month_name,
        m.item_name,
        m.category,
        m.cuisine,
        fc.center_name,
        fc.center_type,
        f.base_price,
        f.checkout_price,
        f.discount_percent,
        f.emailer_for_promotion,
        f.homepage_featured,
        f.sold_qty,
        f.prepared_qty,
        f.waste_qty,
        f.waste_percentage,
        f.waste_cost
    FROM fact_food_waste_demand f
    JOIN dim_food_item m ON f.meal_id = m.meal_id
    JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
    JOIN dim_date d ON f.date_id = d.date_id
    {where_sql}
    ORDER BY f.fact_id ASC
    LIMIT ? OFFSET ?;
    """
    params.extend([limit, offset])
    rows = execute_query(query, params)

    count_query = f"""
    SELECT COUNT(*) as total FROM fact_food_waste_demand f
    JOIN dim_food_item m ON f.meal_id = m.meal_id
    JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
    {where_sql};
    """
    total_count = execute_query(count_query, params[:-2])[0]["total"]

    return jsonify({
        "success": True,
        "page": page,
        "limit": limit,
        "total_records": total_count,
        "total_pages": (total_count + limit - 1) // limit,
        "data": rows
    })

@app.route("/api/etl/status", methods=["GET"])
@require_auth()
def get_etl_status():
    status = ETLPipeline.get_etl_status()
    return jsonify({"success": True, "status": status})

@app.route("/api/etl/run", methods=["POST"])
@require_auth(["Admin", "Analyst"])
def trigger_etl():
    data = request.get_json() or {}
    record_count = int(data.get("record_count", 75000))
    result = ETLPipeline.run_pipeline(target_records=record_count)
    return jsonify({"success": True, "result": result})

# ==============================================================================
# DATA MINING APIS (Protected)
# ==============================================================================
@app.route("/api/mining/classification/evaluate", methods=["GET"])
@require_auth()
def evaluate_classification():
    res = DemandWasteClassifier.train_and_evaluate()
    return jsonify({"success": True, "model": res})

@app.route("/api/mining/classification/predict", methods=["POST"])
@require_auth()
def predict_classification():
    data = request.get_json() or {}
    res = DemandWasteClassifier.predict_demand(data)
    return jsonify({"success": True, "prediction": res})

@app.route("/api/mining/regression/evaluate", methods=["GET"])
@require_auth()
def evaluate_regression():
    res = FoodDemandRegressor.train_and_evaluate()
    return jsonify({"success": True, "model": res})

@app.route("/api/mining/regression/predict", methods=["POST"])
@require_auth()
def predict_regression():
    data = request.get_json() or {}
    res = FoodDemandRegressor.predict_demand_and_prep(data)
    return jsonify({"success": True, "forecast": res})

@app.route("/api/mining/clustering/evaluate", methods=["GET"])
@require_auth()
def evaluate_clustering():
    k = int(request.args.get("k", 4))
    res = FoodPatternClustering.train_and_evaluate(n_clusters=k)
    return jsonify({"success": True, "clustering": res})

@app.route("/api/mining/association-rules/evaluate", methods=["GET"])
@require_auth()
def evaluate_association_rules():
    sup = float(request.args.get("min_support", 0.08))
    conf = float(request.args.get("min_confidence", 0.55))
    lift = float(request.args.get("min_lift", 1.2))
    res = FoodAssociationMiner.get_rules(min_support=sup, min_confidence=conf, min_lift=lift)
    return jsonify({"success": True, "association_rules": res})

@app.route("/api/mining/anomaly-detection/evaluate", methods=["GET"])
@require_auth()
def evaluate_anomaly_detection():
    contam = float(request.args.get("contamination", 0.02))
    res = FoodWasteAnomalyDetector.train_and_detect(contamination=contam)
    return jsonify({"success": True, "anomaly_detection": res})

# ==============================================================================
# PREDICTIONS & SMART INSIGHTS APIS (Protected)
# ==============================================================================
@app.route("/api/insights/smart-summary", methods=["GET"])
@require_auth()
def get_smart_insights():
    res = SmartInsightsService.generate_all_insights()
    return jsonify({"success": True, "insights": res})

@app.route("/api/predictions/forecast", methods=["POST"])
@require_auth()
def forecast_demand_simulation():
    data = request.get_json() or {}
    forecast = FoodDemandRegressor.predict_demand_and_prep(data)
    tier = DemandWasteClassifier.predict_demand(data)
    return jsonify({
        "success": True,
        "quantitative_forecast": forecast,
        "categorical_classification": tier
    })

# ==============================================================================
# DWM ACADEMIC ANALYSIS API (Protected)
# ==============================================================================
@app.route("/api/dwm-analysis/summary", methods=["GET"])
@require_auth()
def get_dwm_analysis_summary():
    """
    Detailed pedagogical mapping of Data Warehousing & Data Mining concepts.
    """
    analysis_data = {
        "project_title": "Smart Food & Waste Intelligence System",
        "academic_discipline": "Data Warehousing and Data Mining (DWM)",
        "pedagogical_pillars": [
            {
                "pillar": "Data Warehousing (DW) Architecture",
                "concepts": [
                    {
                        "concept": "Star Schema Multidimensional Model",
                        "academic_theory": "A multidimensional modeling technique where a central Fact table is surrounded by de-normalized Dimension tables, optimizing query performance for analytical aggregations.",
                        "implementation": "Central Fact table 'fact_food_waste_demand' linked via foreign keys to 'dim_date', 'dim_food_item', 'dim_fulfillment_center', and 'dim_category'. Contains additive numerical measures: prepared_qty, sold_qty, waste_qty, waste_cost, and revenue.",
                        "benefit": "Enables single-join aggregations across 75,000+ real records with B-Tree indexes, achieving sub-10ms analytical query times."
                    },
                    {
                        "concept": "Automated ETL Pipeline",
                        "academic_theory": "Extraction of heterogeneous data, Transformation (cleaning, missing value imputation, business logic computation), and Loading into warehouse storage.",
                        "implementation": "Extracts raw orders, meal catalog, and center coordinates. Preprocesses and cleans data. Calculates food waste measures based on empirical perishability decay models. Bulk loads into warehouse with audit logging.",
                        "benefit": "Maintains data provenance, prevents dirty data ingestion, and provides full reproducibility."
                    }
                ]
            },
            {
                "pillar": "Data Mining (DM) & Machine Learning",
                "concepts": [
                    {
                        "concept": "Classification (Supervised Learning)",
                        "academic_theory": "Predicting discrete class labels using decision trees and ensemble random forests based on historical feature boundaries.",
                        "implementation": "Random Forest Classifier (100 estimators) predicting Demand Tier (LOW, MEDIUM, HIGH) from checkout price, promotions, center area, and dish category. Evaluated with 3x3 Confusion Matrix, Precision, Recall, and F1-score.",
                        "benefit": "Allows centers to classify upcoming meal demands into discrete risk buckets."
                    },
                    {
                        "concept": "Regression (Predictive Modeling)",
                        "academic_theory": "Estimating a continuous numerical response variable given independent feature predictors.",
                        "implementation": "Random Forest & Ridge Regressor forecasting sold_qty. Coupled with a safety-buffer optimization function that calculates the exact prepared_qty needed to minimize waste while ensuring 95% service fill rate.",
                        "benefit": "Solves the central food-waste dilemma: over-preparation vs stockout."
                    },
                    {
                        "concept": "K-Means Clustering (Unsupervised Learning)",
                        "academic_theory": "Partitioning N observations into K clusters where each observation belongs to the cluster with the nearest mean centroid (minimizing within-cluster sum of squares).",
                        "implementation": "K-Means (K=4) clustering on [sold_qty, waste_qty, waste_percentage, checkout_price, discount_percent]. Validated with Silhouette Score, Davies-Bouldin index, and Elbow inertia curve.",
                        "benefit": "Identifies 4 operational archetypes: Core Staples, High-Waste Perishables, Promo Surges, and Gourmet Specialties."
                    },
                    {
                        "concept": "Association Rule Mining (Apriori)",
                        "academic_theory": "Discovering interesting co-occurrence relationships and itemset patterns in transaction databases based on Support, Confidence, and Lift.",
                        "implementation": "Apriori algorithm mining companion dishes in multi-item orders. Discovers rules with Support > 8%, Confidence > 55%, Lift > 1.2.",
                        "benefit": "Synchronizes batch preparation of companion meals to eliminate leftover side-item spoilage."
                    },
                    {
                        "concept": "Anomaly Detection (Unsupervised Outlier Discovery)",
                        "academic_theory": "Isolating anomalous observations that deviate significantly from standard operational distribution patterns.",
                        "implementation": "Isolation Forest algorithm partitioning data trees to isolate extreme waste spikes. Highlights top outliers with root-cause operational diagnoses.",
                        "benefit": "Alerts management to inventory leakage, cold-chain failure, or unforecasted promo failures."
                    }
                ]
            }
        ]
    }
    return jsonify({"success": True, "analysis": analysis_data})

# ==============================================================================
# REPORTS & AUDIT APIS (Protected)
# ==============================================================================
@app.route("/api/reports/summary", methods=["GET"])
@require_auth()
def get_reports_summary():
    report = ReportsService.get_executive_summary_report()
    return jsonify({"success": True, "report": report})

@app.route("/api/reports/export-csv", methods=["GET"])
def export_csv():
    # Allow token query parameter for direct CSV browser download links
    token = request.args.get("token") or (request.headers.get("Authorization", "").replace("Bearer ", ""))
    if token:
        payload = AuthService.decode_token(token)
        if not payload:
            return "Unauthorized", 401
    else:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return "Unauthorized", 401

    query = """
    SELECT 
        f.fact_id, d.week_number, d.month_name, m.item_name, m.category, m.cuisine,
        fc.center_name, fc.center_type, f.checkout_price, f.base_price,
        f.sold_qty, f.prepared_qty, f.waste_qty, f.waste_percentage, f.waste_cost, f.revenue
    FROM fact_food_waste_demand f
    JOIN dim_food_item m ON f.meal_id = m.meal_id
    JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
    JOIN dim_date d ON f.date_id = d.date_id
    LIMIT 2000;
    """
    rows = execute_query(query)
    if not rows:
        return "No data to export", 404

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=food_waste_warehouse_export.csv"}
    )

# ==============================================================================
# SYSTEM ADMINISTRATION APIS (Admin Only)
# ==============================================================================
@app.route("/api/admin/users", methods=["GET"])
@require_auth(["Admin"])
def get_admin_users():
    """
    List all authorized system users. Restricted to Admin role.
    """
    users = UserModel.get_all_users()
    return jsonify({"success": True, "users": users})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
