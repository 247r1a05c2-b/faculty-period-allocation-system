# app.py - Faculty Allocation & Timetable System
import os
from flask import Flask, redirect, url_for, render_template
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config.get('EXPORT_FOLDER', 'exports'), exist_ok=True)

from modules.db import mysql
mysql.init_app(app)

from modules.auth import auth
from modules.admin_routes import admin
from modules.faculty_routes import faculty_bp
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(faculty_bp)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.route('/health')
def health():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT 1 AS ok')
        cur.fetchone()
        cur.close()
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as exc:
        return {'status': 'error', 'database': 'unavailable', 'detail': str(exc)}, 503

@app.route('/setup')
def setup():
    from werkzeug.security import generate_password_hash
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(*) AS cnt FROM users')
        count = cur.fetchone()['cnt']
        if count > 0:
            cur.close()
            return render_template('setup_done.html', message='Setup already complete! Users exist.', already_done=True)

        admin_hash = generate_password_hash('admin123')
        cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin') RETURNING id", ('admin', admin_hash))

        fac_hash = generate_password_hash('faculty123')
        faculty_data = [
            ('faculty1', 'Dr. Priya Sharma', 'priya.sharma@college.edu', 'Computer Science', 8, 8, 'Mon,Tue,Wed,Thu,Fri'),
            ('faculty2', 'Prof. Raj Kumar', 'raj.kumar@college.edu', 'Computer Science', 5, 8, 'Mon,Tue,Wed,Thu,Fri'),
            ('faculty3', 'Dr. Anita Patel', 'anita.patel@college.edu', 'Computer Science', 12, 8, 'Mon,Tue,Wed,Thu,Fri'),
        ]
        for username, name, email, dept, exp, workload, days in faculty_data:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'faculty') RETURNING id", (username, fac_hash))
            uid = cur.fetchone()['id']
            cur.execute("""INSERT INTO faculty (user_id, name, email, department, experience_years, max_workload, available_days)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""", (uid, name, email, dept, exp, workload, days))
        mysql.connection.commit()
        cur.close()
        return render_template('setup_done.html', message='Setup complete! All accounts created.', already_done=False)
    except Exception as e:
        mysql.connection.rollback()
        return render_template('setup_done.html', message=f'Error: {str(e)}', already_done=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
