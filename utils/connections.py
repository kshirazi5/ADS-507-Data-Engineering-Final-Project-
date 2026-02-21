"""
Shared MySQL connection helper for the ETL pipeline.
Reuses DB_CONFIG from config/db_config.py.
"""

import sys
from pathlib import Path
import mysql.connector

# Ensure project root is on sys.path so config.db_config is importable
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.db_config import DB_CONFIG
from utils.logger import setup_logger

# Initialize logger for connection monitoring
logger = setup_logger("DBConnection")

def get_mysql_connection(autocommit=False, connect_timeout=30):
    """
    Return a mysql.connector connection using the shared DB_CONFIG.
    Includes error handling and logging for production monitoring.
    """
    conn_params = dict(DB_CONFIG)
    conn_params["autocommit"] = autocommit
    conn_params["connect_timeout"] = connect_timeout
    
    try:
        conn = mysql.connector.connect(**conn_params)
        if conn.is_connected():
            return conn
            
    except mysql.connector.Error as err:
        logger.error(f"Failed to connect to MySQL: {err}")
        # Re-raise the error so the calling script knows to stop
        raise

def test_connection():
    """Simple utility to verify DB connectivity during 'Demo Day'"""
    try:
        conn = get_mysql_connection()
        logger.info("✓ Database connection successful!")
        conn.close()
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()
