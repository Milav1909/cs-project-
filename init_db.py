import sqlite3
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)
os.makedirs(os.path.join('data', 'uploads'), exist_ok=True)

# Initialize the database
db_path = os.path.join('data', 'files.db')
with sqlite3.connect(db_path) as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            size INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    conn.commit()

print(f"Database initialized at: {os.path.abspath(db_path)}") 