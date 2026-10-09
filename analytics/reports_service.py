from database import execute_query

class ReportsService:
    """Service generating structured executive reports and audit scorecards."""

    @classmethod
    def get_executive_summary_report(cls):
        """Generate high-level waste reduction audit report."""
        category_audit_query = """
        SELECT 
            c.category_name,
            c.food_group,
            c.spoilage_sensitivity,
            COUNT(f.fact_id) as total_observations,
            SUM(f.prepared_qty) as prepared_units,
            SUM(f.sold_qty) as sold_units,
            SUM(f.waste_qty) as wasted_units,
            ROUND((CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100, 2) as waste_percentage,
            ROUND(SUM(f.waste_cost), 2) as waste_cost_dollars,
            ROUND(SUM(f.revenue), 2) as revenue_dollars,
            CASE 
                WHEN (CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100 > 14.0 THEN 'URGENT INTERVENTION'
                WHEN (CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100 > 10.0 THEN 'ATTENTION NEEDED'
                ELSE 'OPTIMAL EFFICIENCY'
            END as efficiency_rating
        FROM fact_food_waste_demand f
        JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY c.category_name, c.food_group, c.spoilage_sensitivity
        ORDER BY waste_percentage DESC;
        """
        category_rows = execute_query(category_audit_query)

        # Center ranking
        center_audit_query = """
        SELECT 
            fc.center_id,
            fc.center_name,
            fc.center_type,
            fc.op_area,
            SUM(f.waste_qty) as wasted_units,
            ROUND((CAST(SUM(f.waste_qty) AS REAL) / SUM(f.prepared_qty)) * 100, 2) as waste_percentage,
            ROUND(SUM(f.waste_cost), 2) as waste_cost_dollars
        FROM fact_food_waste_demand f
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        GROUP BY fc.center_id, fc.center_name, fc.center_type, fc.op_area
        ORDER BY waste_cost_dollars DESC
        LIMIT 10;
        """
        center_rows = execute_query(center_audit_query)

        # Total cost savings potential if waste % reduced by 25% (PBL value proposition)
        total_waste_cost = sum(r["waste_cost_dollars"] for r in category_rows)
        target_savings_25pct = round(total_waste_cost * 0.25, 2)

        return {
            "report_title": "Food Waste Reduction & Demand Optimization Audit",
            "benchmark_period": "26 Operational Weeks (Jan - Jun 2024)",
            "total_categories_audited": len(category_rows),
            "total_waste_cost": round(total_waste_cost, 2),
            "projected_savings_target": target_savings_25pct,
            "category_scorecard": category_rows,
            "top_waste_centers": center_rows
        }
