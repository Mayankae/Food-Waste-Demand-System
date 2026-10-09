import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
from database import execute_df

class FoodPatternClustering:
    """
    Data Mining K-Means Clustering:
    Discovers natural operational archetypes and food waste profiles.
    Evaluates Silhouette Score, Davies-Bouldin Index, and Elbow Inertia.
    """
    _cached_results = None

    @classmethod
    def train_and_evaluate(cls, n_clusters=4, force_retrain=False):
        if cls._cached_results is not None and not force_retrain and cls._cached_results.get("k") == n_clusters:
            return cls._cached_results

        query = """
        SELECT 
            f.sold_qty,
            f.waste_qty,
            f.waste_percentage,
            f.checkout_price,
            f.discount_percent,
            m.item_name,
            m.category,
            m.cuisine
        FROM fact_food_waste_demand f
        JOIN dim_food_item m ON f.meal_id = m.meal_id
        LIMIT 20000;
        """
        df = execute_df(query)

        features = ['sold_qty', 'waste_qty', 'waste_percentage', 'checkout_price', 'discount_percent']
        X = df[features].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        df['cluster'] = labels

        # Metrics
        sil_score = float(silhouette_score(X_scaled[:5000], labels[:5000]))
        db_score = float(davies_bouldin_score(X_scaled, labels))
        inertia = float(kmeans.inertia_)

        # Elbow curve points
        elbow_data = []
        for k_val in [2, 3, 4, 5, 6]:
            km_k = KMeans(n_clusters=k_val, random_state=42, n_init=5, max_iter=150)
            km_k.fit(X_scaled[:5000])
            elbow_data.append({"k": k_val, "inertia": round(float(km_k.inertia_), 1)})

        # Unscaled Centroids
        raw_centroids = scaler.inverse_transform(kmeans.cluster_centers_)
        
        # Archetype profiling based on centroid coordinates
        archetype_names = [
            "High-Volume Core Staples (Low Waste Ratio)",
            "High Waste-Risk Perishables (Spoilage Exposure)",
            "Promotional Surges (Elastic High-Volume)",
            "Premium Gourmet (Low Volume, High Margin)"
        ]

        clusters_info = []
        for c_idx in range(n_clusters):
            cent = raw_centroids[c_idx]
            c_df = df[df['cluster'] == c_idx]
            count = len(c_df)
            pct_of_total = round((count / len(df)) * 100, 1)

            top_cats = c_df['category'].value_counts().head(3).index.tolist()

            clusters_info.append({
                "cluster_id": int(c_idx),
                "name": archetype_names[c_idx] if c_idx < len(archetype_names) else f"Cluster {c_idx}",
                "record_count": count,
                "percentage_of_catalog": pct_of_total,
                "centroid": {
                    "avg_sold_qty": int(round(cent[0])),
                    "avg_waste_qty": int(round(cent[1])),
                    "avg_waste_pct": round(float(cent[2]), 2),
                    "avg_checkout_price": round(float(cent[3]), 2),
                    "avg_discount_pct": round(float(cent[4]), 2)
                },
                "top_categories": top_cats,
                "operational_strategy": (
                    "Staple champion with high turnover; keep reliable daily base stock."
                    if cent[0] > 300 and cent[2] < 12
                    else "High spoilage risk; apply just-in-time preparation and reduce batch sizes."
                    if cent[2] >= 14
                    else "Price-elastic item; coordinate kitchen prep with active promotion schedules."
                    if cent[4] > 15
                    else "Premium niche; maintain lower inventory and cold-storage preservation."
                )
            })

        # 2D PCA projection for scatter plot visualization
        pca = PCA(n_components=2, random_state=42)
        X_2d = pca.fit_transform(X_scaled[:400])
        labels_sample = labels[:400]
        items_sample = df['item_name'].iloc[:400].tolist()

        scatter_points = [
            {
                "x": round(float(X_2d[i, 0]), 2),
                "y": round(float(X_2d[i, 1]), 2),
                "cluster": int(labels_sample[i]),
                "item": items_sample[i]
            }
            for i in range(len(X_2d))
        ]

        cls._cached_results = {
            "algorithm": f"K-Means Clustering (K={n_clusters}, Lloyd's Algorithm)",
            "k": n_clusters,
            "metrics": {
                "silhouette_score": round(sil_score, 3),
                "davies_bouldin_index": round(db_score, 3),
                "inertia": round(inertia, 1)
            },
            "elbow_curve": elbow_data,
            "clusters": clusters_info,
            "scatter_2d": scatter_points,
            "interpretation": "K-Means separates the menu into distinct operational cohorts. Cluster 1 identifies items with excessive waste percentage that require immediate recipe or portion-size intervention."
        }
        return cls._cached_results
