"""
Load customer data into MySQL database
"""

import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def load_customers():
    """Load customer data into dim_customers table"""
    
    # Read cleaned data
    print("Reading cleaned customer data...")
    df = pd.read_csv('data/processed/customers_clean.csv')
    print(f"Loaded {len(df)} records")
    
    # Connect to database
    print("Connecting to database...")
    conn = mysql.connector.connect(
        host=os.getenv('AZURE_DB_HOST'),
        user=os.getenv('AZURE_DB_USER'),
        password=os.getenv('AZURE_DB_PASSWORD'),
        database=os.getenv('AZURE_DB_NAME'),
        ssl_disabled=False,
        ssl_verify_cert=False
    )
    cursor = conn.cursor()
    
    # Insert data
    insert_query = """
    INSERT INTO dim_customers (customer_id, gender, age, city, membership_type)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        gender = VALUES(gender),
        age = VALUES(age),
        city = VALUES(city),
        membership_type = VALUES(membership_type)
    """
    
    records_inserted = 0
    for _, row in df.iterrows():
        cursor.execute(insert_query, (
            int(row['customer_id']),
            row['gender'],
            int(row['age']),
            row['city'],
            row['membership_type']
        ))
        records_inserted += 1
        if records_inserted % 50 == 0:
            print(f"Inserted {records_inserted} records...")
    
    conn.commit()
    print(f"\n✓ Successfully loaded {records_inserted} customers")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM dim_customers")
    count = cursor.fetchone()[0]
    print(f"Total customers in database: {count}")
    
    # Show sample
    print("\nSample data:")
    cursor.execute("SELECT * FROM dim_customers LIMIT 5")
    for row in cursor.fetchall():
        print(f"  Customer {row[1]}: {row[2]}, {row[3]} years old, {row[4]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_customers()
