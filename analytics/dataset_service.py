import os
import datetime
import pandas as pd
from config import Config
from database import execute_query, execute_dml

class DatasetService:
    """Service managing external baseline benchmarks and user-uploaded datasets."""

    @classmethod
    def ensure_uploads_dir(cls):
        os.makedirs(Config.UPLOADS_DIR, exist_ok=True)

    @classmethod
    def ensure_table(cls):
        cls.ensure_uploads_dir()
        try:
            from warehouse.schema import create_warehouse_schema
            from etl.pipeline import ETLPipeline
            from database import get_db_connection
            create_warehouse_schema()
            conn = get_db_connection()
            cursor = conn.cursor()
            ETLPipeline.seed_datasets_catalog(cursor)
            conn.commit()
            conn.close()
        except Exception as e:
            print("Notice ensuring datasets_catalog:", e)

    @classmethod
    def list_datasets(cls):
        """Retrieve all datasets with metadata from datasets_catalog."""
        cls.ensure_table()
        query = """
        SELECT 
            dataset_id,
            name,
            source_type,
            provider_source,
            source_url,
            file_path,
            record_count,
            column_list,
            file_size_kb,
            import_date,
            processing_status,
            is_deletable
        FROM datasets_catalog
        ORDER BY is_deletable ASC, dataset_id ASC;
        """
        rows = execute_query(query)
        
        # Enrich with column array
        results = []
        for r in rows:
            cols = [c.strip() for c in (r.get("column_list") or "").split(",") if c.strip()]
            results.append({
                "dataset_id": r["dataset_id"],
                "name": r["name"],
                "source_type": r["source_type"], # 'EXTERNAL_BENCHMARK' or 'USER_UPLOAD'
                "provider_source": r["provider_source"],
                "source_url": r["source_url"],
                "record_count": r["record_count"],
                "columns": cols,
                "column_count": len(cols),
                "file_size_kb": r["file_size_kb"],
                "import_date": r["import_date"],
                "processing_status": r["processing_status"],
                "is_deletable": bool(r["is_deletable"])
            })
        return results

    @classmethod
    def upload_dataset(cls, file_storage, custom_name=None):
        """
        Import and register a new dataset file (CSV/Excel).
        Extracts row count, column list, and saves to data/uploads/.
        """
        cls.ensure_uploads_dir()
        filename = file_storage.filename
        if not filename:
            raise ValueError("No file uploaded.")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise ValueError("Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.")

        dataset_name = (custom_name or os.path.splitext(filename)[0]).strip()
        save_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        save_path = os.path.join(Config.UPLOADS_DIR, save_filename)
        file_storage.save(save_path)

        # Parse file metadata using pandas
        try:
            if ext == ".csv":
                df = pd.read_csv(save_path, nrows=500000)
            else:
                df = pd.read_excel(save_path, nrows=500000)
            
            record_count = len(df)
            columns = list(df.columns.astype(str))
            col_str = ", ".join(columns[:25]) # store up to 25 primary columns
            file_size_kb = round(os.path.getsize(save_path) / 1024, 2)
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise ValueError(f"Failed to parse uploaded dataset: {str(e)}")

        import_date = datetime.date.today().strftime("%Y-%m-%d")

        dataset_id = execute_dml("""
            INSERT INTO datasets_catalog (
                name, source_type, provider_source, source_url, file_path,
                record_count, column_list, file_size_kb, import_date,
                processing_status, is_deletable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            dataset_name,
            "USER_UPLOAD",
            "User Imported File",
            "",
            save_path,
            record_count,
            col_str,
            file_size_kb,
            import_date,
            "READY_FOR_ETL",
            1
        ])

        return {
            "dataset_id": dataset_id,
            "name": dataset_name,
            "source_type": "USER_UPLOAD",
            "record_count": record_count,
            "column_count": len(columns),
            "columns": columns[:15],
            "file_size_kb": file_size_kb,
            "import_date": import_date,
            "processing_status": "READY_FOR_ETL",
            "is_deletable": 1
        }

    @classmethod
    def delete_dataset(cls, dataset_id):
        """
        Delete a user-uploaded dataset.
        Prevents deletion of baseline external benchmarks.
        """
        rows = execute_query("SELECT * FROM datasets_catalog WHERE dataset_id = ?;", [dataset_id])
        if not rows:
            raise ValueError("Dataset not found.")

        ds = rows[0]
        if not ds.get("is_deletable"):
            raise ValueError("External baseline benchmark datasets cannot be deleted.")

        # Remove physical file if exists
        file_path = ds.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        execute_dml("DELETE FROM datasets_catalog WHERE dataset_id = ?;", [dataset_id])
        return True
