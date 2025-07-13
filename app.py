from flask import Flask, render_template, request, redirect
import sqlite3
import csv

app = Flask(__name__)
DB_PATH = 'contacts.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()
    query = request.args.get('q', '')
    column = request.args.get('column', 'all')
    limit = request.args.get('limit', default=30, type=int)
    page = request.args.get('page', default=1, type=int)
    offset = (page - 1) * limit

    base_sql = "SELECT * FROM contacts"
    limit_clause = " LIMIT ? OFFSET ?"

    if query:
        if column == 'all':
            where_clause = " WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR phone LIKE ? OR last_note LIKE ?"
            rows_raw = conn.execute(
                base_sql + where_clause + limit_clause,
                (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit, offset)
            ).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) FROM contacts" + where_clause,
                (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
            ).fetchone()[0]
        else:
            where_clause = f" WHERE {column} LIKE ?"
            rows_raw = conn.execute(
                base_sql + where_clause + limit_clause,
                (f'%{query}%', limit, offset)
            ).fetchall()
            total = conn.execute(
                f"SELECT COUNT(*) FROM contacts WHERE {column} LIKE ?",
                (f'%{query}%',)
            ).fetchone()[0]
    else:
        rows_raw = conn.execute(base_sql + limit_clause, (limit, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

    conn.close()
    rows = [dict(row) for row in rows_raw]
    total_pages = (total + limit - 1) // limit

    return render_template('index.html', rows=rows, limit=limit, page=page,
                           total_pages=total_pages, query=query, column=column)

@app.route('/add', methods=['POST'])
def add():
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        INSERT OR IGNORE INTO contacts (
            contact_id, first_name, last_name, phone, email,
            last_activity, assigned, tags, last_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['contact_id'], data['first_name'], data['last_name'],
        data['phone'], data['email'], data['last_activity'],
        data['assigned'], data['tags'], data['last_note']
    ))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/edit', methods=['POST'])
def edit():
    data = request.form
    conn = get_db_connection()
    conn.execute('''
        UPDATE contacts SET
            first_name = ?,
            last_name = ?,
            phone = ?,
            email = ?,
            last_activity = ?,
            assigned = ?,
            tags = ?,
            last_note = ?
        WHERE contact_id = ?
    ''', (
        data['first_name'], data['last_name'], data['phone'], data['email'],
        data['last_activity'], data['assigned'], data['tags'], data['last_note'],
        data['contact_id']
    ))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        conn = get_db_connection()
        reader = csv.DictReader(file.stream.read().decode("utf-8").splitlines())
        for row in reader:
            conn.execute('''
                INSERT OR IGNORE INTO contacts (
                    contact_id, first_name, last_name, phone, email,
                    last_activity, assigned, tags, last_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Contact Id'), row.get('First Name'), row.get('Last Name'),
                row.get('Phone'), row.get('Email'), row.get('Last Activity'),
                row.get('Assigned'), row.get('Tags'), row.get('Last Note')
            ))
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/delete', methods=['POST'])
def delete():
    contact_id = request.form['contact_id']
    conn = get_db_connection()
    conn.execute('DELETE FROM contacts WHERE contact_id = ?', (contact_id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
