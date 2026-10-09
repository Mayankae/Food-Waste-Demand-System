import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-food-waste-intelligence-dwm-key-2024")
    
    # Database and Data directories
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
    WAREHOUSE_DB_PATH = os.path.join(DATA_DIR, "warehouse.db")
    
    # Raw dataset paths
    MEAL_INFO_PATH = os.path.join(RAW_DATA_DIR, "meal_info.csv")
    FULFILMENT_CENTER_PATH = os.path.join(RAW_DATA_DIR, "fulfilment_center_info.csv")
    TRAIN_ORDERS_PATH = os.path.join(RAW_DATA_DIR, "train_orders.csv")
    
    # Real dataset remote sources
    REMOTE_MEAL_INFO_URL = "https://raw.githubusercontent.com/devarti19/Food-Demand-Forecasting/master/meal_info.csv"
    REMOTE_CENTER_INFO_URL = "https://raw.githubusercontent.com/devarti19/Food-Demand-Forecasting/master/fulfilment_center_info.csv"
    REMOTE_TRAIN_ORDERS_URL = "https://raw.githubusercontent.com/devarti19/Food-Demand-Forecasting/master/train.csv"
    
    # Target ETL record count (75,000 real records)
    ETL_TARGET_RECORD_COUNT = 75000
    
    # Two-Factor / 2-Step OTP Authentication Flag
    TWO_FACTOR_ENABLED = True
