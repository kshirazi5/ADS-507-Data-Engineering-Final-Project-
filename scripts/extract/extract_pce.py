"""
PCE (Personal Consumption Expenditures) Data Extraction
Enriches economic data with Quarterly and Momentum metrics.
"""

import pandas as pd
from pathlib import Path
import logging

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_pce(input_file, output_file):
    """Extract and add advanced economic transformations including Quarters"""
    
    print(f"--- Starting PCE Enrichment: {input_file} ---")
    
    if not Path(input_file).exists():
        logging.error(f"Input file not found: {input_file}")
        return None

    df = pd.read_csv(input_file)
    
    # 1. CLEANING: Standardize Date and Sort
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    df = df.sort_values('observation_date')
    
    # --- TRANSFORMATION 1: Quarterly Decomposition ---
    # Maps the month to Q1, Q2, Q3, or Q4
    df['quarter'] = df['observation_date'].dt.quarter
    df['quarter_label'] = 'Q' + df['quarter'].astype(str)
    
    # --- TRANSFORMATION 2: Economic Momentum (MoM Change) ---
    df['pce_mom_change_pct'] = df['PCE'].pct_change() * 100
    
    # --- TRANSFORMATION 3: Calendar Decomposition ---
    df['year'] = df['observation_date'].dt.year
    df['month'] = df['observation_date'].dt.month
    
    # --- TRANSFORMATION 4: Economic Status Flag ---
    df['econ_status'] = df['pce_mom_change_pct'].apply(
        lambda x: 'Expansion' if x > 0 else ('Contraction' if x < 0 else 'Stable')
    )
    
    # 2. DATA QUALITY: Fill NaN from pct_change
    df['pce_mom_change_pct'] = df['pce_mom_change_pct'].fillna(0.0)
    
    # 3. SAVE
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"--- SUCCESS: {len(df)} records enriched with Quarters {df['quarter_label'].unique()} ---")
    
    # Sample output for your Design Document
    print("\nQuarterly Economic View:")
    print(df[['observation_date', 'quarter_label', 'PCE', 'econ_status']].tail(5))
    
    return df

if __name__ == "__main__":
    input_file = 'data/raw/PCE.csv'
    output_file = 'data/processed/pce_clean.csv'
    
    try:
        extract_pce(input_file, output_file)
    except Exception as e:
        logging.error(f"PCE extraction failed: {e}")