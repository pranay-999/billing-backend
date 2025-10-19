import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

# Create table for products (tiles, sanitary, etc.)
cursor.execute('''
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_name TEXT UNIQUE,
    type TEXT,
    size TEXT,
    stock INTEGER,
    unit_price REAL
)
''')

# Create table for sales
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_name TEXT,
    type TEXT,
    size TEXT,
    boxes_sold INTEGER,
    unit_price REAL,
    amount REAL,
    gst_type TEXT,
    cgst REAL,
    sgst REAL,
    final_amount REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("✅ Database and tables created successfully!")
