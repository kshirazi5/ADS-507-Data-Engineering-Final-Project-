"""
Load transaction data into MySQL (truncate + full reload)
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pandas as pd
from datetime import datetime
import time
from utils.connections import get_mysql_connection


def get_or_create_product(cursor, stock_code, description, unit_price):
    """Get product_key or create new product"""
    cursor.execute(
        "SELECT product_key FROM dim_products WHERE stock_code = %s",
        (stock_code,)
    )
    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute("""
        INSERT INTO dim_products (stock_code, description, unit_price)
        VALUES (%s, %s, %s)
    """, (stock_code, description or 'Unknown', unit_price or 0.0))

    return cursor.lastrowid


def get_customer_key(cursor, customer_id):
    """Get customer_key from customer_id"""
    if pd.isna(customer_id):
        return None

    try:
        customer_id = int(float(customer_id))
    except (ValueError, TypeError):
        return None

    cursor.execute(
        "SELECT customer_key FROM dim_customers WHERE customer_id = %s",
        (customer_id,)
    )
    result = cursor.fetchone()
    return result[0] if result else None


def load_transactions(chunksize=500):
    """Load transactions: truncate existing data then reload from scratch."""

    print("Connecting to database...")
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # --- Truncate for a clean reload ---
    print("Truncating fact_transactions and dim_products for clean reload...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE fact_transactions")
    cursor.execute("TRUNCATE TABLE dim_products")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    print("Tables truncated.\n")

    print(f"Loading transactions in chunks of {chunksize}...")

    chunks_processed = 0
    total_inserted = 0
    total_skipped = 0
    start_time = datetime.now()

    chunk_iterator = pd.read_csv(
        'data/processed/transactions_clean.csv', chunksize=chunksize
    )

    for chunk in chunk_iterator:
        chunks_processed += 1
        chunk_start = datetime.now()
        chunk_inserted = 0

        for _, row in chunk.iterrows():
            try:
                if pd.isna(row.get('invoiceno')) or pd.isna(row.get('stockcode')):
                    total_skipped += 1
                    continue

                product_key = get_or_create_product(
                    cursor,
                    str(row['stockcode']),
                    row.get('description'),
                    row.get('unitprice', 0)
                )

                customer_key = get_customer_key(cursor, row.get('customerid'))

                try:
                    invoice_date = pd.to_datetime(row['invoicedate'])
                    if pd.isna(invoice_date):
                        total_skipped += 1
                        continue
                except (ValueError, TypeError):
                    total_skipped += 1
                    continue

                date_key = (invoice_date.year * 10000 +
                           invoice_date.month * 100 +
                           invoice_date.day)

                cursor.execute("""
                    INSERT INTO fact_transactions
                    (invoice_no, customer_key, product_key, date_key,
                     transaction_date, quantity, unit_price, country)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(row['invoiceno']),
                    customer_key,
                    product_key,
                    date_key,
                    invoice_date,
                    int(row.get('quantity', 0)),
                    float(row.get('unitprice', 0)),
                    row.get('country', 'Unknown')
                ))

                total_inserted += 1
                chunk_inserted += 1

            except Exception:
                total_skipped += 1
                continue

        # Commit after each chunk
        try:
            conn.commit()
        except Exception:
            print("  Connection error on commit, reconnecting...")
            cursor.close()
            conn.close()
            time.sleep(2)
            conn = get_mysql_connection()
            cursor = conn.cursor()

        chunk_time = (datetime.now() - chunk_start).total_seconds()
        elapsed = (datetime.now() - start_time).total_seconds()

        total_rows = 541909
        rows_processed = chunks_processed * chunksize
        pct = min(rows_processed / total_rows * 100, 100)
        chunks_remaining = max((total_rows - rows_processed) / chunksize, 0)
        avg_time = elapsed / chunks_processed
        est_remaining = (chunks_remaining * avg_time) / 60

        print(
            f"Chunk {chunks_processed}: +{chunk_inserted} | "
            f"Total: {total_inserted:,} inserted, {total_skipped:,} skipped | "
            f"{pct:.1f}% | Est. remaining: {est_remaining:.1f} min"
        )

        # Refresh connection every 10 chunks to prevent timeout
        if chunks_processed % 10 == 0:
            print("  -> Refreshing connection...")
            cursor.close()
            conn.close()
            time.sleep(1)
            conn = get_mysql_connection()
            cursor = conn.cursor()

    total_time = (datetime.now() - start_time).total_seconds()

    print(f"\n✓ Loading complete!")
    print(f"Time taken: {total_time/60:.1f} minutes")
    print(f"Total transactions inserted: {total_inserted:,}")
    print(f"Total skipped: {total_skipped:,}")

    # Verify counts
    cursor.execute("SELECT COUNT(*) FROM fact_transactions")
    trans_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dim_products")
    prod_count = cursor.fetchone()[0]

    print(f"\nDatabase totals:")
    print(f"- Transactions: {trans_count:,}")
    print(f"- Products: {prod_count:,}")

    # Show sample
    print("\nSample transactions:")
    cursor.execute("""
        SELECT t.invoice_no, p.stock_code, t.quantity, t.unit_price, t.country
        FROM fact_transactions t
        JOIN dim_products p ON t.product_key = p.product_key
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} | Qty: {row[2]} | ${row[3]:.2f} | {row[4]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("TRANSACTION DATA LOADING (Truncate + Full Reload)")
    print("=" * 60)
    load_transactions(chunksize=500)
