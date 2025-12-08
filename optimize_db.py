"""
Clean and optimize the SQLite database
"""
import sqlite3
import os

db_path = 'db.sqlite3'

# Get current size
current_size = os.path.getsize(db_path) / (1024 * 1024)
print(f"Current database size: {current_size:.2f} MB")

# Connect and vacuum
print("Optimizing database...")
conn = sqlite3.connect(db_path)
conn.execute("VACUUM")
conn.close()

# Get new size
new_size = os.path.getsize(db_path) / (1024 * 1024)
print(f"New database size: {new_size:.2f} MB")
print(f"Space recovered: {current_size - new_size:.2f} MB")
print("✓ Database optimized successfully!")
