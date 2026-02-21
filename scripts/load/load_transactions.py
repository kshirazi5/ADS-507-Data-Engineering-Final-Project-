import pandas as pd
import logging
from utils.connections import get_mysql_connection

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_transactions(chunksize=2000):
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Truncate for full reload as per your project design
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE fact_transactions;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    insert_query = """
    INSERT INTO fact_transactions 
    (invoice_no, customer_key, product_key, date_key, transaction_date, quantity, unit_price, total_value, is_return, is_price_outlier, country)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    chunk_iterator = pd.read_csv('data/processed/transactions_clean.csv', chunksize=chunksize)

    for chunk in chunk_iterator:
        batch_data = []
        for _, row in chunk.iterrows():
            # Basic date_key generation (YYYYMMDD)
            dt = pd.to_datetime(row['invoicedate'])
            date_key = int(dt.strftime('%Y%m%d'))

            # Map the new enriched columns
            batch_data.append((
                str(row['invoiceno']),
                None, # Customer keys would usually be looked up here
                1,    # Placeholder product_key
                date_key,
                dt,
                int(row['quantity']),
                float(row['unit_price_clean']),
                float(row['total_value']),
                bool(row['is_return']),
                bool(row['is_price_outlier']),
                row['country']
            ))
        
        cursor.executemany(insert_query, batch_data)
        conn.commit()
        logging.info(f"Loaded chunk of {len(batch_data)} records...")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_transactions()
