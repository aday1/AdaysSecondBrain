import argparse
import sqlite3
import os
from werkzeug.security import generate_password_hash

def change_password(username, password):
    db_path = os.path.join(os.path.dirname(__file__), 'db', 'pkm.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the users table exists, create it if not
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    
    # Hash the password using werkzeug.security.generate_password_hash
    hashed_password = generate_password_hash(password)
    
    # Update the password for the user, insert if the user does not exist
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?) ON CONFLICT(username) DO UPDATE SET password = ?", (username, hashed_password, hashed_password))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change user password")
    parser.add_argument("--user", required=True, help="Username")
    parser.add_argument("--password", required=True, help="New password")
    args = parser.parse_args()
    
    change_password(args.user, args.password)