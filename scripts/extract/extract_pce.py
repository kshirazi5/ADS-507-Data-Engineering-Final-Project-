"""
PCE (Personal Consumption Expenditures) Data Extraction
Extracts economic indicator data from CSV
"""

import pandas as pd
from pathlib import Path

def extract_pce(input_file, output_file):
    """Extract and validate PCE economic data"""
    
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records")
    
    # Show info
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"Date range: {df['observation_date'].min()} to {df['observation_date'].max()}")
    
    # Convert date to proper datetime
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    
    # Check for issues
    print(f"\nData Quality Checks:")
    print(f"- Null values in observation_date: {df['observation_date'].isnull().sum()}")
    print(f"- Null values in PCE: {df['PCE'].isnull().sum()}")
    print(f"- Duplicate dates: {df['observation_date'].duplicated().sum()}")
    
    # Sort by date
    df = df.sort_values('observation_date')
    
    # Add year and month columns for easier joining
    df['year'] = df['observation_date'].dt.year
    df['month'] = df['observation_date'].dt.month
    
    # Save cleaned data
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved to {output_file}")
    
    # Show summary
    print(f"\nSummary Statistics:")
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['observation_date'].min()} to {df['observation_date'].max()}")
    print(f"PCE range: ${df['PCE'].min():.2f} to ${df['PCE'].max():.2f}")
    print(f"Average PCE: ${df['PCE'].mean():.2f}")
    
    return df

if __name__ == "__main__":
    input_file = 'data/raw/PCE.csv'
    output_file = 'data/processed/pce_clean.csv'
    
    # Create output directory if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    df = extract_pce(input_file, output_file)
    print("\n✓ PCE extraction complete!")
