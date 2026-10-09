import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from database import execute_df

class FoodWasteAnomalyDetector:
    """
    Data Mining Anomaly Detection using Isolation Forest:
    Detects severe outliers and operational food-waste surges.
    Pinpoints center-dish records with abnormal financial loss or spoilage rates.
    """
    _cached_results = None

    @classmethod
    def train_and_detect(cls, contamination=0.02, force_retrain=False):
        if cls._cached_results is not None and not force_retrain and cls._cached_results.get("contamination") == contamination:
            return cls._cached_results

        query = """
        SELECT 
            f.fact_id,
            d.week_number,
            d.month_name,
            m.item_name,
            m.category,
            m.cuisine,
            fc.center_name,
            fc.center_type,
            f.prepared_qty,
            f.sold_qty,
            f.waste_qty,
            f.waste_percentage,
            f.waste_cost,
            f.base_price,
            f.discount_percent,
            f.emailer_for_promotion,
            f.homepage_featured
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        JOIN dim_date d ON f.date_id = d.date_id
        LIMIT 25000;
        """
        df = execute_df(query)

        features = ['waste_qty', 'waste_percentage', 'waste_cost', 'discount_percent']
        X = df[features].values

        # Isolation Forest Model
        iso = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            n_jobs=-1
        )
        preds = iso.fit_predict(X) # -1 for anomaly, 1 for normal
        scores = iso.decision_function(X) # lower score = more anomalous

        df['is_anomaly'] = preds == -1
        df['anomaly_score'] = scores

        anomaly_df = df[df['is_anomaly']].sort_values(by='waste_cost', ascending=False)
        total_records = len(df)
        total_anomalies = len(anomaly_df)

        # Highlight top 15 most severe anomalies with operational diagnostics
        top_anomalies = []
        for _, row in anomaly_df.head(15).iterrows():
            waste_cost = float(row['waste_cost'])
            waste_pct = float(row['waste_percentage'])
            sold = int(row['sold_qty'])
            prepared = int(row['prepared_qty'])
            cat = str(row['category'])
            promo = int(row['emailer_for_promotion']) or int(row['homepage_featured'])

            # Diagnostic heuristic for root cause
            if promo and waste_pct > 18.0:
                cause = "Failed Promotional Surge: Kitchen heavily over-prepared expecting spike that did not materialize."
            elif cat in ["Fish", "Seafood", "Salad"] and waste_pct > 20.0:
                cause = "Perishability Expiry: Fresh shelf-life exceeded before inventory turnover could occur."
            elif prepared > 2000 and sold < 1200:
                cause = "Forecasting Buffer Overshoot: Multi-shift over-batching in mega distribution kitchen."
            else:
                cause = "Abnormal Demand Collapse: Unanticipated local event or delivery disruption."

            top_anomalies.append({
                "fact_id": int(row['fact_id']),
                "week_number": int(row['week_number']),
                "month_name": str(row['month_name']),
                "item_name": str(row['item_name']),
                "category": cat,
                "cuisine": str(row['cuisine']),
                "center_name": str(row['center_name']),
                "center_type": str(row['center_type']),
                "prepared_qty": prepared,
                "sold_qty": sold,
                "waste_qty": int(row['waste_qty']),
                "waste_percentage": round(waste_pct, 1),
                "waste_cost": round(waste_cost, 2),
                "anomaly_score": round(float(row['anomaly_score']), 4),
                "root_cause_diagnosis": cause
            })

        cls._cached_results = {
            "algorithm": "Isolation Forest (100 Trees, Contamination = 2%)",
            "contamination": contamination,
            "total_records_analyzed": total_records,
            "anomalies_detected": total_anomalies,
            "anomaly_rate_pct": round((total_anomalies / total_records) * 100, 2),
            "score_threshold": round(float(np.percentile(scores, contamination * 100)), 4),
            "top_anomalies": top_anomalies,
            "interpretation": f"Isolation Forest partitioned data into normal vs anomalous clusters, isolating {total_anomalies} high-impact waste incidents that accounted for disproportionate financial spoilage loss."
        }
        return cls._cached_results
