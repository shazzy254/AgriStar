
import sqlite3
import os

def check_schema():
    db_path = 'db.sqlite3' # Assuming default location in root
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check marketplace_order table
    print("--- marketplace_order Table Info ---")
    cursor.execute("PRAGMA table_info(marketplace_order)")
    columns = cursor.fetchall()
    found = False
    for col in columns:
        # col: (cid, name, type, notnull, dflt_value, pk)
        cid, name, dtype, notnull, dflt, pk = col
        if name == 'assigned_rider_id':
            found = True
            print(f"Column: {name}")
            print(f"  Type: {dtype}")
            print(f"  Not Null: {notnull} (1=True, 0=False)")
            print(f"  Default: {dflt}")
            
    if not found:
        print("Column 'assigned_rider_id' NOT FOUND in marketplace_order")

    conn.close()

if __name__ == '__main__':
    check_schema()
