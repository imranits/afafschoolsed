from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file
import mysql.connector
import os
import base64
from mysql.connector import Binary
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecret123"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "SecureRootPass123!",
    "database": "afaqschool1"
}



UPLOAD_FOLDER = "static/uploads"
RECEIPT_FOLDER = "static/receipts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RECEIPT_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RECEIPT_FOLDER"] = RECEIPT_FOLDER

ADMIN_PASSWORD = "admin12345"

# ==== HELPERS ====
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_next_application_no():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM applications")
    max_id = cursor.fetchone()[0] or 0
    cursor.close()
    conn.close()
    return f"APP-{max_id+1:04d}"

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

@app.route("/", methods=["GET", "POST"])
def login2():
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
        is_orphan = request.form.get("is_orphan")  # ✅ New Field

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
            is_orphan,   # ✅ Insert new field
            loss_flood,
            donation_percent,
            Binary(picture_data) if picture_data else None,
            "Pending",
            "1"
        ))
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Application submitted successfully! Your Application No is {application_no}")
        return redirect(url_for("status_report"))

    return render_template("new_registration.html", application_no=application_no)

@app.route("/donor")
def donor_dashboard():
    if "user" not in session or session["user"]["role"] != "donor":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.application_no, a.student_name, a.father_name, s.class_name, s.section, s.total
        FROM applications a
        JOIN students s ON a.application_no = s.application_no
        WHERE a.status = 'Approved'
    """)
    approved_apps = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("donor_dashboard.html", applications=approved_apps)

@app.route("/donor/view/<application_no>")
def donor_view(application_no):
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*,s.class_name, s.section, s.fee, s.books, s.uniform, s.total
        FROM applications a
        JOIN students s ON a.application_no = s.application_no
        WHERE a.application_no = %s
    """, (application_no,))
    application = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("donor_view.html", app=application)

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/receipts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/donor/confirm/<application_no>", methods=["GET", "POST"])
def donor_confirm(application_no):
    if "user" not in session or session["user"]["role"] != "donor":
        flash("Please login as a donor first.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("receipt")
        if not file:
            flash("Please upload a receipt.", "danger")
            return redirect(request.url)

        # Save receipt with application_no prefix
        filename = secure_filename(application_no + "_" + file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Insert donation + update application status
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Insert into donations table
            cursor.execute("""
                INSERT INTO donations (application_no, name, receipt_path)
                VALUES (%s, %s, %s)
            """, (
                application_no,
                session["user"]["name"],  # donor name
                filename
            ))

            # Update application status
            cursor.execute("""
                UPDATE applications
                SET status = 'Assigned'
                WHERE application_no = %s
            """, (application_no,))

            conn.commit()
            flash("Donation confirmed, receipt uploaded, and application assigned successfully!", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error: {str(e)}", "danger")

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("donor_dashboard"))

    return render_template("donor_confirm.html", application_no=application_no)

import pandas as pd
from flask import request, send_file
from io import BytesIO

@app.route("/donor_assignments", methods=["GET", "POST"])
def donor_assignments():
    if "user" not in session or session["user"]["role"] != "admin":
        flash("Admins only.", "warning")
        return redirect(url_for("login"))

    # Filters
    student_name = request.args.get("student_name", "").strip()
    donor_name = request.args.get("donor_name", "").strip()
    application_no = request.args.get("application_no", "").strip()

    query = """
        SELECT a.application_no, a.student_name, a.father_name,
               d.name AS donor_name, u.mobile AS donor_mobile, d.receipt_path,
               a.status, d.created_at
        FROM applications a
        JOIN donations d ON a.application_no = d.application_no
        LEFT JOIN users u ON d.donor_id = u.id
        WHERE 1=1
    """
    params = []

    if student_name:
        query += " AND a.student_name LIKE %s"
        params.append(f"%{student_name}%")
    if donor_name:
        query += " AND d.name LIKE %s"
        params.append(f"%{donor_name}%")
    if application_no:
        query += " AND a.application_no LIKE %s"
        params.append(f"%{application_no}%")

    query += " ORDER BY d.created_at DESC"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Export to Excel if requested
    if request.args.get("export") == "excel":
        df = pd.DataFrame(rows)
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return send_file(
            output,
            download_name="donor_assignments.xlsx",
            as_attachment=True
        )

    return render_template("donor_assignments.html", rows=rows,
                           student_name=student_name,
                           donor_name=donor_name,
                           application_no=application_no)



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


# VIEW APPLICATION
@app.route('/application/<int:app_id>')
def view_application(app_id):
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute('SELECT * FROM applications WHERE id=%s', (app_id,))
            apprec = cur.fetchone()
            if not apprec:
                flash('Application not found')
                return redirect(url_for('home'))
    finally:
        conn.close()
    return render_template('view_application.html', app=apprec)


# ADMIN REVIEW
@app.route("/review")
def review():
    if not session.get("user") or session['user']['role'] != "admin":
        flash("Access denied")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM applications WHERE status='Pending'")
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("review_applications.html", applications=applications)


# IMAGE SERVE
@app.route("/image/<application_no>")
def get_image(application_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT picture FROM applications WHERE application_no=%s", (application_no,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row[0]:
        return send_file(BytesIO(row[0]), mimetype="image/jpeg")
    return "No image", 404


# REVIEW DETAIL
@app.route("/review/<application_no>")
def review_detail(application_no):
    if not session.get("user") or session['user']['role'] != "admin":
        flash("Access denied")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM applications WHERE application_no=%s", (application_no,))
    app_detail = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("review_detail.html", app=app_detail)


# APPROVE / REJECT
@app.route("/approve/<application_no>", methods=["POST"])
def approve_application(application_no):
    if not session.get("user") or session['user']['role'] != "admin":
        flash("Access denied")
        return redirect(url_for("home"))

    class_name = request.form["class_name"]
    section = request.form["section"]
    fee = request.form["fee"]
    books = request.form["books"]
    uniform = request.form["uniform"]
    total = request.form["total"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status='Approved' WHERE application_no=%s", (application_no,))
    cursor.execute("""
        INSERT INTO students (application_no, class_name, section, fee, books, uniform, total)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (application_no, class_name, section, fee, books, uniform, total))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Application approved successfully!", "success")
    return redirect(url_for("review"))

# ---------------- Export to Excel ----------------
from flask import current_app

@app.route("/export_excel")
def export_excel():
    try:
        if "user" not in session or session["user"]["role"] != "admin":
            flash("براہ کرم پہلے لاگ ان کریں", "warning")
            return redirect(url_for("login"))

        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM applications", conn)
        conn.close()

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Applications")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="applications.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        # 🔥 Log error to terminal
        current_app.logger.error(f"Excel export failed: {e}")
        return f"❌ Export failed: {e}", 500


# ---------------- Export to PDF ----------------



@app.route("/reject/<application_no>", methods=["POST"])
def reject_application(application_no):
    if not session.get("user") or session['user']['role'] != "admin":
        flash("Access denied")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status='Rejected' WHERE application_no=%s", (application_no,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Application rejected!", "danger")
    return redirect(url_for("review"))


# REPORT WITH FILTERS
@app.route("/report", methods=["GET", "POST"])
def report():
    if not session.get("user"):
        flash("Please login first", "warning")
        return redirect(url_for("login"))

    status_filter = request.args.get("status", "All")
    student_filter = request.args.get("student_filter", "").strip()
    class_filter = request.args.get("class_filter", "").strip()
    age_filter = request.args.get("age_filter", "").strip()
    income_filter = request.args.get("income_filter", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM applications WHERE 1=1"
    params = []

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
    if income_filter:
        query += " AND father_income >= %s"
        params.append(income_filter)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, tuple(params))
    applications = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("report.html", applications=applications, status_filter=status_filter)


# ==== MAIN ====
if __name__ == "__main__":
    app.run(debug=True, port=5001)
