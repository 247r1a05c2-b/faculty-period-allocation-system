# modules/timetable.py - Timetable Generation using Google OR-Tools CP-SAT
# --------------------------------------------------------------------------

from modules.db import mysql

DAY_ABBR_MAP = {
    'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday',
    'Thu': 'Thursday', 'Fri': 'Friday',
    'Monday': 'Monday', 'Tuesday': 'Tuesday', 'Wednesday': 'Wednesday',
    'Thursday': 'Thursday', 'Friday': 'Friday',
}


def generate_timetable_ortools():
    """Generate and persist a conflict-free timetable with OR-Tools."""
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {'success': False, 'count': 0,
                'error': 'OR-Tools is not installed on the server.'}

    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT a.id, a.faculty_id, a.subject_id, a.class_id,
                   s.weekly_hours, f.available_days
            FROM allocations a
            JOIN subjects s ON a.subject_id = s.id
            JOIN faculty f ON a.faculty_id = f.id
            ORDER BY a.class_id, a.subject_id
        """)
        allocations = cur.fetchall()

        if not allocations:
            return {'success': False, 'count': 0,
                    'error': 'No allocations found. Run Subject Allocation first.'}

        DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        SLOTS = ['9:00-10:00', '10:00-11:00', '11:00-12:00',
                 '12:00-1:00', '2:00-3:00', '3:00-4:00']
        NUM_DAYS = len(DAYS)
        NUM_SLOTS = len(SLOTS)

        def get_avail_days(value):
            parts = [p.strip() for p in (value or '').split(',') if p.strip()]
            full = [DAY_ABBR_MAP.get(p, p) for p in parts]
            valid = [d for d in full if d in DAYS]
            return valid if valid else DAYS

        model = cp_model.CpModel()
        x = {}
        alloc_avail = {}

        for i, alloc in enumerate(allocations):
            available = get_avail_days(alloc['available_days'])
            day_indexes = [d for d, name in enumerate(DAYS) if name in available]
            alloc_avail[i] = day_indexes

            weekly_hours = int(alloc['weekly_hours'] or 1)
            if weekly_hours > len(day_indexes):
                return {
                    'success': False,
                    'count': 0,
                    'error': (
                        f"{weekly_hours} weekly hours cannot be scheduled for allocation "
                        f"{alloc['id']} with only {len(day_indexes)} available days. "
                        "Increase faculty availability or reduce weekly hours."
                    )
                }

            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    var = model.NewBoolVar(f'x_a{i}_d{d}_s{s}')
                    x[(i, d, s)] = var
                    if d not in day_indexes:
                        model.Add(var == 0)

            model.Add(
                sum(x[(i, d, s)] for d in range(NUM_DAYS) for s in range(NUM_SLOTS))
                == weekly_hours
            )

        from collections import defaultdict
        faculty_at = defaultdict(list)
        class_at = defaultdict(list)

        for i, alloc in enumerate(allocations):
            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    faculty_at[(alloc['faculty_id'], d, s)].append(x[(i, d, s)])
                    class_at[(alloc['class_id'], d, s)].append(x[(i, d, s)])

        for variables in faculty_at.values():
            if len(variables) > 1:
                model.Add(sum(variables) <= 1)

        for variables in class_at.values():
            if len(variables) > 1:
                model.Add(sum(variables) <= 1)

        # Spread each class/subject over different days.
        for i in range(len(allocations)):
            for d in range(NUM_DAYS):
                model.Add(sum(x[(i, d, s)] for s in range(NUM_SLOTS)) <= 1)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 12.0
        solver.parameters.num_search_workers = 8
        solver.parameters.random_seed = 42
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return {
                'success': False,
                'count': 0,
                'error': (
                    'No feasible timetable was found within the time limit. '
                    'Increase faculty availability, reduce weekly hours, or increase faculty workload limits.'
                )
            }

        cur.execute("DELETE FROM timetable")

        # Assign rooms after solving, guaranteeing no room is used twice in
        # the same day/period. One room is selected for every scheduled class.
        room_count = max(6, len({a['class_id'] for a in allocations}))
        rooms = [f'R{101 + i}' for i in range(room_count)]
        used_rooms = defaultdict(set)
        count = 0

        for i, alloc in enumerate(allocations):
            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    if solver.Value(x[(i, d, s)]) != 1:
                        continue

                    occupied = used_rooms[(DAYS[d], SLOTS[s])]
                    room = next((r for r in rooms if r not in occupied), None)
                    if room is None:
                        return {
                            'success': False,
                            'count': 0,
                            'error': 'Not enough rooms for the generated schedule.'
                        }

                    occupied.add(room)
                    cur.execute("""
                        INSERT INTO timetable
                            (class_id, faculty_id, subject_id, day, time_slot, room)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        alloc['class_id'], alloc['faculty_id'], alloc['subject_id'],
                        DAYS[d], SLOTS[s], room
                    ))
                    count += 1

        mysql.connection.commit()
        return {'success': True, 'count': count}

    except Exception as e:
        try:
            mysql.connection.rollback()
        except Exception:
            pass
        return {'success': False, 'count': 0, 'error': str(e)}
    finally:
        if cur is not None:
            cur.close()
