from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file
import mysql.connector
import os
import base64
from mysql.connector import Binary
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ==== CONFIG ====
# Use environment variables with fallbacks
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "Zain12345"),
    "database": os.getenv("DB_NAME", "afaqschool1")
}

# Set secret key from environment
app.secret_key = os.getenv("SECRET_KEY", "supersecret123")

# Set upload folders
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
RECEIPT_FOLDER = os.getenv("RECEIPT_FOLDER", "static/receipts")

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECEIPT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RECEIPT_FOLDER"] = RECEIPT_FOLDER

# Admin password from environment
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")

# ==== HELPERS ====
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise

def get_next_application_no():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(id) FROM applications")
        max_id = cursor.fetchone()[0] or 0
        return f"APP-{max_id+1:04d}"
    finally:
        cursor.close()
        conn.close()

# ==== ROUTES ====

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        password = request.form.get("password")

        if role == "admin":
            if password == ADMIN_PASSWORD:
                session["user"] = {
                    "role": "admin",
                    "name": name or "Admin",
                    "mobile": ""
                }
                flash("Admin login successful", "success")
                return redirect(url_for("home"))
            else:
                flash("Invalid admin password", "danger")
                return render_template("login.html")
        else:
            if not name or not mobile:
                flash("Please enter name and mobile", "danger")
                return render_template("login.html")

            session["user"] = {
                "role": role,
                "name": name,
                "mobile": mobile
            }
            flash(f"{role.capitalize()} login successful", "success")
            return redirect(url_for("home"))

    return render_template("login.html")


# HOME
@app.route("/home")
def home():
    if not session.get("user"):
        flash("براہ کرم پہلے لاگ ان کریں", "warning")
        return redirect(url_for("login"))
    user = session["user"]
    return render_template("home.html", user=user)


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))


# NEW REGISTRATION
@app.route("/new_registration", methods=["GET", "POST"])
def new_registration():
    if not session.get("user"):
        return redirect(url_for("login"))

    application_no = get_next_application_no()

    if request.method == "POST":
        student_name = request.form["student_name"]
        father_name = request.form["father_name"]
        dob = request.form["dob"]
        age = request.form.get("age")
        class_name = request.form.get("class")
        sabika_school = request.form.get("sabika_school")
        father_cnic = request.form.get("father_cnic")
        mobile = request.form["mobile_no"]
        monthly_income = request.form.get("father_income")
        loss_flood = request.form.get("loss_flood")
        donation_percent = request.form.get("donation_percentage")
        is_orphan = request.form.get("is_orphan")

        picture_data = None
        picture = request.files.get("picture")
        if picture and picture.filename != "":
            picture_data = picture.read()

        captured_image = request.form.get("captured_image")
        if not picture_data and captured_image:
            header, encoded = captured_image.split(",", 1)
            picture_data = base64.b64decode(encoded)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO applications
                (application_no, student_name, father_name, dob, age, class, sabika_school,
                 father_cnic, mobile_no, father_income, is_orphan, loss_flood, donation_percentage,
                 picture, status, user_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                application_no,
                student_name,
                father_name,
                dob,
                age,
                class_name,
                sabika_school,
                father_cnic,
                mobile,
                monthly_income,
                is_orphan,
                loss_flood,
                donation_percent,
                Binary(picture_data) if picture_data else None,
                "Pending",
                "1"
            ))
            conn.commit()
            flash(f"Application submitted successfully! Your Application No is {application_no}")
            return redirect(url_for("status_report"))
        except Exception as e:
            conn.rollback()
            flash(f"Error submitting application: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("new_registration.html", application_no=application_no)

# ... (rest of your routes remain the same)
# I'll include the key routes but you can copy the rest from your original app.py

@app.route("/donor")
def donor_dashboard():
    if "user" not in session or session["user"]["role"] != "donor":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT a.application_no, a.student_name, a.father_name, s.class_name, s.section, s.total
            FROM applications a
            JOIN students s ON a.application_no = s.application_no
            WHERE a.status = 'Approved'
        """)
        approved_apps = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return render_template("donor_dashboard.html", applications=approved_apps)

# STATUS REPORT
@app.route('/status_report', methods=["GET", "POST"])
def status_report():
    if not session.get('user'):
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    # Get filter values from form/query
    status_filter = request.args.get("status", "All")
    student_filter = request.args.get("student", "").strip()
    class_filter = request.args.get("class", "").strip()
    age_filter = request.args.get("age", "").strip()

    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            query = "SELECT * FROM applications WHERE 1=1"
            params = []

            # Role based filter: non-admins see only their applications
            if session['user']['role'] != 'admin':
                query += " AND mobile_no=%s"
                params.append(session['user']['mobile'])

            # Apply filters
            if status_filter != "All":
                query += " AND status=%s"
                params.append(status_filter)
            if student_filter:
                query += " AND student_name LIKE %s"
                params.append(f"%{student_filter}%")
            if class_filter:
                query += " AND class LIKE %s"
                params.append(f"%{class_filter}%")
            if age_filter:
                query += " AND age=%s"
                params.append(age_filter)

            query += " ORDER BY created_at DESC"
            cur.execute(query, tuple(params))
            apps = cur.fetchall()
    finally:
        conn.close()

    return render_template('status_report.html',
                           apps=apps,
                           status_filter=status_filter,
                           student_filter=student_filter,
                           class_filter=class_filter,
                           age_filter=age_filter)

# IMAGE SERVE
@app.route("/image/<application_no>")
def get_image(application_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT picture FROM applications WHERE application_no=%s", (application_no,))
        row = cursor.fetchone()
        if row and row[0]:
            return send_file(BytesIO(row[0]), mimetype="image/jpeg")
        return "No image", 404
    finally:
        cursor.close()
        conn.close()

# ==== MAIN ====
if __name__ == "__main__":
    # Only run in debug mode if explicitly set
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
