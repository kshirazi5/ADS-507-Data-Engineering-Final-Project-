"""
Shared MySQL connection helper for the ETL pipeline.
Reuses DB_CONFIG from config/db_config.py.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so config.db_config is importable
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import mysql.connector
from config.db_config import DB_CONFIG


def get_mysql_connection(autocommit=False, connect_timeout=30):
    """Return a mysql.connector connection using the shared DB_CONFIG.

    Parameters
    ----------
    autocommit : bool
        Whether the connection should auto-commit after each statement.
    connect_timeout : int
        Connection timeout in seconds.
    """
    conn_params = dict(DB_CONFIG)
    conn_params["autocommit"] = autocommit
    conn_params["connect_timeout"] = connect_timeout
    conn_params["connection_timeout"] = connect_timeout
    return mysql.connector.connect(**conn_params)
