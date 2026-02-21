"""
Customer Behavior Data Extraction Script
Enriches customer data with segmentation and quality metrics.
"""

import pandas as pd
from pathlib import Path
import logging

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_customers(input_file, output_file):
    """Extract, clean, and add advanced transformations to customer data"""
    
    print(f"--- Starting Customer Enrichment: {input_file} ---")
    
    if not Path(input_file).exists():
        logging.error(f"Input file not found: {input_file}")
        return None

    df = pd.read_csv(input_file)
    
    # 1. CLEANING: Standardization
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # --- TRANSFORMATION 1: Demographic Binning ---
    # Useful for analyzing which age groups drive the most revenue
    bins = [0, 18, 30, 50, 70, 120]
    labels = ['Gen Z/Minor', 'Young Adult', 'Adult', 'Middle Aged', 'Senior']
    df['age_segment'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)
    
    # --- TRANSFORMATION 2: Spending Tier (Percentile Based) ---
    # Instead of just a median flag, we create 3 tiers (Low, Medium, High)
    if 'total_spend' in df.columns:
        df['spending_tier'] = pd.qcut(df['total_spend'], q=3, labels=['Low', 'Medium', 'High'])
    
    # --- TRANSFORMATION 3: Engagement Score ---
    # Creating a synthetic feature combining rating and discount usage
    if 'average_rating' in df.columns and 'discount_applied' in df.columns:
        # Convert boolean to 1/0
        discount_val = (df['discount_applied'].astype(str).str.upper() == 'TRUE').astype(int)
        # Score = Rating (1-5) + 2 points if they use discounts
        df['engagement_score'] = df['average_rating'] + (discount_val * 2)
    
    # --- TRANSFORMATION 4: Data Quality Flag ---
    # Identify records that have missing critical info for downstream models
    critical_cols = ['age', 'total_spend', 'membership_type']
    df['is_valid_record'] = df[critical_cols].notnull().all(axis=1)
    
    # 2. VALIDATION SUMMARY
    valid_pct = (df['is_valid_record'].sum() / len(df)) * 100
    print(f"Data Quality Check: {valid_pct:.1f}% of records are complete.")
    
    # 3. SAVE: Save enriched data
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"--- SUCCESS: {len(df)} records enriched and saved to {output_file} ---")
    
    # Quick Analytics for your report
    print("\nSummary of New Features:")
    print(df[['age_segment', 'spending_tier']].value_counts().head(5))
    
    return df

if __name__ == "__main__":
    input_file = 'data/raw/E-commerce_Customer_Behavior_-_Sheet1.csv'
    output_file = 'data/processed/customers_clean.csv'
    
    try:
        extract_customers(input_file, output_file)
    except Exception as e:
        logging.error(f"Extraction failed: {e}")
