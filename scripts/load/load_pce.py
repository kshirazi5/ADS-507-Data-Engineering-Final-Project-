import pandas as pd
import logging
from utils.connections import get_mysql_connection

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_pce():
    df = pd.read_csv('data/processed/pce_clean.csv')
    conn = get_mysql_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO fact_economic_indicators 
    (date_key, observation_date, pce_value, pce_mom_change_pct, quarter_label, econ_status)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        pce_mom_change_pct = VALUES(pce_mom_change_pct),
        econ_status = VALUES(econ_status)
    """

    data = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(row['observation_date'])
        date_key = int(dt.strftime('%Y%m%d'))
        
        data.append((
            date_key,
            dt.date(),
            float(row['PCE']),
            float(row['pce_mom_change_pct']),
            row['quarter_label'],
            row['econ_status']
        ))

    cursor.executemany(insert_query, data)
    conn.commit()
    logging.info("PCE data load complete.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_pce()
