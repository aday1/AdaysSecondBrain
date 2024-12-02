import sqlite3
import os

def initialize_database(db_path='pkm/db/pkm.db'):
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        # Check if database already exists
        db_exists = os.path.exists(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if db_exists:
            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            required_tables = {'daily_metrics', 'work_logs', 'projects', 'habits'}
            
            if not required_tables - existing_tables:
                print("Database already initialized with required tables.")
                return
            print("Database exists but missing some tables. Adding missing tables...")

        # Execute the initialization SQL script
        init_sql_path = os.path.join(os.path.dirname(__file__), 'db', 'init.sql')
        print(f"Loading SQL from: {init_sql_path}")

        with open(init_sql_path, 'r') as f:
            sql_script = f.read()
            statements = [s.strip() for s in sql_script.split(';') 
                        if s.strip() and not s.strip().startswith('--')]
            
            for statement in statements:
                try:
                    # Skip DROP statements if database exists
                    if db_exists and statement.upper().startswith('DROP'):
                        continue
                    cursor.execute(statement)
                except sqlite3.Error as e:
                    if 'already exists' not in str(e):
                        print(f"Error executing statement: {statement}")
                        print(f"Error was: {str(e)}")
                        raise

        conn.commit()
        print("Database initialization completed.")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def apply_migrations(db_path='pkm/db/pkm.db'):
    # Logic to apply migrations if required
    migrations_sql_path = os.path.join(os.path.dirname(__file__), 'db', 'migrations.sql')
    if os.path.exists(migrations_sql_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the migration SQL script
        with open(migrations_sql_path, 'r') as f:
            cursor.executescript(f.read())

        conn.commit()
        conn.close()
        print("Migrations applied successfully.")
    else:
        print("No migrations found.")

if __name__ == "__main__":
    initialize_database()
    apply_migrations()
