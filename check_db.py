import sqlite3
import os

# Path to your database
db_path = os.path.join(os.getcwd(), "backend", "ats_database.db")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, experience_years, domain FROM resumes")
    rows = cursor.fetchall()
    
    print("--- STORED RESUME DATA ---")
    for row in rows:
        print(f"ID: {row[0]}, File: {row[1]}, Exp: {row[2]}, Domain: {row[3]}")
    conn.close()
else:
    print(f"Database not found at {db_path}")
