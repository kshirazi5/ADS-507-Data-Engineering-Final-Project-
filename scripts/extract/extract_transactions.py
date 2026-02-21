"""
Transaction Data Extraction (Chunked with Advanced Transformations)
Extracts and enriches retail data for production analytics.
"""

import pandas as pd
from pathlib import Path
import logging

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_transactions(input_file, output_file, chunksize=10000):
    """Extract, clean, and add retail-specific transformations in chunks"""
    
    print(f"--- Starting Transaction Enrichment: {input_file} ---")
    
    if not Path(input_file).exists():
        logging.error(f"Input file not found: {input_file}")
        return 0

    chunks_processed = 0
    total_saved = 0
    first_chunk = True
    
    for chunk in pd.read_csv(input_file, chunksize=chunksize):
        chunks_processed += 1
        
        # 1. CLEANING: Standardize column names
        chunk.columns = chunk.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # --- TRANSFORMATION 1: Return Flagging ---
        # In retail datasets (like Online Retail), negative quantities indicate returns
        chunk['is_return'] = chunk['quantity'] < 0
        
        # --- TRANSFORMATION 2: Unit Price Normalization ---
        # Clean up negative prices and convert to absolute values for returns
        chunk['unit_price_clean'] = chunk['unitprice'].abs().fillna(0.0)
        
        # --- TRANSFORMATION 3: Total Transaction Value (Calculated Column) ---
        # Essential for revenue reporting in your MySQL fact table
        chunk['total_value'] = chunk['quantity'] * chunk['unit_price_clean']
        
        # --- TRANSFORMATION 4: Anomaly Detection (Statistical Outliers) ---
        # Flags transactions where unit price is significantly higher than average
        avg_price = chunk['unit_price_clean'].mean()
        std_price = chunk['unit_price_clean'].std()
        chunk['is_price_outlier'] = chunk['unit_price_clean'] > (avg_price + (3 * std_price))
        
        # --- TRANSFORMATION 5: DateTime Decomposition ---
        # Extracting components helps if you want to join to your Date Dimension later
        if 'invoicedate' in chunk.columns:
            chunk['invoicedate'] = pd.to_datetime(chunk['invoicedate'], errors='coerce')
            chunk['hour_of_day'] = chunk['invoicedate'].dt.hour
            chunk['is_weekend'] = chunk['invoicedate'].dt.dayofweek >= 5

        # 2. SAVE: Append mode after the first chunk
        mode = 'w' if first_chunk else 'a'
        header = first_chunk
        chunk.to_csv(output_file, mode=mode, header=header, index=False)
        
        total_saved += len(chunk)
        first_chunk = False
        
        if chunks_processed % 5 == 0:
            print(f"Processed {chunks_processed} chunks... (Total records: {total_saved})")

    print(f"--- SUCCESS: {total_saved} transactions saved to {output_file} ---")
    return total_saved

if __name__ == "__main__":
    input_file = 'data/raw/online_retail.csv'
    output_file = 'data/processed/transactions_clean.csv'
    
    try:
        # Create output directory if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        extract_transactions(input_file, output_file)
    except Exception as e:
        logging.error(f"Transaction extraction failed: {e}")