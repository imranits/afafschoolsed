"""
Afaq School - Single-file Flask app scaffold (writes templates and static files on first run)

Files created at runtime:
 - templates/*.html
 - static/uploads/ (for student pics and receipts)

Requirements:
 pip install flask pymysql python-dotenv

Configure MySQL credentials in a .env file next to this script:
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=yourpassword
DB_NAME=afaqschool
ADMIN_MOBILE=0000000000  # change to admin mobile(s), comma-separated allowed

Run:
 python afaq_school_app.py

Notes:
 - This is a starting scaffold. Improve validation, security, and file size/type checks before production.
 - Uploaded files stored under static/uploads. Make sure the folder is writable.

"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import pymysql
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_UPLOADS = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_UPLOADS, exist_ok=True)

# Write minimal templates if they don't exist
_template_files = {
    'layout.html': """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Afaq School</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <a class="navbar-brand" href="/">Afaq School</a>
        <div class="d-flex">
          {% if session.get('user') %}
            <span class="navbar-text me-2">{{ session['user']['name'] }} ({{ session['user']['role'] }})</span>
            <a class="btn btn-outline-light btn-sm" href="{{ url_for('logout') }}">Logout</a>
          {% else %}
            <a class="btn btn-outline-light btn-sm" href="{{ url_for('login') }}">Login</a>
          {% endif %}
        </div>
      </div>
    </nav>

    <div class="container py-4">
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class="alert alert-info">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      {% block content %}{% endblock %}
    </div>
  </body>
</html>""",

    'login.html': """{% extends 'layout.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Login / Register</h5>
        <form method="post" action="{{ url_for('login') }}">
          <div class="mb-3">
            <label class="form-label">Are you:</label>
            <select name="role" class="form-select">
              <option value="applicant">Applicant</option>
              <option value="donor">Donor</option>
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label">Name</label>
            <input class="form-control" name="name" required>
          </div>
          <div class="mb-3">
            <label class="form-label">Mobile Number</label>
            <input class="form-control" name="mobile" required>
          </div>
          <button class="btn btn-primary">Login / Register</button>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}""",

    'home.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Menu</h3>
<div class="d-grid gap-3 col-6">
  <a class="btn btn-lg btn-outline-primary" href="{{ url_for('new_registration') }}">New Registration</a>
  <a class="btn btn-lg btn-outline-success" href="{{ url_for('status_report') }}">Status Report</a>
  {% if session['user']['role'] == 'admin' %}
    <a class="btn btn-lg btn-outline-warning" href="{{ url_for('review_applications') }}">Review Applications</a>
  {% endif %}
  <a class="btn btn-lg btn-outline-danger" href="{{ url_for('logout') }}">Exit</a>
</div>
{% endblock %}""",

    'new_registration.html': """{% extends 'layout.html' %}
{% block content %}
<h3>New Registration</h3>
<form method="post" enctype="multipart/form-data">
  <div class="mb-3">
    <label class="form-label">Student Name</label>
    <input class="form-control" name="student_name" required>
  </div>
  <div class="mb-3">
    <label class="form-label">Age</label>
    <input class="form-control" name="age" type="number">
  </div>
  <div class="mb-3">
    <label class="form-label">Picture</label>
    <input class="form-control" name="picture" type="file" accept="image/*">
  </div>
  <button class="btn btn-primary">Submit</button>
</form>
{% endblock %}""",

    'status_report.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Status Report</h3>
<table class="table">
  <thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Action</th></tr></thead>
  <tbody>
    {% for a in apps %}
      <tr>
        <td>{{ a['id'] }}</td>
        <td>{{ a['student_name'] }}</td>
        <td>{{ a['status'] }}</td>
        <td>
          <a class="btn btn-sm btn-outline-primary" href="{{ url_for('view_application', app_id=a['id']) }}">View</a>
        </td>
      </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}""",

    'view_application.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Application #{{ app['id'] }}</h3>
<div class="row">
  <div class="col-md-4">
    {% if app['picture_path'] %}
      <img src="{{ url_for('uploaded_file', filename=app['picture_path']) }}" class="img-fluid">
    {% endif %}
  </div>
  <div class="col-md-8">
    <ul class="list-group">
      <li class="list-group-item"><strong>Name:</strong> {{ app['student_name'] }}</li>
      <li class="list-group-item"><strong>Age:</strong> {{ app['age'] }}</li>
      <li class="list-group-item"><strong>Status:</strong> {{ app['status'] }}</li>
      {% if app['status'] == 'approved' and session['user']['role'] == 'donor' %}
        <li class="list-group-item">
          <a class="btn btn-success" href="{{ url_for('choose_for_donation', app_id=app['id']) }}">Choose</a>
        </li>
      {% endif %}
    </ul>
  </div>
</div>
{% endblock %}""",

    'review_applications.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Review Applications</h3>
<table class="table">
  <thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Action</th></tr></thead>
  <tbody>
    {% for a in apps %}
      <tr>
        <td>{{ a['id'] }}</td>
        <td>{{ a['student_name'] }}</td>
        <td>{{ a['status'] }}</td>
        <td>
          <a class="btn btn-sm btn-primary" href="{{ url_for('approve_app', app_id=a['id']) }}">Approve</a>
          <a class="btn btn-sm btn-danger" href="{{ url_for('disapprove_app', app_id=a['id']) }}">Disapprove</a>
        </td>
      </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}""",

    'assign_class.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Assign Class / Costs for {{ app['student_name'] }}</h3>
<form method="post">
  <div class="mb-3"><label class="form-label">Class</label><input class="form-control" name="assigned_class" required></div>
  <div class="mb-3"><label class="form-label">Section</label><input class="form-control" name="section"></div>
  <div class="mb-3"><label class="form-label">Book Cost</label><input class="form-control" name="cost_book" type="number" step="0.01"></div>
  <div class="mb-3"><label class="form-label">Fee</label><input class="form-control" name="cost_fee" type="number" step="0.01"></div>
  <div class="mb-3"><label class="form-label">Uniform</label><input class="form-control" name="cost_uniform" type="number" step="0.01"></div>
  <button class="btn btn-primary">Save</button>
</form>
{% endblock %}""",

    'donor_list.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Approved Applications (Choose to Sponsor)</h3>
<table class="table">
  <thead><tr><th>ID</th><th>Name</th><th>Class</th><th>Total</th><th>Action</th></tr></thead>
  <tbody>
    {% for a in apps %}
      <tr>
        <td>{{ a['id'] }}</td>
        <td>{{ a['student_name'] }}</td>
        <td>{{ a.get('assigned_class','-') }}</td>
        <td>{{ a.get('total_cost', '-') }}</td>
        <td><a class="btn btn-sm btn-primary" href="{{ url_for('view_application', app_id=a['id']) }}">View</a></td>
      </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}""",

    'donate.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Donate for {{ app['student_name'] }}</h3>
<p>Total: {{ app['total_cost'] }}</p>
<form method="post" enctype="multipart/form-data">
  <div class="mb-3">
    <label class="form-label">Upload Payment Receipt</label>
    <input class="form-control" name="receipt" type="file" accept="image/*,application/pdf" required>
  </div>
  <button class="btn btn-success">Upload & Confirm</button>
</form>
{% endblock %}""",

    'verify_payments.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Verify Payments</h3>
<table class="table">
  <thead><tr><th>ID</th><th>Application</th><th>Donor</th><th>Receipt</th><th>Action</th></tr></thead>
  <tbody>
    {% for p in payments %}
      <tr>
        <td>{{ p['id'] }}</td>
        <td>{{ p['app_name'] }}</td>
        <td>{{ p['donor_name'] }}</td>
        <td>{% if p['receipt_path'] %}<a href="{{ url_for('uploaded_file', filename=p['receipt_path']) }}" target="_blank">View</a>{% endif %}</td>
        <td>
          <a class="btn btn-sm btn-success" href="{{ url_for('confirm_payment', payment_id=p['id']) }}">Confirm</a>
        </td>
      </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}""",
}

for name, content in _template_files.items():
    path = os.path.join(TEMPLATES_DIR, name)
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

# Load env
load_dotenv()
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'Zain12345')
DB_NAME = os.getenv('DB_NAME', 'afaqschool')
ADMIN_MOBILE = os.getenv('ADMIN_MOBILE', '0000000000')
ADMIN_MOBILES = [m.strip() for m in ADMIN_MOBILE.split(',') if m.strip()]

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-123')
app.template_folder = TEMPLATES_DIR
app.config['UPLOAD_FOLDER'] = STATIC_UPLOADS

# --- Database utilities ---

def get_db_connection():
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME,
                           cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    return conn

# Create tables if not exist
def init_db():
    conn = None
    try:
        # connect without database to create DB if not exists
        tmp = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, cursorclass=pymysql.cursors.DictCursor)
        with tmp.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        tmp.close()
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200),
                mobile VARCHAR(30) UNIQUE,
                role ENUM('applicant','donor','admin') DEFAULT 'applicant',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''')
            cur.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                student_name VARCHAR(200),
                age INT,
                picture_path VARCHAR(500),
                status ENUM('pending','approved','disapproved','assigned','chosen','donated','confirmed') DEFAULT 'pending',
                assigned_class VARCHAR(50),
                section VARCHAR(10),
                cost_book DECIMAL(10,2) DEFAULT 0,
                cost_fee DECIMAL(10,2) DEFAULT 0,
                cost_uniform DECIMAL(10,2) DEFAULT 0,
                total_cost DECIMAL(12,2) DEFAULT 0,
                donor_id INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''')
            cur.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application_id INT,
                donor_id INT,
                receipt_path VARCHAR(500),
                confirmed ENUM('pending','confirmed') DEFAULT 'pending',
                confirmed_by INT DEFAULT NULL,
                confirmed_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''')
    except Exception as e:
        print('DB init error:', e)
    finally:
        if conn:
            conn.close()

init_db()

# --- Helpers ---

def get_or_create_user(name, mobile, role):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE mobile=%s', (mobile,))
            user = cur.fetchone()
            if user:
                return user
            # create
            r = 'admin' if mobile in ADMIN_MOBILES else role
            cur.execute('INSERT INTO users (name, mobile, role) VALUES (%s,%s,%s)', (name, mobile, r))
            cur.execute('SELECT * FROM users WHERE id=LAST_INSERT_ID()')
            return cur.fetchone()
    finally:
        conn.close()

# route: uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Routes ---
@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        role = request.form.get('role', 'applicant')
        user = get_or_create_user(name, mobile, role)
        session['user'] = {'id': user['id'], 'name': user['name'], 'mobile': user['mobile'], 'role': user['role']}
        flash('Logged in as ' + user['name'])
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out')
    return redirect(url_for('login'))

@app.route('/new_registration', methods=['GET','POST'])
def new_registration():
    if not session.get('user'):
        return redirect(url_for('login'))
    if session['user']['role'] not in ['applicant','admin']:
        flash('Only applicants can register new students')
        return redirect(url_for('index'))
    if request.method == 'POST':
        student_name = request.form['student_name']
        age = request.form.get('age')
        pic = request.files.get('picture')
        pic_path = None
        if pic and pic.filename:
            fname = secure_filename(pic.filename)
            dest = f"{session['user']['mobile']}_student_{fname}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], dest)
            pic.save(save_path)
            pic_path = dest
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO applications (user_id, student_name, age, picture_path) VALUES (%s,%s,%s,%s)''',
                            (session['user']['id'], student_name, age or None, pic_path))
            flash('Application submitted')
            return redirect(url_for('status_report'))
        finally:
            conn.close()
    return render_template('new_registration.html')

@app.route('/status_report')
def status_report():
    if not session.get('user'):
        return redirect(url_for('login'))
    uid = session['user']['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if session['user']['role'] == 'admin':
                cur.execute('SELECT * FROM applications ORDER BY created_at DESC')
            else:
                cur.execute('SELECT * FROM applications WHERE user_id=%s ORDER BY created_at DESC', (uid,))
            apps = cur.fetchall()
    finally:
        conn.close()
    return render_template('status_report.html', apps=apps)

@app.route('/application/<int:app_id>')
def view_application(app_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM applications WHERE id=%s', (app_id,))
            apprec = cur.fetchone()
            if not apprec:
                flash('Application not found')
                return redirect(url_for('index'))
    finally:
        conn.close()
    return render_template('view_application.html', app=apprec)

# Admin review
@app.route('/review_applications')
def review_applications():
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM applications WHERE status='pending' ORDER BY created_at DESC")
            apps = cur.fetchall()
    finally:
        conn.close()
    return render_template('review_applications.html', apps=apps)

@app.route('/approve/<int:app_id>')
def approve_app(app_id):
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE applications SET status='approved' WHERE id=%s", (app_id,))
    finally:
        conn.close()
    flash('Application approved. Assign class & costs.')
    return redirect(url_for('assign_class', app_id=app_id))

@app.route('/disapprove/<int:app_id>')
def disapprove_app(app_id):
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE applications SET status='disapproved' WHERE id=%s", (app_id,))
    finally:
        conn.close()
    flash('Application disapproved')
    return redirect(url_for('review_applications'))

@app.route('/assign/<int:app_id>', methods=['GET','POST'])
def assign_class(app_id):
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM applications WHERE id=%s', (app_id,))
            apprec = cur.fetchone()
            if not apprec:
                flash('Not found')
                return redirect(url_for('review_applications'))
            if request.method == 'POST':
                assigned_class = request.form['assigned_class']
                section = request.form.get('section')
                cost_book = float(request.form.get('cost_book') or 0)
                cost_fee = float(request.form.get('cost_fee') or 0)
                cost_uniform = float(request.form.get('cost_uniform') or 0)
                total = cost_book + cost_fee + cost_uniform
                cur.execute('''UPDATE applications SET status='assigned', assigned_class=%s, section=%s, cost_book=%s, cost_fee=%s, cost_uniform=%s, total_cost=%s WHERE id=%s''',
                            (assigned_class, section, cost_book, cost_fee, cost_uniform, total, app_id))
                flash('Assigned with costs')
                return redirect(url_for('review_applications'))
    finally:
        conn.close()
    return render_template('assign_class.html', app=apprec)

# Donor side: list approved/assigned
@app.route('/donor_list')
def donor_list():
    if not session.get('user') or session['user']['role'] not in ['donor','admin']:
        flash('Donors only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM applications WHERE status IN ('assigned','approved') ORDER BY created_at DESC")
            apps = cur.fetchall()
    finally:
        conn.close()
    return render_template('donor_list.html', apps=apps)

@app.route('/choose/<int:app_id>')
def choose_for_donation(app_id):
    # mark chosen by donor and redirect to payment upload
    if not session.get('user') or session['user']['role'] != 'donor':
        flash('Donors only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE applications SET status=%s, donor_id=%s WHERE id=%s', ('chosen', session['user']['id'], app_id))
    finally:
        conn.close()
    return redirect(url_for('donate', app_id=app_id))

@app.route('/donate/<int:app_id>', methods=['GET','POST'])
def donate(app_id):
    if not session.get('user') or session['user']['role'] != 'donor':
        flash('Donors only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM applications WHERE id=%s', (app_id,))
            apprec = cur.fetchone()
            if not apprec:
                flash('Not found')
                return redirect(url_for('donor_list'))
            if request.method == 'POST':
                receipt = request.files.get('receipt')
                if receipt and receipt.filename:
                    fname = secure_filename(receipt.filename)
                    dest = f"donor_{session['user']['mobile']}_receipt_{fname}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], dest)
                    receipt.save(save_path)
                    with conn.cursor() as cur2:
                        cur2.execute('INSERT INTO payments (application_id, donor_id, receipt_path) VALUES (%s,%s,%s)', (app_id, session['user']['id'], dest))
                        # mark application as donated (awaiting confirmation)
                        cur2.execute("UPDATE applications SET status='donated', donor_id=%s WHERE id=%s", (session['user']['id'], app_id))
                    flash('Receipt uploaded. Awaiting admin verification.')
                    return redirect(url_for('donor_list'))
    finally:
        conn.close()
    return render_template('donate.html', app=apprec)

# Admin: verify pending payments
@app.route('/verify_payments')
def verify_payments():
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT p.*, a.student_name as app_name, u.name as donor_name FROM payments p
                           LEFT JOIN applications a ON a.id=p.application_id
                           LEFT JOIN users u ON u.id=p.donor_id
                           WHERE p.confirmed='pending' ORDER BY p.created_at DESC''')
            payments = cur.fetchall()
    finally:
        conn.close()
    return render_template('verify_payments.html', payments=payments)

@app.route('/confirm_payment/<int:payment_id>')
def confirm_payment(payment_id):
    if not session.get('user') or session['user']['role'] != 'admin':
        flash('Admin only')
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # mark payment confirmed
            cur.execute("UPDATE payments SET confirmed='confirmed', confirmed_by=%s, confirmed_at=NOW() WHERE id=%s", (session['user']['id'], payment_id))
            # also mark application as confirmed
            cur.execute('SELECT application_id, donor_id FROM payments WHERE id=%s', (payment_id,))
            p = cur.fetchone()
            if p:
                cur.execute("UPDATE applications SET status='confirmed', donor_id=%s WHERE id=%s", (p['donor_id'], p['application_id']))
    finally:
        conn.close()
    flash('Payment confirmed')
    return redirect(url_for('verify_payments'))

import base64
import os
from flask import Flask, render_template, request, redirect, url_for, flash

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # change if different
        password="Zain12345",        # your MySQL password
        database="afaqschool"  # your DB name
    )



# Generate next Application No
def get_next_application_no():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT MAX(id) as max_id FROM applications")
    row = cursor.fetchone()
    conn.close()
    next_no = 1 if not row["max_id"] else row["max_id"] + 1
    return f"APP-{next_no:04d}"  # e.g. APP-0001, APP-0002


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_name = request.form["student_name"]
        father_name = request.form["father_name"]
        dob = request.form["dob"]
        age = request.form.get("age")
        student_class = request.form.get("class")
        sabika_school = request.form.get("sabika_school")
        father_cnic = request.form.get("father_cnic")
        mobile_no = request.form["mobile_no"]
        father_income = request.form.get("father_income")
        loss_flood = request.form.get("loss_flood")
        donation_percentage = request.form.get("donation_percentage")

        # Handle picture
        picture_data = None
        if request.form.get("captured_image"):
            picture_data = base64.b64decode(request.form["captured_image"].split(",")[1])
        elif "picture" in request.files and request.files["picture"]:
            file = request.files["picture"]
            picture_data = file.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        # First insert row without application_no
        cursor.execute("""
            INSERT INTO applications
            (student_name, father_name, dob, age, class, sabika_school,
             father_cnic, mobile_no, father_income, loss_flood, donation_percentage, picture)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            student_name, father_name, dob, age, student_class, sabika_school,
            father_cnic, mobile_no, father_income, loss_flood, donation_percentage, picture_data
        ))
        app_id = cursor.lastrowid   # auto-incremented id

        # Generate application_no based on id
        application_no = f"APP-{app_id:03d}"

        # Update row with application_no
        cursor.execute("UPDATE applications SET application_no=%s WHERE id=%s", (application_no, app_id))
        conn.commit()
        conn.close()

        flash(f"Registration successful! Your Reference No is: {application_no}", "success")
        return redirect(url_for("register"))

    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)
