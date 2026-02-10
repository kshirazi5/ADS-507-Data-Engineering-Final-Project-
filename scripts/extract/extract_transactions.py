"""
Transaction Data Extraction (Chunked for large files)
Extracts transaction data from online retail CSV
"""

import pandas as pd
from pathlib import Path

def extract_transactions(input_file, output_file, chunksize=10000):
    """Extract transaction data in chunks"""
    
    print(f"Reading {input_file} in chunks of {chunksize}...")
    
    chunks_processed = 0
    total_records = 0
    total_saved = 0
    
    # Process in chunks and save
    first_chunk = True
    
    for chunk in pd.read_csv(input_file, chunksize=chunksize):
        chunks_processed += 1
        total_records += len(chunk)
        
        # Show columns on first chunk
        if first_chunk:
            print(f"\nColumns found: {chunk.columns.tolist()}")
            print(f"Sample data:")
            print(chunk.head(2))
            first_chunk = False
        
        # Clean column names
        chunk.columns = chunk.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Convert date if it exists
        date_columns = ['invoicedate', 'invoice_date', 'date']
        for col in date_columns:
            if col in chunk.columns:
                chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
                break
        
        # Remove rows with critical nulls
        initial_len = len(chunk)
        
        # Must have invoice number and stock code
        if 'invoiceno' in chunk.columns:
            chunk = chunk.dropna(subset=['invoiceno'])
        if 'stockcode' in chunk.columns:
            chunk = chunk.dropna(subset=['stockcode'])
        
        removed = initial_len - len(chunk)
        if removed > 0:
            print(f"  Removed {removed} rows with null critical values")
        
        total_saved += len(chunk)
        
        # Save (append mode after first chunk)
        mode = 'w' if chunks_processed == 1 else 'a'
        header = chunks_processed == 1
        chunk.to_csv(output_file, mode=mode, header=header, index=False)
        
        print(f"Chunk {chunks_processed}: Processed {len(chunk)} records (Total: {total_saved})")
    
    print(f"\n✓ Extraction complete!")
    print(f"Total chunks processed: {chunks_processed}")
    print(f"Total records read: {total_records}")
    print(f"Total records saved: {total_saved}")
    print(f"Records removed: {total_records - total_saved}")
    
    return total_saved

if __name__ == "__main__":
    input_file = 'data/raw/online_retail.csv'
    output_file = 'data/processed/transactions_clean.csv'
    
    # Create output directory if needed
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    total = extract_transactions(input_file, output_file, chunksize=10000)
    print(f"\n✓ Transaction extraction complete! {total} records ready to load.")
