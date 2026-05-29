# modules/faculty_routes.py - Faculty Panel Routes
# --------------------------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.auth import login_required
from modules.db import mysql

faculty_bp = Blueprint('faculty_bp', __name__, url_prefix='/faculty')

# ============================================================
# FACULTY DASHBOARD
# ============================================================
@faculty_bp.route('/dashboard')
@login_required
def dashboard():
    fac_id = session.get('faculty_id')
    if not fac_id:
        flash('Faculty profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM faculty WHERE id = %s", (fac_id,))
    faculty = cur.fetchone()

    cur.execute("""
        SELECT p.preference_rank, s.name AS subject_name, s.code
        FROM preferences p
        JOIN subjects s ON p.subject_id = s.id
        WHERE p.faculty_id = %s
        ORDER BY p.preference_rank
    """, (fac_id,))
    preferences = cur.fetchall()

    cur.execute("""
        SELECT s.name AS subject_name, s.code, c.name AS class_name, a.score
        FROM allocations a
        JOIN subjects s ON a.subject_id = s.id
        JOIN classes  c ON a.class_id   = c.id
        WHERE a.faculty_id = %s
    """, (fac_id,))
    allocations = cur.fetchall()

    cur.execute("""
        SELECT t.day, t.time_slot, s.name AS subject_name, c.name AS class_name, t.room
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN classes  c ON t.class_id   = c.id
        WHERE t.faculty_id = %s
        ORDER BY FIELD(t.day,'Monday','Tuesday','Wednesday','Thursday','Friday'), t.time_slot
    """, (fac_id,))
    timetable_rows = cur.fetchall()

    cur.close()
    return render_template('faculty/dashboard.html',
                           faculty=faculty,
                           preferences=preferences,
                           allocations=allocations,
                           timetable_rows=timetable_rows)

# ============================================================
# SET PREFERENCES
# ============================================================
@faculty_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    fac_id = session.get('faculty_id')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM subjects ORDER BY code")
    subjects = cur.fetchall()

    cur.execute("""
        SELECT p.preference_rank, p.subject_id, s.name AS subject_name
        FROM preferences p
        JOIN subjects s ON p.subject_id = s.id
        WHERE p.faculty_id = %s
        ORDER BY p.preference_rank
    """, (fac_id,))
    existing = {row['preference_rank']: row for row in cur.fetchall()}

    if request.method == 'POST':
        pref1 = request.form.get('pref1')
        pref2 = request.form.get('pref2')
        pref3 = request.form.get('pref3')

        chosen = [p for p in [pref1, pref2, pref3] if p]
        if len(chosen) < 3:
            flash('Please select all 3 preferences.', 'warning')
            cur.close()
            return redirect(url_for('faculty_bp.preferences'))

        if len(chosen) != len(set(chosen)):
            flash('Please select 3 different subjects.', 'warning')
            cur.close()
            return redirect(url_for('faculty_bp.preferences'))

        cur.execute("DELETE FROM preferences WHERE faculty_id = %s", (fac_id,))
        for rank, subject_id in enumerate([pref1, pref2, pref3], start=1):
            cur.execute("""
                INSERT INTO preferences (faculty_id, subject_id, preference_rank)
                VALUES (%s, %s, %s)
            """, (fac_id, subject_id, rank))

        mysql.connection.commit()
        flash('Preferences saved successfully!', 'success')
        cur.close()
        return redirect(url_for('faculty_bp.dashboard'))

    cur.close()
    return render_template('faculty/preferences.html',
                           subjects=subjects, existing=existing)

# ============================================================
# UPDATE PROFILE
# ============================================================
@faculty_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    fac_id       = session.get('faculty_id')
    experience   = int(request.form.get('experience', 0))
    max_workload = int(request.form.get('max_workload', 4))
    avail_days   = ','.join(request.form.getlist('available_days'))

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE faculty SET experience_years=%s, max_workload=%s, available_days=%s
        WHERE id=%s
    """, (experience, max_workload, avail_days, fac_id))
    mysql.connection.commit()
    cur.close()
    flash('Profile updated!', 'success')
    return redirect(url_for('faculty_bp.dashboard'))

# ============================================================
# FACULTY TIMETABLE VIEW
# ============================================================
@faculty_bp.route('/timetable')
@login_required
def timetable():
    fac_id = session.get('faculty_id')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT t.day, t.time_slot, s.name AS subject_name, s.code,
               c.name AS class_name, t.room
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN classes  c ON t.class_id   = c.id
        WHERE t.faculty_id = %s
        ORDER BY FIELD(t.day,'Monday','Tuesday','Wednesday','Thursday','Friday'), t.time_slot
    """, (fac_id,))
    rows = cur.fetchall()
    cur.close()

    days  = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    slots = ['9:00-10:00','10:00-11:00','11:00-12:00','12:00-1:00','2:00-3:00','3:00-4:00']
    grid  = {d: {s: None for s in slots} for d in days}
    for row in rows:
        grid[row['day']][row['time_slot']] = row

    return render_template('faculty/timetable.html',
                           grid=grid, days=days, slots=slots, rows=rows)

# ============================================================
# EXPORTS
# ============================================================
@faculty_bp.route('/timetable/export/pdf')
@login_required
def export_my_timetable_pdf():
    from modules.export import export_faculty_pdf
    return export_faculty_pdf(session.get('faculty_id'))

@faculty_bp.route('/timetable/export/excel')
@login_required
def export_my_timetable_excel():
    from modules.export import export_faculty_excel
    return export_faculty_excel(session.get('faculty_id'))
