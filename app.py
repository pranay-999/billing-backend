from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_NAME = "inventory.db"

# ---------------------------
# Helper Function
# ---------------------------
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, args)
    data = cursor.fetchall()
    conn.commit()
    conn.close()
    return (data[0] if data else None) if one else data

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    return jsonify({"message": "Billing backend ready!"})

# Fetch stock by design name
@app.route('/get_stock/<design_name>', methods=['GET'])
def get_stock(design_name):
    result = query_db("SELECT * FROM stock WHERE design_name = ?", (design_name,), one=True)
    if result:
        return jsonify({
            "design_name": result[1],
            "type": result[2],
            "size": result[3],
            "stock": result[4],
            "unit_price": result[5]
        })
    return jsonify({"error": "Design not found"}), 404

# Add a sale entry with GST logic
@app.route('/add_sale', methods=['POST'])
def add_sale():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        design_name = data.get('design_name')
        boxes_sold = data.get('boxes_sold')
        unit_price = data.get('unit_price')
        gst_mode = data.get('gst_mode')

        if not design_name or not unit_price or not boxes_sold:
            return jsonify({"error": "Missing required fields"}), 400

        base_amount = float(unit_price) * int(boxes_sold)

        if gst_mode == "exclusive":
            cgst = base_amount * 0.09
            sgst = base_amount * 0.09
            final_amount = base_amount + cgst + sgst
        elif gst_mode == "inclusive":
            base = base_amount / 1.18
            cgst = base * 0.09
            sgst = base * 0.09
            final_amount = base_amount
        else:
            cgst = sgst = 0
            final_amount = base_amount

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales (design_name, type, size, boxes_sold, unit_price, amount, gst_type, cgst, sgst, final_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            design_name, data.get('type'), data.get('size'),
            boxes_sold, unit_price, base_amount, gst_mode,
            cgst, sgst, final_amount
        ))
        conn.commit()
        conn.close()

        return jsonify({"message": "Sale added successfully!", "final_amount": final_amount})
    except Exception as e:
        print("Error in /add_sale:", str(e))
        return jsonify({"error": str(e)}), 500


# Get all sales
@app.route('/get_sales', methods=['GET'])
def get_sales():
    result = query_db("SELECT * FROM sales ORDER BY date DESC")
    return jsonify(result)

# --- Initialize Database with Sample Stock if Empty ---
def initialize_stock():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock")
    count = cursor.fetchone()[0]
    if count == 0:
        print("Inserting default stock data...")
        items = [
            ("Galaxy White", "Tile", "2x2", 100, 45.0),
            ("Aqua Blue", "Sanitary", "Medium", 50, 120.0),
            ("Marble Gloss", "Tile", "1x1", 80, 65.0)
        ]
        cursor.executemany(
            "INSERT INTO stock (design_name, type, size, stock, unit_price) VALUES (?, ?, ?, ?, ?)",
            items
        )
        conn.commit()
    conn.close()

# call function when app starts
initialize_stock()

# ---------------------------
# Update Sale
# ---------------------------
@app.route('/update_sale/<int:bill_id>', methods=['PUT'])
def update_sale(bill_id):
    try:
        data = request.get_json()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        design_name = data.get("design_name")
        type_ = data.get("type")
        size = data.get("size")
        boxes_sold = int(data.get("boxes_sold"))
        unit_price = float(data.get("unit_price"))
        gst_mode = data.get("gst_mode", "exclusive")

        base_amount = unit_price * boxes_sold

        if gst_mode == "exclusive":
            cgst = base_amount * 0.09
            sgst = base_amount * 0.09
            final_amount = base_amount + cgst + sgst
        elif gst_mode == "inclusive":
            base = base_amount / 1.18
            cgst = base * 0.09
            sgst = base * 0.09
            final_amount = base_amount
        else:
            cgst = sgst = 0
            final_amount = base_amount

        cursor.execute(
            """
            UPDATE sales 
            SET design_name=?, type=?, size=?, boxes_sold=?, unit_price=?, amount=?, gst_type=?, cgst=?, sgst=?, final_amount=? 
            WHERE bill_id=?
            """,
            (design_name, type_, size, boxes_sold, unit_price, base_amount, gst_mode, cgst, sgst, final_amount, bill_id)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Sale updated successfully!"})
    except Exception as e:
        print("Error updating sale:", str(e))
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Delete Sale
# ---------------------------
@app.route('/delete_sale/<int:bill_id>', methods=['DELETE'])
def delete_sale(bill_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sales WHERE bill_id=?", (bill_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Sale deleted successfully!"})
    except Exception as e:
        print("Error deleting sale:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
