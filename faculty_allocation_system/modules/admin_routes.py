# modules/admin_routes.py - Admin Panel Routes
# -----------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from modules.auth import admin_required
from modules.db import mysql

admin = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================
# ADMIN DASHBOARD
# ============================================================
@admin.route('/dashboard')
@admin_required
def dashboard():
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM faculty")
    faculty_count = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM subjects")
    subject_count = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM classes")
    class_count = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM allocations")
    alloc_count = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM timetable")
    tt_count = cur.fetchone()['cnt']

    cur.execute("""
        SELECT f.name AS faculty_name, s.name AS subject_name,
               c.name AS class_name, a.score
        FROM allocations a
        JOIN faculty f   ON a.faculty_id = f.id
        JOIN subjects s  ON a.subject_id = s.id
        JOIN classes  c  ON a.class_id   = c.id
        ORDER BY a.allocated_at DESC LIMIT 10
    """)
    recent_allocs = cur.fetchall()

    cur.execute("""
        SELECT f.name, COUNT(a.id) AS assigned_subjects, f.max_workload
        FROM faculty f
        LEFT JOIN allocations a ON f.id = a.faculty_id
        GROUP BY f.id, f.name, f.max_workload
    """)
    workload_data = cur.fetchall()

    cur.close()
    return render_template('admin/dashboard.html',
                           faculty_count=faculty_count,
                           subject_count=subject_count,
                           class_count=class_count,
                           alloc_count=alloc_count,
                           tt_count=tt_count,
                           recent_allocs=recent_allocs,
                           workload_data=workload_data)

# ============================================================
# MANAGE FACULTY
# ============================================================
@admin.route('/faculty')
@admin_required
def faculty_list():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT f.*, u.username
        FROM faculty f JOIN users u ON f.user_id = u.id
        ORDER BY f.name
    """)
    faculty = cur.fetchall()
    cur.close()
    return render_template('admin/faculty.html', faculty=faculty)

@admin.route('/faculty/add', methods=['GET', 'POST'])
@admin_required
def add_faculty():
    if request.method == 'POST':
        username   = request.form['username'].strip()
        password   = request.form['password']
        name       = request.form['name'].strip()
        email      = request.form['email'].strip()
        department = request.form['department'].strip()
        experience = int(request.form.get('experience', 0))
        max_work   = int(request.form.get('max_workload', 4))
        avail_days = ','.join(request.form.getlist('available_days'))
        try:
            cur = mysql.connection.cursor()
            pw_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'faculty')",
                (username, pw_hash)
            )
            user_id = cur.lastrowid
            cur.execute("""
                INSERT INTO faculty (user_id, name, email, department,
                                     experience_years, max_workload, available_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, email, department, experience, max_work, avail_days))
            mysql.connection.commit()
            cur.close()
            flash(f'Faculty {name} added successfully.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin.faculty_list'))
    return render_template('admin/add_faculty.html')

@admin.route('/faculty/delete/<int:fid>', methods=['POST'])
@admin_required
def delete_faculty(fid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id FROM faculty WHERE id = %s", (fid,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM users WHERE id = %s", (row['user_id'],))
        mysql.connection.commit()
        flash('Faculty deleted.', 'success')
    cur.close()
    return redirect(url_for('admin.faculty_list'))

# ============================================================
# MANAGE SUBJECTS
# ============================================================
@admin.route('/subjects')
@admin_required
def subjects():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM subjects ORDER BY code")
    subj = cur.fetchall()
    cur.close()
    return render_template('admin/subjects.html', subjects=subj)

@admin.route('/subjects/add', methods=['POST'])
@admin_required
def add_subject():
    name     = request.form['name'].strip()
    code     = request.form['code'].strip().upper()
    dept     = request.form['department'].strip()
    credits  = int(request.form.get('credits', 3))
    wk_hours = int(request.form.get('weekly_hours', 3))
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO subjects (name, code, department, credits, weekly_hours)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, code, dept, credits, wk_hours))
        mysql.connection.commit()
        cur.close()
        flash(f'Subject {code} added.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.subjects'))

@admin.route('/subjects/delete/<int:sid>', methods=['POST'])
@admin_required
def delete_subject(sid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM subjects WHERE id = %s", (sid,))
    mysql.connection.commit()
    cur.close()
    flash('Subject deleted.', 'success')
    return redirect(url_for('admin.subjects'))

# ============================================================
# MANAGE CLASSES
# ============================================================
@admin.route('/classes')
@admin_required
def classes():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM classes ORDER BY department, semester, section")
    cls = cur.fetchall()
    cur.close()
    return render_template('admin/classes.html', classes=cls)

@admin.route('/classes/add', methods=['POST'])
@admin_required
def add_class():
    name     = request.form['name'].strip()
    dept     = request.form['department'].strip()
    semester = int(request.form.get('semester', 1))
    section  = request.form.get('section', 'A').strip()
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO classes (name, department, semester, section) VALUES (%s,%s,%s,%s)",
            (name, dept, semester, section)
        )
        mysql.connection.commit()
        cur.close()
        flash(f'Class {name} added.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.classes'))

@admin.route('/classes/delete/<int:cid>', methods=['POST'])
@admin_required
def delete_class(cid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM classes WHERE id = %s", (cid,))
    mysql.connection.commit()
    cur.close()
    flash('Class deleted.', 'success')
    return redirect(url_for('admin.classes'))

# ============================================================
# SUBJECT ALLOCATION
# ============================================================
@admin.route('/allocation')
@admin_required
def allocation():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.id, f.name AS faculty_name, s.name AS subject_name,
               s.code AS subject_code, c.name AS class_name, a.score
        FROM allocations a
        JOIN faculty f  ON a.faculty_id = f.id
        JOIN subjects s ON a.subject_id = s.id
        JOIN classes  c ON a.class_id   = c.id
        ORDER BY c.name, s.code
    """)
    allocations = cur.fetchall()

    cur.execute("""
        SELECT f.name AS faculty_name, s.name AS subject_name, p.preference_rank
        FROM preferences p
        JOIN faculty f  ON p.faculty_id = f.id
        JOIN subjects s ON p.subject_id = s.id
        ORDER BY f.name, p.preference_rank
    """)
    preferences = cur.fetchall()
    cur.close()
    return render_template('admin/allocation.html',
                           allocations=allocations, preferences=preferences)

@admin.route('/allocation/run', methods=['POST'])
@admin_required
def run_allocation():
    from modules.allocation import run_subject_allocation
    result = run_subject_allocation()
    if result['success']:
        flash(f"Allocation complete! {result['count']} subjects allocated.", 'success')
    else:
        flash(f"Allocation error: {result['error']}", 'danger')
    return redirect(url_for('admin.allocation'))

@admin.route('/allocation/clear', methods=['POST'])
@admin_required
def clear_allocation():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM timetable")
    cur.execute("DELETE FROM allocations")
    mysql.connection.commit()
    cur.close()
    flash('All allocations and timetable cleared.', 'info')
    return redirect(url_for('admin.allocation'))

# ============================================================
# TIMETABLE
# ============================================================
@admin.route('/timetable')
@admin_required
def timetable():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM classes ORDER BY name")
    classes = cur.fetchall()

    cur.execute("SELECT * FROM faculty ORDER BY name")
    faculty = cur.fetchall()

    cur.execute("""
        SELECT t.*, f.name AS faculty_name, s.name AS subject_name,
               s.code AS subject_code, c.name AS class_name
        FROM timetable t
        JOIN faculty f  ON t.faculty_id = f.id
        JOIN subjects s ON t.subject_id = s.id
        JOIN classes  c ON t.class_id   = c.id
        ORDER BY c.name, t.day, t.time_slot
    """)
    timetable_rows = cur.fetchall()
    cur.close()

    days  = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    slots = ['9:00-10:00','10:00-11:00','11:00-12:00','12:00-1:00','2:00-3:00','3:00-4:00']

    tt_grid = {}
    for cls in classes:
        tt_grid[cls['name']] = {d: {s: None for s in slots} for d in days}

    for row in timetable_rows:
        cname = row['class_name']
        if cname in tt_grid:
            tt_grid[cname][row['day']][row['time_slot']] = row

    return render_template('admin/timetable.html',
                           classes=classes, faculty=faculty,
                           tt_grid=tt_grid, days=days, slots=slots,
                           timetable_rows=timetable_rows)

@admin.route('/timetable/generate', methods=['POST'])
@admin_required
def generate_timetable():
    from modules.timetable import generate_timetable_ortools
    result = generate_timetable_ortools()
    if result['success']:
        flash(f"Timetable generated! {result['count']} periods scheduled.", 'success')
    else:
        flash(f"Timetable error: {result['error']}", 'danger')
    return redirect(url_for('admin.timetable'))

@admin.route('/timetable/clear', methods=['POST'])
@admin_required
def clear_timetable():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM timetable")
    mysql.connection.commit()
    cur.close()
    flash('Timetable cleared.', 'info')
    return redirect(url_for('admin.timetable'))

# ============================================================
# EXPORTS
# ============================================================
@admin.route('/export/timetable/excel')
@admin_required
def export_timetable_excel():
    from modules.export import export_excel
    return export_excel()

@admin.route('/export/timetable/pdf')
@admin_required
def export_timetable_pdf():
    from modules.export import export_pdf
    return export_pdf()

@admin.route('/export/timetable/excel/faculty/<int:fac_id>')
@admin_required
def export_faculty_timetable_excel(fac_id):
    from modules.export import export_faculty_excel
    return export_faculty_excel(fac_id)
