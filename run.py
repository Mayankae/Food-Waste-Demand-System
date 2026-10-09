import os
import sys
from app import app
from etl.pipeline import ETLPipeline

def main():
    print("=" * 70)
    print("  SMART FOOD & WASTE INTELLIGENCE SYSTEM")
    print("  College PBL - Data Warehousing & Data Mining (DWM)")
    print("=" * 70)
    
    # Check warehouse status
    status = ETLPipeline.get_etl_status()
    print(f"[*] Warehouse Status: {status['warehouse_status']}")
    print(f"[*] Total Fact Records in Star Schema: {status['fact_records']:,}")
    print("[*] Two-Factor Authentication Module: PLACEHOLDER MODE (Configured)")
    print("[*] Default Test Accounts:")
    print("    - Admin:   admin@smartfood.edu   / admin123")
    print("    - Analyst: analyst@smartfood.edu / analyst123")
    print("    - Viewer:  viewer@smartfood.edu  / viewer123")
    print("=" * 70)
    print("  Server launching at: http://127.0.0.1:5000")
    print("=" * 70)

    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == "__main__":
    main()
