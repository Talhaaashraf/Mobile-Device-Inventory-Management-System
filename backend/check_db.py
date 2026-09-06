import sqlite3

conn = sqlite3.connect('device_inventory.db')
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables:", tables)

# Try to find and print users table content
for t in tables:
    table_name = t[0]
    if 'user' in table_name.lower():
        print(f"\n--- Contents of {table_name} ---")
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
        cur.execute(f"PRAGMA table_info({table_name});")
        cols = [c[1] for c in cur.fetchall()]
        print("Columns:", cols)
        for row in rows:
            print(row)

conn.close()