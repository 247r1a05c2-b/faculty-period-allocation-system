# modules/auth.py - Authentication Routes
# ----------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps
from modules.db import mysql

auth = Blueprint('auth', __name__)

# ============================================================
# Decorator: require login to access a page
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ============================================================
# Decorator: require admin role
# ============================================================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('faculty_bp.dashboard'))
        return f(*args, **kwargs)
    return decorated

# ============================================================
# LOGIN
# ============================================================
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('faculty_bp.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']

            if user['role'] == 'faculty':
                c = mysql.connection.cursor()
                c.execute("SELECT id FROM faculty WHERE user_id = %s", (user['id'],))
                fac = c.fetchone()
                c.close()
                if fac:
                    session['faculty_id'] = fac['id']

            flash(f"Welcome, {username}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('faculty_bp.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

# ============================================================
# LOGOUT
# ============================================================
@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
