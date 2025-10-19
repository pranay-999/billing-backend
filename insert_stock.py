import sqlite3

# Connect to the database
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

# Sample stock entries
items = [
    ("Galaxy White", "Tile", "2x2", 100, 45.0),
    ("Aqua Blue", "Sanitary", "Medium", 50, 120.0),
    ("Marble Gloss", "Tile", "1x1", 80, 65.0)
]

for item in items:
    cursor.execute("""
        INSERT OR IGNORE INTO stock (design_name, type, size, stock, unit_price)
        VALUES (?, ?, ?, ?, ?)
    """, item)

conn.commit()
conn.close()

print("✅ Stock items inserted successfully!")
