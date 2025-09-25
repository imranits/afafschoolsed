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
ADMIN_PASSWORD=secret123   # hardcoded admin password

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
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Afaq School</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  </head>
  <body class=\"bg-light\">
    <nav class=\"navbar navbar-expand-lg navbar-dark bg-primary\">
      <div class=\"container-fluid\">
        <a class=\"navbar-brand\" href=\"/\">Afaq School</a>
        <div class=\"d-flex\">
          {% if session.get('user') %}
            <span class=\"navbar-text me-2\">{{ session['user']['name'] }} ({{ session['user']['role'] }})</span>
            <a class=\"btn btn-outline-light btn-sm\" href=\"{{ url_for('logout') }}\">Logout</a>
          {% else %}
            <a class=\"btn btn-outline-light btn-sm\" href=\"{{ url_for('login') }}\">Login</a>
          {% endif %}
        </div>
      </div>
    </nav>

    <div class=\"container py-4\">
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class=\"alert alert-info\">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      {% block content %}{% endblock %}
    </div>
  </body>
</html>""",

    'login.html': """{% extends 'layout.html' %}
{% block content %}
<div class=\"row justify-content-center\">
  <div class=\"col-md-6\">
    <div class=\"card\">
      <div class=\"card-body\">
        <h5 class=\"card-title\">Login</h5>
        <form method=\"post\" action=\"{{ url_for('login') }}\">
          <div class=\"mb-3\">
            <label class=\"form-label\">Role</label>
            <select name=\"role\" id=\"roleSelect\" class=\"form-select\" required>
              <option value=\"applicant\">Applicant</option>
              <option value=\"donor\">Donor</option>
              <option value=\"admin\">Admin</option>
            </select>
          </div>
          <div class=\"mb-3\" id=\"nameField\">
            <label class=\"form-label\">Name</label>
            <input class=\"form-control\" name=\"name\" required>
          </div>
          <div class=\"mb-3\" id=\"mobileField\">
            <label class=\"form-label\">Mobile Number</label>
            <input class=\"form-control\" name=\"mobile\">
          </div>
          <div class=\"mb-3\" id=\"passwordField\" style=\"display:none;\">
            <label class=\"form-label\">Password</label>
            <input type=\"password\" name=\"password\" class=\"form-control\">
          </div>
          <button class=\"btn btn-primary\">Login</button>
        </form>
      </div>
    </div>
  </div>
</div>
<script>
function toggleFields() {
  let role = document.getElementById(\"roleSelect\").value;
  let nameField = document.getElementById(\"nameField\");
  let mobileField = document.getElementById(\"mobileField\");
  let passwordField = document.getElementById(\"passwordField\");
  if (role === \"admin\") {
    mobileField.style.display = \"none\";
    passwordField.style.display = \"block\";
    passwordField.querySelector('input').setAttribute('required', 'required');
    mobileField.querySelector('input').removeAttribute('required');
  } else {
    mobileField.style.display = \"block\";
    passwordField.style.display = \"none\";
    passwordField.querySelector('input').removeAttribute('required');
    mobileField.querySelector('input').setAttribute('required', 'required');
  }
}
document.addEventListener(\"DOMContentLoaded\", toggleFields);
document.getElementById(\"roleSelect\").addEventListener(\"change\", toggleFields);
</script>
{% endblock %}""",

    'home.html': """{% extends 'layout.html' %}
{% block content %}
<h3>Menu</h3>
<div class=\"d-grid gap-3 col-6\">
  <a class=\"btn btn-lg btn-outline-primary\" href=\"{{ url_for('new_registration') }}\">New Registration</a>
  <a class=\"btn btn-lg btn-outline-success\" href=\"{{ url_for('status_report') }}\">Status Report</a>
  {% if session['user']['role'] == 'admin' %}
    <a class=\"btn btn-lg btn-outline-warning\" href=\"{{ url_for('review_applications') }}\">Review Applications</a>
    <a class=\"btn btn-lg btn-outline-info\" href=\"{{ url_for('verify_payments') }}\">Verify Payments</a>
  {% endif %}
  {% if session['user']['role'] == 'donor' %}
    <a class=\"btn btn-lg btn-outline-success\" href=\"{{ url_for('donor_list') }}\">Sponsor a Student</a>
  {% endif %}
  <a class=\"btn btn-lg btn-outline-danger\" href=\"{{ url_for('logout') }}\">Exit</a>
</div>
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
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'afaqschool')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'secret123')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-123')
app.template_folder = TEMPLATES_DIR
app.config['UPLOAD_FOLDER'] = STATIC_UPLOADS

# --- Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        if role == 'admin':
            if password == ADMIN_PASSWORD:
                session['user'] = {'name': name or 'Admin', 'role': 'admin'}
                flash('Admin login successful')
                return redirect(url_for('home'))
            else:
                flash('Invalid admin password')
                return redirect(url_for('login'))
        else:
            if not name or not mobile:
                flash('Please enter your name and mobile')
                return redirect(url_for('login'))
            session['user'] = {'name': name, 'mobile': mobile, 'role': role}
            flash(f'{role.capitalize()} login successful')
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
