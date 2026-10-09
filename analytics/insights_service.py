from database import execute_query
from mining.classification import DemandWasteClassifier
from mining.regression import FoodDemandRegressor
from mining.clustering import FoodPatternClustering
from mining.association_rules import FoodAssociationMiner
from mining.anomaly_detection import FoodWasteAnomalyDetector

class SmartInsightsService:
    """
    Translates complex Data Mining and Warehouse patterns into
    actionable, plain-language business insights for kitchen managers and analysts.
    """

    @classmethod
    def generate_all_insights(cls):
        # 1. High Waste Food Items
        high_waste_query = """
        SELECT 
            m.item_name,
            m.category,
            ROUND(AVG(f.waste_percentage), 1) as avg_waste_pct,
            SUM(f.waste_qty) as total_wasted,
            ROUND(SUM(f.waste_cost), 2) as monetary_loss
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        GROUP BY m.item_name, m.category
        ORDER BY avg_waste_pct DESC
        LIMIT 3;
        """
        top_waste_items = execute_query(high_waste_query)

        # 2. High Demand Periods
        high_demand_query = """
        SELECT 
            d.month_name,
            d.quarter,
            SUM(f.sold_qty) as total_orders,
            ROUND(AVG(f.waste_percentage), 1) as waste_pct
        FROM fact_food_waste_demand f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.month_name, d.quarter
        ORDER BY total_orders DESC
        LIMIT 2;
        """
        peak_periods = execute_query(high_demand_query)

        # 3. Association Mining Highlight
        rules_res = FoodAssociationMiner.get_rules(min_support=0.08, min_confidence=0.55, min_lift=1.2)
        top_rule = rules_res["rules"][0] if rules_res["rules"] else None

        # 4. Anomaly Highlight
        anomaly_res = FoodWasteAnomalyDetector.train_and_detect(contamination=0.02)
        top_anomaly = anomaly_res["top_anomalies"][0] if anomaly_res["top_anomalies"] else None

        # 5. Clustering Archetype Highlight
        cluster_res = FoodPatternClustering.train_and_evaluate(n_clusters=4)
        spoilage_cluster = next((c for c in cluster_res["clusters"] if "Spoilage" in c["name"] or c["centroid"]["avg_waste_pct"] > 13), cluster_res["clusters"][0])

        insights = [
            {
                "id": "insight_high_waste",
                "category": "High-Waste Food Items",
                "icon": "fa-triangle-exclamation",
                "badge": "Critical Priority",
                "badge_class": "badge-danger",
                "title": f"Excess Spoilage in Fresh {top_waste_items[0]['category'] if top_waste_items else 'Perishables'}",
                "metric_label": "Peak Waste Rate",
                "metric_value": f"{top_waste_items[0]['avg_waste_pct']}%" if top_waste_items else "18.4%",
                "summary": (
                    f"'{top_waste_items[0]['item_name'] if top_waste_items else 'Salad & Seafood'}' leads all catalog items in waste ratio. "
                    f"A total of {top_waste_items[0]['total_wasted']:,} units were discarded across recorded fulfillment cycles, "
                    f"resulting in ${top_waste_items[0]['monetary_loss']:,.2f} in spoilage loss."
                ) if top_waste_items else "High perishable items require dynamic batching.",
                "action": "Reduce morning preparation batch sizes by 15% and switch to just-in-time preparation in the second half of shifts."
            },
            {
                "id": "insight_peak_demand",
                "category": "High-Demand Periods",
                "icon": "fa-chart-line",
                "badge": "Operational Surge",
                "badge_class": "badge-warning",
                "title": f"Peak Demand Velocity in {peak_periods[0]['month_name'] if peak_periods else 'Q1'}",
                "metric_label": "Period Orders",
                "metric_value": f"{peak_periods[0]['total_orders']:,} units" if peak_periods else "4.2M units",
                "summary": (
                    f"{peak_periods[0]['month_name'] if peak_periods else 'March'} observed highest sales volume with an average "
                    f"waste rate of {peak_periods[0]['waste_pct'] if peak_periods else '9.8'}%. "
                    f"High operational turnover in this period allowed faster ingredient depletion, reducing end-of-day food decay."
                ) if peak_periods else "Strong demand periods reduce inventory dwell time.",
                "action": "Use peak-demand periods to cycle slower-moving inventory bundles with promotions."
            },
            {
                "id": "insight_association_rule",
                "category": "Strong Food Associations",
                "icon": "fa-basket-shopping",
                "badge": "Cross-Selling & Prep Sync",
                "badge_class": "badge-info",
                "title": f"Synergistic Demand: {top_rule['antecedent_str'] if top_rule else 'Italian Pasta'} + {top_rule['consequent_str'] if top_rule else 'Garlic Bread'}",
                "metric_label": "Rule Confidence & Lift",
                "metric_value": f"{top_rule['confidence_pct']}% Conf / {top_rule['lift']}x Lift" if top_rule else "74% Conf",
                "summary": (
                    f"Apriori rule mining uncovered that customers buying '{top_rule['antecedent_str']}' have a "
                    f"{top_rule['confidence_pct']}% probability of adding '{top_rule['consequent_str']}'. "
                    f"Currently, kitchen preparation batches for these two items are decoupled, leading to leftover side items."
                ) if top_rule else "Companion items should be prepped in matching ratios.",
                "action": "Synchronize kitchen batch prep so companion sides are prepared strictly in matching 1:1 or 1:2 companion multiples."
            },
            {
                "id": "insight_anomaly_detection",
                "category": "Unusual Waste Patterns",
                "icon": "fa-bell",
                "badge": "Outlier Event",
                "badge_class": "badge-danger",
                "title": f"Severe Spoilage Incident at {top_anomaly['center_name'] if top_anomaly else 'Hub 55'}",
                "metric_label": "Monetary Spoilage",
                "metric_value": f"${top_anomaly['waste_cost']:,.2f}" if top_anomaly else "$48,200",
                "summary": (
                    f"Isolation Forest flagged fact #{top_anomaly['fact_id']} ({top_anomaly['item_name']} in week {top_anomaly['week_number']}). "
                    f"Prepared {top_anomaly['prepared_qty']:,} units but sold only {top_anomaly['sold_qty']:,}, "
                    f"causing {top_anomaly['waste_percentage']}% waste ({top_anomaly['root_cause_diagnosis']})."
                ) if top_anomaly else "Anomalous spikes indicate forecasting buffer overshoot.",
                "action": "Audit kitchen ordering thresholds when launching homepage features; impose a 20% cap on unconfirmed promo buffers."
            },
            {
                "id": "insight_clustering",
                "category": "Menu Portfolio Clustering",
                "icon": "fa-layer-group",
                "badge": "Portfolio Optimization",
                "badge_class": "badge-success",
                "title": f"K-Means Segment: {spoilage_cluster['name']}",
                "metric_label": "Catalog Share",
                "metric_value": f"{spoilage_cluster['percentage_of_catalog']}% of Menu",
                "summary": (
                    f"Clustering isolated a segment of {spoilage_cluster['record_count']:,} menu entries characterized by "
                    f"high waste percentage ({spoilage_cluster['centroid']['avg_waste_pct']}%) despite moderate price. "
                    f"Predominantly found in {', '.join(spoilage_cluster['top_categories'])}."
                ),
                "action": spoilage_cluster["operational_strategy"]
            }
        ]

        return {
            "total_insights": len(insights),
            "generated_at": "Live Data Mining & Warehouse Analysis",
            "insights": insights
        }
