from pkm.pkm_manager import PKMManager
from datetime import datetime

def get_date_range():
    pkm = PKMManager()
    conn = pkm.get_db_connection()
    cursor = conn.cursor()
    
    # Query for the earliest and latest dates
    cursor.execute("""
        SELECT MIN(date), MAX(date)
        FROM daily_logs;
    """)
    
    min_date, max_date = cursor.fetchone()
    
    conn.close()
    
    if min_date and max_date:
        return min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')
    return None, None

if __name__ == "__main__":
    min_date, max_date = get_date_range()
    if min_date and max_date:
        print(f"{min_date},{max_date}")
    else:
        print("no_data")
