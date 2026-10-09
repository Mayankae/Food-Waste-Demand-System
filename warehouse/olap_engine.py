from database import execute_query, execute_df

class OLAPEngine:
    """
    OLAP Analytical Query Engine supporting:
    - Slice: 1-dimensional filtering
    - Dice: Multi-dimensional sub-cube extraction
    - Roll-up: Aggregation up dimensional hierarchies
    - Drill-down: De-aggregation into fine granularities
    - Pivot: 2D cross-tabulation matrix calculation
    """

    @staticmethod
    def slice(dimension, value, limit=100):
        """
        Perform an OLAP Slice operation:
        Fix one dimension to a single coordinate and aggregate the remaining facts.
        """
        valid_dims = {
            "cuisine": ("f.meal_id = m.meal_id", "m.cuisine = ?", "dim_food_item m"),
            "category": ("f.category_id = c.category_id", "c.category_name = ?", "dim_category c"),
            "center_type": ("f.center_id = fc.center_id", "fc.center_type = ?", "dim_fulfillment_center fc"),
            "quarter": ("f.date_id = d.date_id", "d.quarter = ?", "dim_date d"),
            "season": ("f.date_id = d.date_id", "d.season = ?", "dim_date d"),
            "month_name": ("f.date_id = d.date_id", "d.month_name = ?", "dim_date d")
        }

        if dimension not in valid_dims:
            raise ValueError(f"Invalid slice dimension: {dimension}. Valid dimensions: {list(valid_dims.keys())}")

        join_cond, where_cond, join_table = valid_dims[dimension]

        query = f"""
        SELECT 
            m.category,
            m.cuisine,
            fc.center_type,
            d.month_name,
            COUNT(f.fact_id) as total_records,
            SUM(f.prepared_qty) as total_prepared,
            SUM(f.sold_qty) as total_sold,
            SUM(f.waste_qty) as total_waste,
            ROUND(AVG(f.waste_percentage), 2) as avg_waste_pct,
            ROUND(SUM(f.waste_cost), 2) as total_waste_cost,
            ROUND(SUM(f.revenue), 2) as total_revenue
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_category c ON f.category_id = c.category_id
        WHERE {where_cond}
        GROUP BY m.category, m.cuisine, fc.center_type, d.month_name
        ORDER BY total_waste DESC
        LIMIT ?;
        """
        rows = execute_query(query, [value, limit])
        return {
            "operation": "SLICE",
            "slice_dimension": dimension,
            "slice_value": value,
            "result_count": len(rows),
            "data": rows
        }

    @staticmethod
    def dice(filters, limit=100):
        """
        Perform an OLAP Dice operation:
        Define a sub-cube by specifying criteria across multiple dimensions.
        Example: filters = {"cuisine": "Italian", "center_type": "TYPE_A", "quarter": "Q1"}
        """
        where_clauses = []
        params = []

        if "cuisine" in filters and filters["cuisine"]:
            where_clauses.append("m.cuisine = ?")
            params.append(filters["cuisine"])

        if "category" in filters and filters["category"]:
            where_clauses.append("m.category = ?")
            params.append(filters["category"])

        if "center_type" in filters and filters["center_type"]:
            where_clauses.append("fc.center_type = ?")
            params.append(filters["center_type"])

        if "quarter" in filters and filters["quarter"]:
            where_clauses.append("d.quarter = ?")
            params.append(filters["quarter"])

        if "waste_risk" in filters and filters["waste_risk"]:
            where_clauses.append("f.waste_risk_tier = ?")
            params.append(filters["waste_risk"])

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        params.append(limit)

        query = f"""
        SELECT 
            f.fact_id,
            d.week_number,
            d.month_name,
            d.quarter,
            m.item_name,
            m.category,
            m.cuisine,
            fc.center_name,
            fc.center_type,
            f.prepared_qty,
            f.sold_qty,
            f.waste_qty,
            ROUND(f.waste_percentage, 2) as waste_pct,
            ROUND(f.waste_cost, 2) as waste_cost,
            ROUND(f.revenue, 2) as revenue,
            f.waste_risk_tier
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE {where_sql}
        ORDER BY f.waste_cost DESC
        LIMIT ?;
        """
        rows = execute_query(query, params)
        return {
            "operation": "DICE",
            "active_filters": filters,
            "result_count": len(rows),
            "data": rows
        }

    @staticmethod
    def rollup(hierarchy_level="month"):
        """
        Perform an OLAP Roll-up operation:
        Ascend temporal or product hierarchies to view higher-level aggregates.
        Options: 'week' -> 'month' -> 'quarter' -> 'year', or 'category' -> 'cuisine'
        """
        if hierarchy_level == "quarter":
            group_by = "d.year, d.quarter"
            select_cols = "d.year, d.quarter as time_dimension"
            order_by = "d.year, d.quarter"
        elif hierarchy_level == "month":
            group_by = "d.year, d.month_name, d.month_number"
            select_cols = "d.year, d.month_name as time_dimension"
            order_by = "d.year, d.month_number"
        elif hierarchy_level == "cuisine":
            group_by = "m.cuisine"
            select_cols = "m.cuisine as grouping_dimension"
            order_by = "total_waste DESC"
        elif hierarchy_level == "center_type":
            group_by = "fc.center_type"
            select_cols = "fc.center_type as grouping_dimension"
            order_by = "total_waste DESC"
        else: # default category
            group_by = "c.category_name, c.food_group"
            select_cols = "c.category_name as grouping_dimension, c.food_group"
            order_by = "total_waste DESC"

        query = f"""
        SELECT 
            {select_cols},
            COUNT(f.fact_id) as record_count,
            SUM(f.prepared_qty) as total_prepared,
            SUM(f.sold_qty) as total_sold,
            SUM(f.waste_qty) as total_waste,
            ROUND(AVG(f.waste_percentage), 2) as avg_waste_pct,
            ROUND(SUM(f.waste_cost), 2) as total_waste_cost,
            ROUND(SUM(f.revenue), 2) as total_revenue
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY {group_by}
        ORDER BY {order_by};
        """
        rows = execute_query(query)
        return {
            "operation": "ROLLUP",
            "hierarchy_level": hierarchy_level,
            "result_count": len(rows),
            "data": rows
        }

    @staticmethod
    def drilldown(parent_dimension, parent_value):
        """
        Perform an OLAP Drill-down operation:
        Navigate from a high-level summary down to low-level members.
        Example: Drill down from Category='Biryani' to individual Meal Items.
        """
        if parent_dimension == "category":
            query = """
            SELECT 
                m.meal_id,
                m.item_name,
                m.cuisine,
                m.perishability_tier,
                COUNT(f.fact_id) as center_weeks_recorded,
                SUM(f.prepared_qty) as total_prepared,
                SUM(f.sold_qty) as total_sold,
                SUM(f.waste_qty) as total_waste,
                ROUND(AVG(f.waste_percentage), 2) as avg_waste_pct,
                ROUND(SUM(f.waste_cost), 2) as total_waste_cost,
                ROUND(SUM(f.revenue), 2) as total_revenue
            FROM fact_food_waste_demand f
            JOIN dim_food_item m ON f.meal_id = m.meal_id
            WHERE m.category = ?
            GROUP BY m.meal_id, m.item_name, m.cuisine, m.perishability_tier
            ORDER BY total_waste DESC;
            """
            rows = execute_query(query, [parent_value])
        elif parent_dimension == "center_type":
            query = """
            SELECT 
                fc.center_id,
                fc.center_name,
                fc.city_code,
                fc.op_area,
                COUNT(f.fact_id) as total_records,
                SUM(f.prepared_qty) as total_prepared,
                SUM(f.sold_qty) as total_sold,
                SUM(f.waste_qty) as total_waste,
                ROUND(AVG(f.waste_percentage), 2) as avg_waste_pct,
                ROUND(SUM(f.waste_cost), 2) as total_waste_cost
            FROM fact_food_waste_demand f
            JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
            WHERE fc.center_type = ?
            GROUP BY fc.center_id, fc.center_name, fc.city_code, fc.op_area
            ORDER BY total_waste DESC
            LIMIT 25;
            """
            rows = execute_query(query, [parent_value])
        else:
            raise ValueError(f"Unsupported drilldown dimension: {parent_dimension}")

        return {
            "operation": "DRILLDOWN",
            "parent_dimension": parent_dimension,
            "parent_value": parent_value,
            "data": rows
        }

    @staticmethod
    def pivot(row_dim="category", col_dim="center_type", metric="waste_cost"):
        """
        Perform an OLAP Pivot (Cross-tabulation) operation:
        Transforms multi-dimensional metrics into a 2D matrix.
        Rows: e.g., Food Category
        Columns: e.g., Center Type (TYPE_A, TYPE_B, TYPE_C)
        Values: e.g., total_waste_cost ($) or waste_qty
        """
        metric_expr = {
            "waste_cost": "ROUND(SUM(f.waste_cost), 2)",
            "waste_qty": "SUM(f.waste_qty)",
            "sold_qty": "SUM(f.sold_qty)",
            "revenue": "ROUND(SUM(f.revenue), 2)",
            "waste_percentage": "ROUND(AVG(f.waste_percentage), 2)"
        }.get(metric, "ROUND(SUM(f.waste_cost), 2)")

        row_col = "m.category" if row_dim == "category" else "m.cuisine"
        col_col = "fc.center_type" if col_dim == "center_type" else "d.quarter"

        query = f"""
        SELECT 
            {row_col} as row_label,
            {col_col} as col_label,
            {metric_expr} as val
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        JOIN dim_date d ON f.date_id = d.date_id
        GROUP BY {row_col}, {col_col}
        ORDER BY {row_col}, {col_col};
        """
        rows = execute_query(query)

        # Build pivot matrix
        matrix = {}
        columns = sorted(list(set(r["col_label"] for r in rows)))
        for r in rows:
            row_k = r["row_label"]
            if row_k not in matrix:
                matrix[row_k] = {c: 0 for c in columns}
            matrix[row_k][r["col_label"]] = r["val"]

        pivot_table = []
        for row_k, vals in matrix.items():
            entry = {"label": row_k}
            entry.update(vals)
            # Row total
            entry["total"] = round(sum(v for v in vals.values() if isinstance(v, (int, float))), 2)
            pivot_table.append(entry)

        return {
            "operation": "PIVOT",
            "row_dimension": row_dim,
            "col_dimension": col_dim,
            "metric": metric,
            "columns": columns,
            "rows": pivot_table
        }
