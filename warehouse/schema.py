import sqlite3
from database import get_db_connection

def create_warehouse_schema():
    """
    Create the complete Star Schema tables, indexes, and audit logs
    for the Smart Food & Waste Intelligence Warehouse.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # -------------------------------------------------------------
    # 1. DIMENSION TABLE: dim_date
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_date (
        date_id INTEGER PRIMARY KEY,           -- e.g., 202401 to 202426
        week_number INTEGER NOT NULL,          -- Week in cycle (1 to 26)
        calendar_date TEXT NOT NULL,           -- Representative start date (YYYY-MM-DD)
        month_name TEXT NOT NULL,              -- January, February, etc.
        month_number INTEGER NOT NULL,         -- 1 to 12
        quarter TEXT NOT NULL,                 -- Q1, Q2, Q3, Q4
        year INTEGER NOT NULL,                 -- 2024
        is_weekend_peak INTEGER DEFAULT 0,     -- 1 if high weekend demand period
        season TEXT NOT NULL                   -- Winter, Spring, Summer, Autumn
    );
    """)

    # -------------------------------------------------------------
    # 2. DIMENSION TABLE: dim_food_item
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_food_item (
        meal_id INTEGER PRIMARY KEY,           -- Meal identifier from dataset
        item_name TEXT NOT NULL,               -- Descriptive item name
        category TEXT NOT NULL,                -- Beverages, Rice Bowl, Pasta, Biryani, etc.
        cuisine TEXT NOT NULL,                 -- Thai, Indian, Italian, Continental
        perishability_tier TEXT NOT NULL,      -- High, Medium, Low
        shelf_life_days INTEGER NOT NULL,      -- Shelf life in days (1, 2, 3, 7, 30)
        storage_type TEXT NOT NULL             -- Cold Storage, Chilled Prep, Ambient
    );
    """)

    # -------------------------------------------------------------
    # 3. DIMENSION TABLE: dim_fulfillment_center
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_fulfillment_center (
        center_id INTEGER PRIMARY KEY,         -- Center identifier
        center_name TEXT NOT NULL,             -- Friendly center name
        city_code INTEGER NOT NULL,            -- Anonymized city code
        region_code INTEGER NOT NULL,          -- Region code
        center_type TEXT NOT NULL,             -- TYPE_A, TYPE_B, TYPE_C
        op_area REAL NOT NULL,                 -- Operational area in sq km
        capacity_tier TEXT NOT NULL            -- Mega Distribution, Urban Kitchen, Regional Depot
    );
    """)

    # -------------------------------------------------------------
    # 4. DIMENSION TABLE: dim_category
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_category (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        food_group TEXT NOT NULL,              -- Mains, Starters, Beverages, Desserts
        spoilage_sensitivity TEXT NOT NULL     -- High, Moderate, Low
    );
    """)

    # -------------------------------------------------------------
    # 5. FACT TABLE: fact_food_waste_demand (Core Fact Table)
    # Grain: 1 record per fulfillment center, per meal item, per week
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_food_waste_demand (
        fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_record_id INTEGER NOT NULL,   -- Original transaction ID from Kaggle dataset
        date_id INTEGER NOT NULL,              -- FK to dim_date
        meal_id INTEGER NOT NULL,              -- FK to dim_food_item
        center_id INTEGER NOT NULL,            -- FK to dim_fulfillment_center
        category_id INTEGER NOT NULL,          -- FK to dim_category
        
        -- Price & Promotion measures
        checkout_price REAL NOT NULL,          -- Selling price to customer ($)
        base_price REAL NOT NULL,              -- Base list price ($)
        discount_amount REAL NOT NULL,         -- base_price - checkout_price ($)
        discount_percent REAL NOT NULL,        -- (discount / base_price) * 100
        emailer_for_promotion INTEGER DEFAULT 0,-- 1 if promoted via email
        homepage_featured INTEGER DEFAULT 0,    -- 1 if featured on homepage
        
        -- Operational & Waste measures (Additive Facts)
        sold_qty INTEGER NOT NULL,             -- Actual demand / units ordered
        prepared_qty INTEGER NOT NULL,         -- Units prepared / inventory stocked
        waste_qty INTEGER NOT NULL,            -- Unsold / spoiled units (prepared - sold)
        waste_percentage REAL NOT NULL,        -- (waste_qty / prepared_qty) * 100
        waste_cost REAL NOT NULL,              -- Monetary loss ($) = waste_qty * base_price
        revenue REAL NOT NULL,                 -- Revenue generated ($) = sold_qty * checkout_price
        profit_loss REAL NOT NULL,             -- Net margin ($) = revenue - (prepared_qty * cost)
        
        -- Classification Tiers (Derived for fast query & Mining)
        waste_risk_tier TEXT NOT NULL,         -- 'LOW' (<8%), 'MEDIUM' (8-16%), 'HIGH' (>16%)
        demand_tier TEXT NOT NULL,             -- 'LOW' (<100), 'MEDIUM' (100-350), 'HIGH' (>350)
        
        FOREIGN KEY (date_id) REFERENCES dim_date(date_id),
        FOREIGN KEY (meal_id) REFERENCES dim_food_item(meal_id),
        FOREIGN KEY (center_id) REFERENCES dim_fulfillment_center(center_id),
        FOREIGN KEY (category_id) REFERENCES dim_category(category_id)
    );
    """)

    # -------------------------------------------------------------
    # 6. SYSTEM TABLES: users and etl_audit_log
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,                    -- Admin, Analyst, Viewer
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS etl_audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        step_name TEXT NOT NULL,
        status TEXT NOT NULL,                  -- SUCCESS, RUNNING, FAILED
        records_processed INTEGER DEFAULT 0,
        execution_time_sec REAL DEFAULT 0.0,
        details TEXT
    );
    """)

    # -------------------------------------------------------------
    # 7. DATASETS CATALOG TABLE: datasets_catalog
    # Manages both built-in external benchmarks and user uploads
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets_catalog (
        dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source_type TEXT NOT NULL,             -- 'EXTERNAL_BENCHMARK' or 'USER_UPLOAD'
        provider_source TEXT NOT NULL,         -- Source provider / origin
        source_url TEXT,
        file_path TEXT,
        record_count INTEGER NOT NULL,
        column_list TEXT NOT NULL,
        file_size_kb REAL DEFAULT 0.0,
        import_date TEXT NOT NULL,
        processing_status TEXT NOT NULL,       -- 'PROCESSED_IN_WAREHOUSE', 'READY_FOR_ETL', 'ARCHIVED'
        is_deletable INTEGER DEFAULT 0
    );
    """)

    # -------------------------------------------------------------
    # 7. PERFORMANCE INDEXES (Star Schema Optimization)
    # -------------------------------------------------------------
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_food_waste_demand(date_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_meal ON fact_food_waste_demand(meal_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_center ON fact_food_waste_demand(center_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_category ON fact_food_waste_demand(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_waste_tier ON fact_food_waste_demand(waste_risk_tier);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_demand_tier ON fact_food_waste_demand(demand_tier);")

    conn.commit()
    conn.close()
    return True

def get_star_schema_metadata():
    """Return dictionary describing the Star Schema for DWM Analysis and schema visualizations."""
    return {
        "fact_table": {
            "name": "fact_food_waste_demand",
            "grain": "1 record per Fulfillment Center, per Meal Item, per Calendar Week",
            "type": "Transaction Fact Table with Additive Measures",
            "primary_key": "fact_id",
            "foreign_keys": [
                {"column": "date_id", "references": "dim_date.date_id"},
                {"column": "meal_id", "references": "dim_food_item.meal_id"},
                {"column": "center_id", "references": "dim_fulfillment_center.center_id"},
                {"column": "category_id", "references": "dim_category.category_id"}
            ],
            "measures": [
                {"name": "prepared_qty", "type": "INTEGER", "description": "Total units prepared / stocked in kitchen"},
                {"name": "sold_qty", "type": "INTEGER", "description": "Actual units purchased by customers (num_orders)"},
                {"name": "waste_qty", "type": "INTEGER", "description": "Unconsumed / spoiled units (prepared - sold)"},
                {"name": "waste_percentage", "type": "REAL", "description": "Percentage ratio of waste to preparation"},
                {"name": "waste_cost", "type": "REAL", "description": "Financial loss due to wasted food ($)"},
                {"name": "revenue", "type": "REAL", "description": "Gross sales revenue earned ($)"},
                {"name": "profit_loss", "type": "REAL", "description": "Net contribution after inventory preparation cost ($)"},
                {"name": "checkout_price", "type": "REAL", "description": "Final price after promotions ($)"},
                {"name": "discount_amount", "type": "REAL", "description": "Discount given from base list price ($)"}
            ]
        },
        "dimension_tables": [
            {
                "name": "dim_date",
                "primary_key": "date_id",
                "role": "Temporal dimension supporting Roll-up and Drill-down across Time hierarchies",
                "hierarchy": "Week -> Month -> Quarter -> Year",
                "columns": ["date_id", "week_number", "calendar_date", "month_name", "quarter", "year", "is_weekend_peak", "season"]
            },
            {
                "name": "dim_food_item",
                "primary_key": "meal_id",
                "role": "Product dimension capturing food characteristics, perishability, and cuisine",
                "hierarchy": "Meal Item -> Category -> Cuisine",
                "columns": ["meal_id", "item_name", "category", "cuisine", "perishability_tier", "shelf_life_days", "storage_type"]
            },
            {
                "name": "dim_fulfillment_center",
                "primary_key": "center_id",
                "role": "Location and facility dimension capturing kitchen capacity and geographical area",
                "hierarchy": "Center ID -> Center Type -> City Code -> Region Code",
                "columns": ["center_id", "center_name", "city_code", "region_code", "center_type", "op_area", "capacity_tier"]
            },
            {
                "name": "dim_category",
                "primary_key": "category_id",
                "role": "Categorical food grouping dimension for menu portfolio planning",
                "hierarchy": "Category -> Food Group",
                "columns": ["category_id", "category_name", "food_group", "spoilage_sensitivity"]
            }
        ]
    }
