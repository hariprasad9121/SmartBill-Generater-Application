from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import os
from datetime import datetime
from io import BytesIO
import csv

app = Flask(__name__)
DB_PATH = os.path.join('database', 'bill.db')

# ---------- Initialize DB if not exists ----------
def init_db():
    if not os.path.exists('database'):
        os.makedirs('database')
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT NOT NULL,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        created_at TEXT NOT NULL
    )''')
    conn.close()

init_db()

# ---------- Home ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- New Bill Form ----------
@app.route('/form')
def form():
    return render_template('billform.html')

# ---------- Generate Bill ----------
@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    customer = request.form['customer']
    items = request.form['items']
    total = request.form['total']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO bills (customer, items, total, created_at) VALUES (?, ?, ?, ?)",
                 (customer, items, total, created_at))
    conn.commit()
    conn.close()

    return render_template('bill.html', customer=customer, items=items, total=total, created_at=created_at)

# ---------- View All Bills ----------
@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT * FROM bills ORDER BY created_at DESC")
    bills = cursor.fetchall()
    conn.close()
    return render_template('history.html', bills=bills)

# ---------- Search Bills by Customer ----------
@app.route('/search')
def search_bill():
    query = request.args.get('q', '').lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT * FROM bills WHERE LOWER(customer) LIKE ?", ('%' + query + '%',))
    bills = cursor.fetchall()
    conn.close()
    return render_template('search.html', bills=bills)

# ---------- Export Bills (Same as History Table) ----------
@app.route('/export')
def export_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT id, customer, items, total, created_at FROM bills ORDER BY created_at DESC")
    bills = cursor.fetchall()
    conn.close()

    # Create CSV content using BytesIO
    output = BytesIO()
    header = ['ID', 'Customer', 'Items', 'Total', 'Date']
    csv_lines = [",".join(header)]

    for bill in bills:
        line = ",".join([str(field) for field in bill])
        csv_lines.append(line)

    # Write to output stream
    output.write("\n".join(csv_lines).encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        download_name='bills_history.csv',
        as_attachment=True
    )

# ---------- Run App ----------
if __name__ == '__main__':
    app.run(debug=True)
