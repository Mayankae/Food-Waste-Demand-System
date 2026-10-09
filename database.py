import sqlite3
import pandas as pd
from config import Config

def get_db_connection():
    """Establish a connection to the SQLite Data Warehouse database."""
    conn = sqlite3.connect(Config.WAREHOUSE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=None):
    """Execute a read query and return rows as list of dicts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    finally:
        conn.close()

def execute_scalar(query, params=None):
    """Execute a query that returns a single scalar value."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def execute_df(query, params=None):
    """Execute a SQL query and return results as a Pandas DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

def execute_dml(query, params=None):
    """Execute an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
