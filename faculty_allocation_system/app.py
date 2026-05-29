# app.py - Main Flask Application Entry Point
# ============================================
# Run with: python app.py
# Open browser: http://localhost:5001
#
# FIRST TIME SETUP (after importing schema.sql into phpMyAdmin):
#   Visit http://localhost:5001/setup  — creates admin & faculty accounts

import os
from flask import Flask, redirect, url_for, render_template
from config import Config

# ---- Initialize Flask app ----
app = Flask(__name__)
app.config.from_object(Config)

# Create exports folder if needed
os.makedirs(app.config.get('EXPORT_FOLDER', 'exports'), exist_ok=True)

# ---- Initialize MySQL ----
from modules.db import mysql
mysql.init_app(app)

# ---- Register Blueprints ----
from modules.auth           import auth
from modules.admin_routes   import admin
from modules.faculty_routes import faculty_bp

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(faculty_bp)

# ---- Root → login ----
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# ============================================================
# FIRST-RUN SETUP ROUTE
# Visit http://localhost:5001/setup ONCE after importing SQL.
# Creates admin and 3 sample faculty accounts.
# ============================================================
@app.route('/setup')
def setup():
    from werkzeug.security import generate_password_hash
    try:
        cur = mysql.connection.cursor()

        # Check if already set up
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        count = cur.fetchone()['cnt']
        if count > 0:
            cur.close()
            return render_template('setup_done.html',
                                   message='Setup already complete! Users exist.',
                                   already_done=True)

        # Create admin user
        admin_hash = generate_password_hash('admin123')
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
            ('admin', admin_hash)
        )

        # Create 3 faculty users
        fac_hash = generate_password_hash('faculty123')
        # max_workload=8 so all 6 subjects × 2 classes can be distributed
        # All 5 days available — prevents solver from running out of slots
        faculty_data = [
            ('faculty1', 'Dr. Priya Sharma',  'priya.sharma@college.edu',  'Computer Science', 8,  8, 'Mon,Tue,Wed,Thu,Fri'),
            ('faculty2', 'Prof. Raj Kumar',   'raj.kumar@college.edu',     'Computer Science', 5,  8, 'Mon,Tue,Wed,Thu,Fri'),
            ('faculty3', 'Dr. Anita Patel',   'anita.patel@college.edu',   'Computer Science', 12, 8, 'Mon,Tue,Wed,Thu,Fri'),
        ]

        for username, name, email, dept, exp, workload, days in faculty_data:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'faculty')",
                (username, fac_hash)
            )
            uid = cur.lastrowid
            cur.execute("""
                INSERT INTO faculty
                    (user_id, name, email, department, experience_years, max_workload, available_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (uid, name, email, dept, exp, workload, days))

        mysql.connection.commit()
        cur.close()

        return render_template('setup_done.html',
                               message='Setup complete! All accounts created.',
                               already_done=False)

    except Exception as e:
        return render_template('setup_done.html',
                               message=f'Error: {str(e)}',
                               already_done=False)

# ---- Run the app ----
if __name__ == '__main__':
    print("=" * 60)
    print("  Faculty Allocation & Timetable System")
    print("  1. Make sure XAMPP MySQL is running")
    print("  2. Import database/schema.sql into phpMyAdmin")
    print("  3. Open: http://localhost:5001/setup  (first time only)")
    print("  4. Then login at: http://localhost:5001")
    print("  Admin: admin / admin123")
    print("  Faculty: faculty1 / faculty123")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
