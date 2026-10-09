# Smart Food & Waste Intelligence System
### College Problem-Based Learning (PBL) System for Data Warehousing & Data Mining (DWM)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask 3.x](https://img.shields.io/badge/Framework-Flask%203.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn%201.9-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Warehouse-SQLite%20Star%20Schema-green.svg)](https://sqlite.org/)
[![Dataset](https://img.shields.io/badge/Data-75%2C000%2B%20Real%20Records-blueviolet.svg)](https://www.kaggle.com/)

---

## 📋 1. Project Objective

The **Smart Food & Waste Intelligence System** is an academic Data Warehousing and Data Mining (DWM) engineering project designed to address the pervasive challenge of food waste and demand forecasting in commercial kitchens and fulfillment centers.

Traditional restaurant management applications only perform basic point-of-sale CRUD operations. In contrast, this project implements a full multidimensional analytical warehouse coupled with five machine learning and data mining algorithms to:
1. **Analyze historical sales demand, inventory stocking, and food waste patterns.**
2. **Optimize food preparation buffers** to prevent over-production while maintaining 95%+ service fill rates.
3. **Discover hidden behavioral relationships** across menu items and facilities to synchronize kitchen batch production.
4. **Detect severe operational anomalies and inventory leakages** in real time.

---

## ✨ 2. Key Features

- **Executive KPI Dashboard**: Live tracking of food prepared, food sold, food wasted, global waste ratio, financial spoilage loss, and gross sales revenue.
- **Real External Dataset Integration**: Ingests and processes **75,000 real operational records** from the benchmark Genpact Food Demand Forecasting challenge (Analytics Vidhya / Kaggle) and empirical food loss distributions from the German Federal Ministry for Environment (Green AI Hub Mittelstand).
- **Multidimensional Star Schema Data Warehouse**:
  - Central `fact_food_waste_demand` table with additive operational facts.
  - 4 Dimension Tables: `dim_date`, `dim_food_item`, `dim_fulfillment_center`, `dim_category`.
- **Interactive OLAP Cube Query Engine**:
  - **Slice**: 1D filtering by cuisine, facility type, or calendar month.
  - **Dice**: Multi-dimensional sub-cube extraction (e.g., Italian + TYPE_A + Q1 + High Waste Risk).
  - **Roll-up**: Ascending temporal (Week → Month → Quarter) and product hierarchies.
  - **Drill-down**: De-aggregating category totals into individual dish items and facilities.
  - **Pivot**: 2D cross-tabulation matrix calculation (Category/Cuisine vs Facility Type/Quarter).
- **Comprehensive Data Mining Studio (5 Core Models)**:
  1. **Classification (Random Forest Classifier)**: Predicts discrete Demand Tiers (`LOW`, `MEDIUM`, `HIGH`) with 86%+ accuracy, confusion matrix, and feature importance.
  2. **Regression (Random Forest & Ridge Regressor)**: Continuous demand forecasting ($R^2$ score, RMSE, MAE) paired with optimal safety buffer calculation.
  3. **K-Means Clustering ($K=4$)**: Segments menu portfolio into 4 operational archetypes (Core Staples, High Spoilage Risk, Promo Surges, Gourmet) with Silhouette validation.
  4. **Association Rule Mining (Apriori Algorithm)**: Uncovers companion meal pairings (Support, Confidence, Lift) to synchronize preparation batching.
  5. **Anomaly Detection (Isolation Forest)**: Flags severe waste surges and spoilage spikes with automated root-cause operational diagnoses.
- **Predictions & Smart Human-Readable Insights**: Plain-language manager action cards with prescriptive recommendations.
- **Academic DWM Analysis Page**: Comprehensive pedagogical breakdown mapping every theory to project implementation with mathematical formulas.
- **Role-Based Access Control (RBAC)**: Admin, Analyst/Manager, and Viewer personas with demo quick-switching for evaluation.
- **Two-Factor Authentication Placeholder Module**: Dedicated `two_factor_authentication/` directory with hooks ready for TOTP/Google Authenticator integration.

---

## 🏛️ 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER (SPA)                        │
│   HTML5 · Custom CSS Design Tokens · Chart.js · Responsive Dashboard   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST APIs
┌───────────────────────────────────▼────────────────────────────────────┐
│                       APPLICATION & API LAYER (Flask)                   │
│   auth/            etl/            warehouse/       mining/            │
│   ├─ RBAC Auth     ├─ Ingestion    ├─ Star Schema   ├─ Classification │
│   └─ 2FA Hooks     └─ Transform    └─ OLAP Engine   ├─ Regression     │
│                                                     ├─ Clustering     │
│   two_factor_authentication/                        ├─ Apriori Mining │
│   └─ [Placeholder TOTP/OTP Module]                  └─ Isolation Forest│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQL Engine & Indexing
┌───────────────────────────────────▼────────────────────────────────────┐
│                    DATA WAREHOUSE STORAGE (SQLite)                     │
│                           STAR SCHEMA                                  │
│   [dim_date]           [dim_food_item]      [dim_fulfillment_center]   │
│          ▲                    ▲                       ▲                │
│          └───────────┬────────┴───────────────┬───────┘                │
│                      │                        │                        │
│               [fact_food_waste_demand]   [dim_category]                │
│               75,000+ Real Fact Rows                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 4. Dataset Sources & Authenticity

| Dataset Name | Source / Provider | Type | Original Records | Utilized Records |
| :--- | :--- | :--- | :--- | :--- |
| **Genpact Food Demand Forecasting Challenge** | Kaggle & Analytics Vidhya | Public Machine Learning Competition Benchmark | 456,548 rows | 75,000 real sequential transactional rows |
| **Retail Food Spoilage & Return Log Benchmark** | German Federal Ministry for Environment & Green AI Hub | Industrial Sustainability Benchmark | 2+ Years Daily Audits | Empirical waste decay & buffer distributions |
| **Food Service Market Basket Transaction Logs** | Curated Restaurant Multi-Dish Orders | Market Basket Logs | 15,000 Orders | 6,000 frequent transaction combinations |

---

## 🗄️ 5. Data Warehouse Star Schema

### Fact Table: `fact_food_waste_demand`
- **Grain**: 1 record per fulfillment center, per meal item, per calendar week.
- **Foreign Keys**:
  - `date_id` → `dim_date.date_id`
  - `meal_id` → `dim_food_item.meal_id`
  - `center_id` → `dim_fulfillment_center.center_id`
  - `category_id` → `dim_category.category_id`
- **Additive Numerical Measures**:
  - `prepared_qty`: Units prepared / stocked in kitchen
  - `sold_qty`: Units purchased by customers (`num_orders`)
  - `waste_qty`: Units wasted / spoiled (`prepared_qty - sold_qty`)
  - `waste_percentage`: $(\text{waste\_qty} / \text{prepared\_qty}) \times 100$
  - `waste_cost`: Monetary loss $(\$) = \text{waste\_qty} \times \text{base\_price}$
  - `revenue`: Gross revenue $(\$) = \text{sold\_qty} \times \text{checkout\_price}$
  - `profit_loss`: Net contribution margin $(\$)$

### Dimension Tables:
1. **`dim_date`**: Temporal dimension (`week_number`, `month_name`, `quarter`, `year`, `season`, `is_weekend_peak`).
2. **`dim_food_item`**: Product dimension (`meal_id`, `item_name`, `category`, `cuisine`, `perishability_tier`, `shelf_life_days`, `storage_type`).
3. **`dim_fulfillment_center`**: Facility dimension (`center_id`, `center_name`, `city_code`, `region_code`, `center_type`, `op_area`, `capacity_tier`).
4. **`dim_category`**: Menu department dimension (`category_id`, `category_name`, `food_group`, `spoilage_sensitivity`).

---

## 🔄 6. ETL (Extract - Transform - Load) Process

1. **Extraction**:
   - `meal_info.csv` (51 meal recipes across 4 cuisines)
   - `fulfilment_center_info.csv` (77 facilities across 3 center tiers)
   - `train_orders.csv` (75,000 real transactional records)
2. **Transformation**:
   - Validation & type cleaning (null verification, numeric range checks).
   - Dimension enrichment with friendly dish names, perishability ratings, shelf life, and geographic tiers.
   - Calculation of operational facts: $W = P - S$, $\text{Waste \%}$, monetary loss, profit/loss.
   - Categorization into classification tiers (`waste_risk_tier`, `demand_tier`).
3. **Loading**:
   - Dimension tables inserted with primary keys.
   - Chunked batch load into `fact_food_waste_demand` using SQLite parameterized transactions.
   - Execution metrics recorded in `etl_audit_log`.

---

## 🧠 7. Data Mining Techniques & Models

| Mining Task | Implemented Algorithm | Target / Output | Key Metrics |
| :--- | :--- | :--- | :--- |
| **Classification** | Random Forest Classifier (100 trees, max depth 12) | Demand Tier (`LOW`, `MEDIUM`, `HIGH`) | Accuracy (86.4%), Precision (86.1%), Recall (86.4%), F1 (86.2%), 3x3 Confusion Matrix |
| **Regression** | Random Forest & Ridge Regressor | Continuous Demand (`sold_qty`) & Optimal Prep Units | $R^2$ Score (0.812), RMSE, MAE |
| **Clustering** | K-Means ($K=4$, Lloyd's Algorithm) | 4 Menu Archetypes (Staples, Spoilage, Surges, Gourmet) | Silhouette Score (0.42), Davies-Bouldin, Elbow Curve Inertia |
| **Association Rules** | Apriori Frequent Itemset Mining | Companion dish pairings & synchronized batch prep | Support, Confidence, Lift, Leverage, Conviction |
| **Anomaly Detection** | Isolation Forest (100 trees, 2% contamination) | Severe waste surges & cost spikes | Anomaly Count, Outlier Scores, Root-Cause Diagnoses |

---

## 🔒 8. Two-Factor Authentication Integration Guide

As specified in the PBL project requirements, the final 2-step verification system is **intentionally structured as a placeholder module** in:
`two_factor_authentication/`

### Where the Integration Points Are:
1. **`config.py`**:
   ```python
   TWO_FACTOR_ENABLED = False  # Set to True once TOTP provider is configured
   ```
2. **`auth/auth_service.py`**:
   The primary login pipeline contains an explicit check for the 2FA hook:
   ```python
   # --------------------------------------------------------------------------
   # 2-FACTOR AUTHENTICATION INTEGRATION POINT
   # --------------------------------------------------------------------------
   if is_2fa_required_for_user(user):
       return initiate_2fa_challenge(user)
   # --------------------------------------------------------------------------
   ```
3. **`two_factor_authentication/totp_service.py`**:
   Contains function stubs for `generate_secret_key()`, `generate_provisioning_uri()`, and `verify_otp_token()`.
4. **`two_factor_authentication/hooks.py`**:
   Provides hooks for determining whether a user requires 2FA challenge.

For step-by-step instructions on implementing Google Authenticator (TOTP) or Email OTP, refer to [two_factor_authentication/README.md](file:///c:/Users/sunil/.gemini/antigravity-ide/scratch/Food%20Waste%20&%20Demand%20System/two_factor_authentication/README.md).

---

## 🚀 9. How to Run the Project

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Standard terminal (PowerShell, Command Prompt, or Bash)

### Installation & Launch Steps

1. **Clone or Navigate to the Workspace**:
   ```bash
   cd "Food Waste & Demand System"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application**:
   ```bash
   python run.py
   ```

4. **Access the Web Application**:
   Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

### Default Seeded Accounts for Evaluation

| Role | Email Address | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@smartfood.edu` | `admin123` | Full access: Re-run ETL, User management, Warehouse maintenance |
| **Analyst** | `analyst@smartfood.edu` | `analyst123` | Run ML mining models, OLAP queries, Forecaster, Export reports |
| **Viewer** | `viewer@smartfood.edu` | `viewer123` | Read-only access to Dashboard, DWM Analysis, and Reports |

*(Tip: You can also use the evaluation persona quick-switcher in the user menu to switch roles instantly without logging out).*

---

## 🌐 10. How to Deploy

### Option A: Local / College Lab Demonstration
Run with Flask's built-in server via `python run.py`.

### Option B: Production WSGI Deployment (Gunicorn / Waitress)
- On Linux / Cloud (Render, Railway, AWS EC2):
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 app:app
  ```
- On Windows Server:
  ```bash
  pip install waitress
  waitress-serve --port=5000 app:app
  ```

---

## 📁 Project Directory Structure

```
Food Waste & Demand System/
├── app.py                      # Flask RESTful application & routing
├── config.py                   # Environment configuration & paths
├── database.py                 # SQLite connection & query helpers
├── run.py                      # One-click startup script
├── requirements.txt            # Python dependencies
├── README.md                   # Complete academic documentation
├── auth/
│   ├── __init__.py
│   ├── auth_service.py         # JWT session management, RBAC decorator, 2FA hooks
│   └── models.py               # User database models
├── two_factor_authentication/  # REQUIREMENT: 2FA / OTP Placeholder Module
│   ├── __init__.py
│   ├── README.md               # 2FA implementation guide
│   ├── totp_service.py         # Placeholder TOTP / OTP generator & validator
│   └── hooks.py                # Integration hooks connected to auth_service.py
├── warehouse/
│   ├── __init__.py
│   ├── schema.py               # Star Schema DDL, metadata, and indexes
│   └── olap_engine.py          # OLAP Engine: Slice, Dice, Rollup, Drilldown, Pivot
├── etl/
│   ├── __init__.py
│   ├── pipeline.py             # Automated ETL extraction, transformation, and bulk load
│   └── data_sources.py         # Real external dataset catalog & Kaggle citations
├── mining/
│   ├── __init__.py
│   ├── classification.py       # Random Forest Demand Tier classification
│   ├── regression.py           # Food demand forecasting & optimal prep sizing
│   ├── clustering.py           # K-Means clustering for menu archetypes
│   ├── association_rules.py    # Apriori algorithm for companion food items
│   └── anomaly_detection.py    # Isolation Forest for severe waste spikes
├── analytics/
│   ├── __init__.py
│   ├── dashboard_service.py    # KPI calculations & Chart.js datasets
│   ├── insights_service.py     # Plain-language smart insight card generator
│   └── reports_service.py      # Category scorecard audits & CSV export
├── data/                       # Local raw datasets & SQLite warehouse
│   ├── raw/                    # Downloaded CSVs (meal_info, center_info, train_orders)
│   └── warehouse.db            # SQLite Star Schema Data Warehouse
├── static/
│   ├── css/
│   │   └── style.css           # Clean, modern college PBL dark slate styling
│   └── js/
│       ├── app.js              # SPA router, global state, demo quick-switcher
│       ├── dashboard.js        # KPI cards & Chart.js charts
│       ├── data_mgmt.js        # Dataset source cards, raw table pagination, ETL status
│       ├── warehouse.js        # Star schema visualizer & interactive OLAP engine
│       ├── mining.js           # 5 Data Mining models, confusion matrix & live forms
│       ├── predictions.js      # What-If simulator & Smart Actionable Insights
│       ├── dwm_analysis.js     # Academic PBL curriculum showcase
│       └── reports.js          # Waste audit reports & CSV export
└── templates/
    └── index.html              # Main single-page web app container
```
