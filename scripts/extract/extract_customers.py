"""
Customer Behavior Data Extraction Script
Extracts customer behavior data from CSV and prepares for loading
"""

import pandas as pd
from pathlib import Path

def extract_customers(input_file, output_file):
    """Extract and clean customer behavior data"""
    
    # Read the CSV
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records")
    
    # Show original columns
    print(f"\nOriginal columns: {df.columns.tolist()}")
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    print(f"Cleaned columns: {df.columns.tolist()}")
    
    # Convert boolean
    if 'discount_applied' in df.columns:
        df['discount_applied'] = df['discount_applied'].astype(str).str.upper() == 'TRUE'
    
    # Check for issues
    print(f"\nData Quality Checks:")
    print(f"Null values:\n{df.isnull().sum()}")
    print(f"Duplicates: {df['customer_id'].duplicated().sum()}")
    
    # Validate age range
    invalid_ages = ((df['age'] < 18) | (df['age'] > 100)).sum()
    if invalid_ages > 0:
        print(f"Warning: {invalid_ages} records with invalid ages")
    
    # Save cleaned data
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved to {output_file}")
    
    # Show summary
    print(f"\nSummary Statistics:")
    print(f"Total customers: {len(df)}")
    print(f"Average age: {df['age'].mean():.1f}")
    print(f"Average spend: ${df['total_spend'].mean():.2f}")
    print(f"Average rating: {df['average_rating'].mean():.2f}")
    
    return df

if __name__ == "__main__":
    input_file = 'data/raw/E-commerce_Customer_Behavior_-_Sheet1.csv'
    output_file = 'data/processed/customers_clean.csv'
    
    # Create output directory if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    df = extract_customers(input_file, output_file)
    print("\n✓ Customer extraction complete!")
