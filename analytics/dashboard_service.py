from database import execute_query

class DashboardService:
    """Service providing aggregate KPIs, trends, and charts for executive dashboard."""

    @classmethod
    def get_kpis(cls):
        """Calculate high-level summary KPIs from warehouse fact table."""
        query = """
        SELECT 
            COUNT(fact_id) as total_records,
            SUM(prepared_qty) as total_prepared,
            SUM(sold_qty) as total_sold,
            SUM(waste_qty) as total_waste,
            ROUND((CAST(SUM(waste_qty) AS REAL) / SUM(prepared_qty)) * 100, 2) as overall_waste_pct,
            ROUND(SUM(waste_cost), 2) as total_waste_cost,
            ROUND(SUM(revenue), 2) as total_revenue,
            ROUND(SUM(profit_loss), 2) as total_profit_loss
        FROM fact_food_waste_demand;
        """
        kpi_rows = execute_query(query)
        base = kpi_rows[0] if kpi_rows else {}

        # Add facility and menu counts
        centers_count = execute_query("SELECT COUNT(*) as cnt FROM dim_fulfillment_center;")[0]["cnt"]
        items_count = execute_query("SELECT COUNT(*) as cnt FROM dim_food_item;")[0]["cnt"]

        return {
            "total_records": base.get("total_records", 0),
            "total_food_prepared": base.get("total_prepared", 0),
            "total_food_sold": base.get("total_sold", 0),
            "total_food_wasted": base.get("total_waste", 0),
            "overall_waste_percentage": base.get("overall_waste_pct", 0.0),
            "total_waste_cost": base.get("total_waste_cost", 0.0),
            "total_revenue": base.get("total_revenue", 0.0),
            "total_profit_loss": base.get("total_profit_loss", 0.0),
            "active_fulfillment_centers": centers_count,
            "monitored_menu_items": items_count
        }

    @classmethod
    def get_charts_data(cls):
        """Provide structured datasets for Chart.js dashboard visualizers."""
        # 1. Monthly Demand vs Waste Timeline
        timeline_query = """
        SELECT 
            d.month_name,
            d.month_number,
            SUM(f.sold_qty) as demand_sold,
            SUM(f.prepared_qty) as food_prepared,
            SUM(f.waste_qty) as food_wasted,
            ROUND(AVG(f.waste_percentage), 2) as waste_pct
        FROM fact_food_waste_demand f
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY d.month_name, d.month_number
        ORDER BY d.month_number ASC;
        """
        timeline_rows = execute_query(timeline_query)

        # 2. Top 8 Most Wasted Food Items (by total waste quantity and cost)
        top_wasted_query = """
        SELECT 
            m.item_name,
            m.category,
            m.cuisine,
            SUM(f.waste_qty) as total_waste_units,
            ROUND(SUM(f.waste_cost), 2) as total_waste_cost,
            ROUND(AVG(f.waste_percentage), 2) as avg_waste_pct
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        GROUP BY m.item_name, m.category, m.cuisine
        ORDER BY total_waste_units DESC
        LIMIT 8;
        """
        top_wasted_rows = execute_query(top_wasted_query)

        # 3. Waste by Cuisine
        cuisine_query = """
        SELECT 
            m.cuisine,
            SUM(f.prepared_qty) as prepared,
            SUM(f.sold_qty) as sold,
            SUM(f.waste_qty) as waste,
            ROUND((CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100, 2) as waste_pct,
            ROUND(SUM(f.waste_cost), 2) as cost
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        GROUP BY m.cuisine
        ORDER BY waste DESC;
        """
        cuisine_rows = execute_query(cuisine_query)

        # 4. Center Type Distribution
        center_query = """
        SELECT 
            fc.center_type,
            COUNT(DISTINCT fc.center_id) as center_count,
            SUM(f.sold_qty) as sold,
            SUM(f.waste_qty) as waste,
            ROUND((CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100, 2) as waste_pct
        FROM fact_food_waste_demand f
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        GROUP BY fc.center_type
        ORDER BY fc.center_type ASC;
        """
        center_rows = execute_query(center_query)

        # 5. Waste Risk Tier Breakdown
        tier_query = """
        SELECT 
            waste_risk_tier,
            COUNT(fact_id) as record_count,
            ROUND((CAST(COUNT(fact_id) AS REAL) / (SELECT COUNT(*) FROM fact_food_waste_demand)) * 100, 1) as percentage
        FROM fact_food_waste_demand
        GROUP BY waste_risk_tier;
        """
        tier_rows = execute_query(tier_query)

        return {
            "monthly_timeline": timeline_rows,
            "top_wasted_items": top_wasted_rows,
            "cuisine_breakdown": cuisine_rows,
            "center_performance": center_rows,
            "waste_risk_tiers": tier_rows
        }
