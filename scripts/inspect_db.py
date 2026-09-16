import sqlite3

conn = sqlite3.connect('database/maintenance.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
for t in tables:
    name = t[0]
    cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
    print(f"Table {name}: {[c[1] for c in cols]}")
conn.close()
