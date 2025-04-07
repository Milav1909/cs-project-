import sqlite3
import os

def create_db():
    # Create directories
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/uploads'):
        os.mkdir('data/uploads')
    
    # Create database
    db_path = 'data/files.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create table
    c.execute('''
    CREATE TABLE IF NOT EXISTS files
    (id TEXT PRIMARY KEY,
     filename TEXT NOT NULL,
     filepath TEXT NOT NULL,
     size INTEGER NOT NULL,
     created_at TIMESTAMP NOT NULL,
     expires_at TIMESTAMP NOT NULL)
    ''')
    
    # Save (commit) the changes
    conn.commit()
    
    # Close the connection
    conn.close()
    
    print "Database created at:", os.path.abspath(db_path)

if __name__ == '__main__':
    create_db() 