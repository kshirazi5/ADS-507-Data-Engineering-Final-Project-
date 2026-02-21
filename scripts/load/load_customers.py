import pandas as pd
import logging
from utils.connections import get_mysql_connection

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_customers():
    # Read the enriched CSV from the processed folder
    df = pd.read_csv('data/processed/customers_clean.csv')
    
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # SQL query updated with new columns
    insert_query = """
    INSERT INTO dim_customers 
    (customer_id, gender, age, age_segment, city, membership_type, spending_tier, engagement_score, is_valid_record)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        age_segment = VALUES(age_segment),
        spending_tier = VALUES(spending_tier),
        engagement_score = VALUES(engagement_score),
        is_valid_record = VALUES(is_valid_record)
    """

    # Prepare data for batch insertion
    data = []
    for _, row in df.iterrows():
        data.append((
            int(row['customer_id']),
            row['gender'],
            int(row['age']),
            row['age_segment'],
            row['city'],
            row['membership_type'],
            row['spending_tier'],
            float(row['engagement_score']),
            bool(row['is_valid_record'])
        ))

    try:
        cursor.executemany(insert_query, data)
        conn.commit()
        logging.info(f"Successfully loaded {cursor.rowcount} customers (including updates).")
    except Exception as e:
        logging.error(f"Error loading customers: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    load_customers()
