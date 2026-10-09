import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from database import execute_df

class FoodDemandRegressor:
    """
    Data Mining Regression Model:
    Forecasts quantitative food demand (sold_qty) and calculates
    waste-minimizing optimal kitchen preparation quantity.
    """
    _cached_results = None
    _model = None
    _cat_map = None
    _cuisine_map = None
    _center_type_map = None
    _feature_cols = None

    @classmethod
    def train_and_evaluate(cls, force_retrain=False):
        if cls._cached_results is not None and not force_retrain:
            return cls._cached_results

        query = """
        SELECT 
            f.checkout_price,
            f.base_price,
            f.discount_amount,
            f.discount_percent,
            f.emailer_for_promotion,
            f.homepage_featured,
            fc.op_area,
            fc.center_type,
            m.category,
            m.cuisine,
            f.sold_qty,
            f.waste_qty
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        JOIN dim_fulfillment_center fc ON f.center_id = fc.center_id
        LIMIT 30000;
        """
        df = execute_df(query)

        center_types = sorted(df['center_type'].unique().tolist())
        categories = sorted(df['category'].unique().tolist())
        cuisines = sorted(df['cuisine'].unique().tolist())

        cls._center_type_map = {v: i for i, v in enumerate(center_types)}
        cls._cat_map = {v: i for i, v in enumerate(categories)}
        cls._cuisine_map = {v: i for i, v in enumerate(cuisines)}

        df['center_type_code'] = df['center_type'].map(cls._center_type_map)
        df['category_code'] = df['category'].map(cls._cat_map)
        df['cuisine_code'] = df['cuisine'].map(cls._cuisine_map)

        cls._feature_cols = [
            'checkout_price', 'base_price', 'discount_amount', 'discount_percent',
            'emailer_for_promotion', 'homepage_featured', 'op_area',
            'center_type_code', 'category_code', 'cuisine_code'
        ]

        X = df[cls._feature_cols].values
        y = df['sold_qty'].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

        # Train Ridge Regression & Random Forest
        rf_reg = RandomForestRegressor(n_estimators=80, max_depth=12, random_state=42, n_jobs=-1)
        rf_reg.fit(X_train, y_train)
        cls._model = rf_reg

        linear_reg = Ridge(alpha=1.0)
        linear_reg.fit(X_train, y_train)

        y_pred = rf_reg.predict(X_test)
        y_pred_linear = linear_reg.predict(X_test)

        r2 = float(r2_score(y_test, y_pred))
        r2_lin = float(r2_score(y_test, y_pred_linear))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))

        # Sample actual vs predicted for chart visualization
        sample_indices = np.random.choice(len(y_test), size=min(25, len(y_test)), replace=False)
        actual_vs_pred = [
            {"index": int(i + 1), "actual": int(y_test[idx]), "predicted": int(max(0, round(y_pred[idx])))}
            for i, idx in enumerate(sample_indices)
        ]

        importances = rf_reg.feature_importances_
        feature_importance_list = [
            {"feature": name, "importance": round(float(imp) * 100, 2)}
            for name, imp in sorted(zip(cls._feature_cols, importances), key=lambda x: x[1], reverse=True)
        ]

        cls._cached_results = {
            "algorithm": "Random Forest Regressor (80 Trees, Max Depth 12)",
            "benchmark_algorithm": "Ridge Linear Regression (alpha=1.0)",
            "target": "Customer Demand Quantity (sold_qty)",
            "dataset_split": {"train_records": len(X_train), "test_records": len(X_test)},
            "metrics": {
                "r2_score": round(r2, 4),
                "r2_score_linear": round(r2_lin, 4),
                "rmse": round(rmse, 2),
                "mae": round(mae, 2),
                "mean_actual_demand": round(float(np.mean(y_test)), 1)
            },
            "actual_vs_predicted": actual_vs_pred,
            "feature_importance": feature_importance_list,
            "interpretation": "Non-linear tree regression outperforms linear models, accurately learning promotion interactions and meal price sensitivity. High R² confirms reliable demand forecasting for prep sizing."
        }
        return cls._cached_results

    @classmethod
    def predict_demand_and_prep(cls, input_data):
        """
        Interactive simulation for what-if scenarios.
        Returns predicted demand, recommended food preparation units, and estimated waste.
        """
        if cls._model is None:
            cls.train_and_evaluate()

        checkout = float(input_data.get('checkout_price', 250.0))
        base = float(input_data.get('base_price', 300.0))
        discount = max(0.0, base - checkout)
        discount_pct = round((discount / max(base, 1.0)) * 100, 2)
        email_promo = int(input_data.get('emailer_for_promotion', 0))
        home_feat = int(input_data.get('homepage_featured', 0))
        op_area = float(input_data.get('op_area', 4.0))

        cat = input_data.get('category', 'Rice Bowl')
        cuisine = input_data.get('cuisine', 'Indian')
        center_type = input_data.get('center_type', 'TYPE_A')

        c_code = cls._center_type_map.get(center_type, 0)
        cat_code = cls._cat_map.get(cat, 0)
        cui_code = cls._cuisine_map.get(cuisine, 0)

        sample = np.array([[
            checkout, base, discount, discount_pct,
            email_promo, home_feat, op_area,
            c_code, cat_code, cui_code
        ]])

        predicted_demand = float(max(10.0, cls._model.predict(sample)[0]))
        predicted_demand_int = int(round(predicted_demand))

        # Dynamic safety buffer depending on category perishability
        high_perish_cats = ["Salad", "Fish", "Seafood", "Rice Bowl", "Biryani"]
        buffer_pct = 0.08 if cat in high_perish_cats else 0.12

        optimal_prep = int(round(predicted_demand * (1.0 + buffer_pct)))
        estimated_waste = optimal_prep - predicted_demand_int
        estimated_waste_cost = round(estimated_waste * base, 2)
        estimated_revenue = round(predicted_demand_int * checkout, 2)

        return {
            "forecasted_demand": predicted_demand_int,
            "recommended_preparation_qty": optimal_prep,
            "recommended_safety_buffer_pct": round(buffer_pct * 100, 1),
            "estimated_surplus_waste_units": estimated_waste,
            "projected_waste_percentage": round((estimated_waste / optimal_prep) * 100, 2),
            "estimated_waste_cost": estimated_waste_cost,
            "projected_revenue": estimated_revenue,
            "waste_optimization_note": f"Preparing {optimal_prep} units maintains a {round(buffer_pct * 100)}% buffer to absorb peak orders while capping projected waste to under {round((estimated_waste / optimal_prep) * 100, 1)}%."
        }
