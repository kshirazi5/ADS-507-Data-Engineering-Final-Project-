"""
Load PCE economic data into MySQL database
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pandas as pd
import mysql.connector
from utils.connections import get_mysql_connection


def load_pce():
    """Load PCE data into fact_economic_indicators table"""

    # Read cleaned PCE data
    print("Reading cleaned PCE data...")
    df = pd.read_csv('data/processed/pce_clean.csv')
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    print(f"Loaded {len(df)} records")

    # Connect to database
    print("Connecting to database...")
    conn = get_mysql_connection()
    cursor = conn.cursor()

    print("Loading data...")

    # For each PCE record, find matching date_key and insert
    insert_query = """
    INSERT INTO fact_economic_indicators
    (date_key, observation_date, pce_value)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        pce_value = VALUES(pce_value)
    """

    records_inserted = 0
    records_skipped = 0

    for _, row in df.iterrows():
        # Calculate date_key (YYYYMMDD format)
        date_key = (row['year'] * 10000 +
                   row['month'] * 100 +
                   row['observation_date'].day)

        try:
            cursor.execute(insert_query, (
                date_key,
                row['observation_date'].date(),
                float(row['PCE'])
            ))
            records_inserted += 1

            if records_inserted % 100 == 0:
                print(f"Inserted {records_inserted} records...")

        except mysql.connector.Error as err:
            print(f"Error inserting {row['observation_date']}: {err}")
            records_skipped += 1

    conn.commit()

    print(f"\n✓ Loading complete!")
    print(f"- Records inserted: {records_inserted}")
    print(f"- Records skipped: {records_skipped}")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM fact_economic_indicators")
    count = cursor.fetchone()[0]
    print(f"- Total in database: {count}")

    # Show sample
    print("\nSample data:")
    cursor.execute("""
        SELECT observation_date, pce_value
        FROM fact_economic_indicators
        ORDER BY observation_date DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: ${row[1]:.2f}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_pce()
