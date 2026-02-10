import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to database
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor()

# Show all tables
print("=== TABLES IN DATABASE ===")
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*50 + "\n")

# For each table, show row count and sample data
for table in tables:
    table_name = table[0]
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Table: {table_name}")
    print(f"Row count: {count}")
    
    # Show first 3 rows
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"DESCRIBE {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}")
        print("Sample rows:")
        for row in rows:
            print(f"  {row}")
    
    print("\n" + "-"*50 + "\n")

cursor.close()
conn.close()
