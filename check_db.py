#!/usr/bin/env python3
import sqlite3
from datetime import datetime
import os

def check_database():
    """Display a clean overview of the PKM database structure and contents."""
    try:
        conn = sqlite3.connect('pkm/db/pkm.db')
        cursor = conn.cursor()
        
        print("\n📊 PKM Database Overview")
        print("=" * 50)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        # Table categories for better organization
        categories = {
            'Core Metrics': ['daily_metrics', 'sub_daily_moods'],
            'Activity Tracking': ['habit_logs', 'work_logs', 'alcohol_logs'],
            'Health Monitoring': ['sleep_logs'],
            'Goals & Planning': ['goals', 'habits'],
            'Other': []
        }
        
        # Categorize tables
        categorized_tables = {cat: [] for cat in categories}
        for table in tables:
            table_name = table[0]
            categorized = False
            for cat, table_list in categories.items():
                if table_name in table_list:
                    categorized_tables[cat].append(table_name)
                    categorized = True
                    break
            if not categorized:
                categorized_tables['Other'].append(table_name)
        
        # Print tables by category
        for category, table_list in categorized_tables.items():
            if table_list:  # Only show categories with tables
                print(f"\n🔹 {category}")
                print("-" * 50)
                
                for table_name in table_list:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    # Print table summary
                    print(f"\n📋 {table_name}")
                    print(f"   Records: {count}")
                    
                    # If table has data, show date range if applicable
                    if count > 0:
                        date_cols = [col[1] for col in columns if 'date' in col[1].lower() or 'timestamp' in col[1].lower()]
                        for date_col in date_cols:
                            cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name} WHERE {date_col} IS NOT NULL;")
                            min_date, max_date = cursor.fetchone()
                            if min_date and max_date:
                                print(f"   Date Range: {min_date} to {max_date}")
                    
                    # Print column summary
                    print("   Columns:")
                    for col in columns:
                        col_name = col[1]
                        col_type = col[2]
                        print(f"   - {col_name} ({col_type})")
        
        conn.close()
        print("\n✅ Database overview complete!")
        
    except sqlite3.Error as e:
        print(f"❌ SQLite error occurred: {e}")
        if conn:
            conn.close()
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    if not os.path.exists('pkm/db/pkm.db'):
        print("❌ Error: Database file not found at pkm/db/pkm.db")
        exit(1)
    check_database()
