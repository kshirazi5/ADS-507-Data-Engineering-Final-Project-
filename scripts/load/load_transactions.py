"""
Load transaction data into MySQL (with connection handling)
"""

import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime
import time

load_dotenv()

def get_connection():
    """Create a fresh database connection"""
    return mysql.connector.connect(
        host=os.getenv('AZURE_DB_HOST'),
        user=os.getenv('AZURE_DB_USER'),
        password=os.getenv('AZURE_DB_PASSWORD'),
        database=os.getenv('AZURE_DB_NAME'),
        ssl_disabled=False,
        ssl_verify_cert=False,
        autocommit=False,
        connect_timeout=30,
        connection_timeout=30
    )

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
    except:
        return None
    
    cursor.execute(
        "SELECT customer_key FROM dim_customers WHERE customer_id = %s",
        (customer_id,)
    )
    result = cursor.fetchone()
    return result[0] if result else None

def load_transactions(chunksize=500, start_chunk=0):
    """Load transactions in chunks with connection management"""
    
    print("Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Loading transactions (starting from chunk {start_chunk+1})...")
    print("Processing in smaller batches with connection refreshes...\n")
    
    chunks_processed = 0
    total_inserted = 0
    total_skipped = 0
    start_time = datetime.now()
    
    # Read and process in chunks
    chunk_iterator = pd.read_csv('data/processed/transactions_clean.csv', chunksize=chunksize)
    
    # Skip to start_chunk if resuming
    for _ in range(start_chunk):
        next(chunk_iterator)
        chunks_processed += 1
    
    for chunk in chunk_iterator:
        chunks_processed += 1
        chunk_start = datetime.now()
        chunk_inserted = 0
        
        for _, row in chunk.iterrows():
            try:
                # Skip if missing critical data
                if pd.isna(row.get('invoiceno')) or pd.isna(row.get('stockcode')):
                    total_skipped += 1
                    continue
                
                # Get or create product
                product_key = get_or_create_product(
                    cursor,
                    str(row['stockcode']),
                    row.get('description'),
                    row.get('unitprice', 0)
                )
                
                # Get customer key
                customer_key = get_customer_key(cursor, row.get('customerid'))
                
                # Parse invoice date
                try:
                    invoice_date = pd.to_datetime(row['invoicedate'])
                    if pd.isna(invoice_date):
                        total_skipped += 1
                        continue
                except:
                    total_skipped += 1
                    continue
                
                # Calculate date_key
                date_key = (invoice_date.year * 10000 + 
                           invoice_date.month * 100 + 
                           invoice_date.day)
                
                # Insert transaction
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
                
            except Exception as e:
                total_skipped += 1
                continue
        
        # Commit and refresh connection every chunk
        try:
            conn.commit()
        except Exception as e:
            print(f"  Connection error on commit, reconnecting...")
            cursor.close()
            conn.close()
            time.sleep(2)
            conn = get_connection()
            cursor = conn.cursor()
        
        chunk_time = (datetime.now() - chunk_start).total_seconds()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Estimate remaining
        chunks_total = 542  # 541909 / 1000
        chunks_left = chunks_total - chunks_processed
        avg_time = elapsed / chunks_processed
        est_remaining = (chunks_left * avg_time) / 60
        
        print(f"Chunk {chunks_processed}: +{chunk_inserted} | Total: {total_inserted:,} inserted, {total_skipped:,} skipped | "
              f"Time: {elapsed:.0f}s | Est. remaining: {est_remaining:.1f} min")
        
        # Refresh connection every 10 chunks (prevent timeout)
        if chunks_processed % 10 == 0:
            print(f"  → Refreshing connection...")
            cursor.close()
            conn.close()
            time.sleep(1)
            conn = get_connection()
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
    print("="*60)
    print("TRANSACTION DATA LOADING (Improved)")
    print("="*60)
    
    # You already loaded ~4000 records, so we can continue from chunk 5
    # Or start fresh - check first
    load_transactions(chunksize=500, start_chunk=4)
