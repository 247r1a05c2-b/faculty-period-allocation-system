# modules/export.py - PDF and Excel Export
# ------------------------------------------

import io
from flask import send_file, flash, redirect, url_for
from modules.db import mysql


def _get_timetable_data(faculty_id=None):
    """Fetch timetable rows, optionally filtered by faculty."""
    cur = mysql.connection.cursor()
    if faculty_id:
        cur.execute("""
            SELECT t.day, t.time_slot, s.name AS subject_name, s.code,
                   f.name AS faculty_name, c.name AS class_name, t.room
            FROM timetable t
            JOIN subjects s ON t.subject_id = s.id
            JOIN faculty  f ON t.faculty_id  = f.id
            JOIN classes  c ON t.class_id    = c.id
            WHERE t.faculty_id = %s
            ORDER BY FIELD(t.day,'Monday','Tuesday','Wednesday','Thursday','Friday'), t.time_slot
        """, (faculty_id,))
    else:
        cur.execute("""
            SELECT t.day, t.time_slot, s.name AS subject_name, s.code,
                   f.name AS faculty_name, c.name AS class_name, t.room
            FROM timetable t
            JOIN subjects s ON t.subject_id = s.id
            JOIN faculty  f ON t.faculty_id  = f.id
            JOIN classes  c ON t.class_id    = c.id
            ORDER BY c.name,
                     FIELD(t.day,'Monday','Tuesday','Wednesday','Thursday','Friday'),
                     t.time_slot
        """)
    rows = cur.fetchall()
    cur.close()
    return rows


# ============================================================
# EXCEL — full timetable
# ============================================================
def export_excel():
    try:
        import pandas as pd
        rows = _get_timetable_data()
        if not rows:
            flash('No timetable data to export.', 'warning')
            return redirect(url_for('admin.timetable'))

        df = pd.DataFrame(rows, columns=['Day','Time Slot','Subject','Code','Faculty','Class','Room'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Full Timetable', index=False)
            for cls_name in df['Class'].unique():
                sub = df[df['Class'] == cls_name][['Day','Time Slot','Subject','Faculty','Room']]
                sub.to_excel(writer, sheet_name=f'Class {cls_name}'[:31], index=False)

        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='timetable.xlsx')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('admin.timetable'))


# ============================================================
# EXCEL — faculty specific
# ============================================================
def export_faculty_excel(faculty_id):
    try:
        import pandas as pd
        rows = _get_timetable_data(faculty_id=faculty_id)

        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM faculty WHERE id = %s", (faculty_id,))
        fac = cur.fetchone()
        cur.close()
        fac_name = fac['name'] if fac else f'Faculty_{faculty_id}'

        if not rows:
            flash('No timetable data to export.', 'warning')
            return redirect(url_for('faculty_bp.timetable'))

        df = pd.DataFrame(rows, columns=['Day','Time Slot','Subject','Code','Faculty','Class','Room'])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='My Timetable', index=False)

        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True,
                         download_name=f'timetable_{fac_name.replace(" ","_")}.xlsx')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect(url_for('faculty_bp.timetable'))


# ============================================================
# PDF — full timetable
# ============================================================
def export_pdf():
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table,
                                        TableStyle, Paragraph, Spacer)
        from reportlab.lib.styles import getSampleStyleSheet

        rows = _get_timetable_data()
        if not rows:
            flash('No timetable data to export.', 'warning')
            return redirect(url_for('admin.timetable'))

        output  = io.BytesIO()
        doc     = SimpleDocTemplate(output, pagesize=landscape(A4))
        styles  = getSampleStyleSheet()
        content = [Paragraph('Faculty Timetable', styles['Title']), Spacer(1, 12)]

        header = ['Day','Time Slot','Subject','Code','Faculty','Class','Room']
        data   = [header] + [
            [r['day'], r['time_slot'], r['subject_name'],
             r['code'], r['faculty_name'], r['class_name'], r['room']]
            for r in rows
        ]

        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0),  colors.HexColor('#1a237e')),
            ('TEXTCOLOR',  (0,0), (-1,0),  colors.white),
            ('FONTNAME',   (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        content.append(tbl)

        doc.build(content)
        output.seek(0)
        return send_file(output, mimetype='application/pdf',
                         as_attachment=True, download_name='timetable.pdf')
    except Exception as e:
        flash(f'PDF export error: {str(e)}', 'danger')
        return redirect(url_for('admin.timetable'))


# ============================================================
# PDF — faculty specific
# ============================================================
def export_faculty_pdf(faculty_id):
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table,
                                        TableStyle, Paragraph, Spacer)
        from reportlab.lib.styles import getSampleStyleSheet

        rows = _get_timetable_data(faculty_id=faculty_id)

        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM faculty WHERE id = %s", (faculty_id,))
        fac = cur.fetchone()
        cur.close()
        fac_name = fac['name'] if fac else 'Faculty'

        if not rows:
            flash('No timetable data.', 'warning')
            return redirect(url_for('faculty_bp.timetable'))

        output  = io.BytesIO()
        doc     = SimpleDocTemplate(output, pagesize=landscape(A4))
        styles  = getSampleStyleSheet()
        content = [Paragraph(f'Timetable — {fac_name}', styles['Title']), Spacer(1, 12)]

        header = ['Day','Time Slot','Subject','Class','Room']
        data   = [header] + [
            [r['day'], r['time_slot'], r['subject_name'], r['class_name'], r['room']]
            for r in rows
        ]

        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0),  colors.HexColor('#1565c0')),
            ('TEXTCOLOR',  (0,0), (-1,0),  colors.white),
            ('FONTNAME',   (0,0), (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#e3f2fd')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        content.append(tbl)

        doc.build(content)
        output.seek(0)
        return send_file(output, mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'timetable_{fac_name.replace(" ","_")}.pdf')
    except Exception as e:
        flash(f'PDF export error: {str(e)}', 'danger')
        return redirect(url_for('faculty_bp.timetable'))
