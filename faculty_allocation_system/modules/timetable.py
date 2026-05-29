# modules/timetable.py - Timetable Generation using Google OR-Tools CP-SAT
# --------------------------------------------------------------------------

from modules.db import mysql

# Maps short day names (stored in DB) → full day names used by the solver
DAY_ABBR_MAP = {
    'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday',
    'Thu': 'Thursday', 'Fri': 'Friday',
    # Also accept full names in case someone stores them that way
    'Monday': 'Monday', 'Tuesday': 'Tuesday', 'Wednesday': 'Wednesday',
    'Thursday': 'Thursday', 'Friday': 'Friday',
}

def generate_timetable_ortools():
    """
    Generates a conflict-free timetable using OR-Tools CP-SAT solver.
    Returns: {'success': bool, 'count': int, 'error': str}
    """
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return {'success': False, 'count': 0,
                'error': 'ortools not installed. Run: pip install ortools'}

    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT a.id, a.faculty_id, a.subject_id, a.class_id,
                   s.weekly_hours, f.available_days
            FROM allocations a
            JOIN subjects s ON a.subject_id = s.id
            JOIN faculty  f ON a.faculty_id  = f.id
        """)
        allocations = cur.fetchall()

        if not allocations:
            cur.close()
            return {'success': False, 'count': 0,
                    'error': 'No allocations found. Run Subject Allocation first.'}

        DAYS  = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        SLOTS = ['9:00-10:00', '10:00-11:00', '11:00-12:00',
                 '12:00-1:00', '2:00-3:00',   '3:00-4:00']

        NUM_DAYS  = len(DAYS)
        NUM_SLOTS = len(SLOTS)

        # Cap weekly_hours at available days to prevent impossible constraints
        # e.g. if a subject needs 3 hrs but faculty only available 2 days → cap to 2
        def get_avail_days(avail_str):
            """Convert stored day string to list of full day names."""
            parts = [p.strip() for p in (avail_str or '').split(',') if p.strip()]
            full  = [DAY_ABBR_MAP.get(p, p) for p in parts]
            valid = [d for d in full if d in DAYS]
            return valid if valid else DAYS   # fallback: all days if none matched

        model = cp_model.CpModel()

        # ------------------------------------------------------------------
        # Decision variables: x[(alloc_idx, day, slot)] = 1 if scheduled
        # ------------------------------------------------------------------
        x = {}
        alloc_avail = {}   # cache of available day indices per allocation

        for i, alloc in enumerate(allocations):
            avail_full    = get_avail_days(alloc['available_days'])
            avail_day_idx = [di for di, dn in enumerate(DAYS) if dn in avail_full]
            alloc_avail[i] = avail_day_idx

            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    var = model.NewBoolVar(f'x_a{i}_d{d}_s{s}')
                    x[(i, d, s)] = var
                    if d not in avail_day_idx:
                        # Faculty not available on this day — force to 0
                        model.Add(var == 0)

        # ------------------------------------------------------------------
        # Constraint 1: Each allocation scheduled exactly weekly_hours times
        # BUT cap at (available_days × 1) to keep it feasible
        # ------------------------------------------------------------------
        for i, alloc in enumerate(allocations):
            avail_count  = len(alloc_avail[i])
            target_hours = min(alloc['weekly_hours'], avail_count)
            model.Add(
                sum(x[(i, d, s)] for d in range(NUM_DAYS) for s in range(NUM_SLOTS))
                == target_hours
            )

        # ------------------------------------------------------------------
        # Constraint 2: No faculty conflict — same faculty can't teach two
        # things at the same (day, slot)
        # ------------------------------------------------------------------
        from collections import defaultdict
        faculty_at = defaultdict(list)
        class_at   = defaultdict(list)

        for i, alloc in enumerate(allocations):
            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    faculty_at[(alloc['faculty_id'], d, s)].append(x[(i, d, s)])
                    class_at[(alloc['class_id'],   d, s)].append(x[(i, d, s)])

        for vlist in faculty_at.values():
            if len(vlist) > 1:
                model.Add(sum(vlist) <= 1)

        # ------------------------------------------------------------------
        # Constraint 3: No class conflict — a class can't have two subjects
        # at the same (day, slot)
        # ------------------------------------------------------------------
        for vlist in class_at.values():
            if len(vlist) > 1:
                model.Add(sum(vlist) <= 1)

        # ------------------------------------------------------------------
        # Constraint 4: At most 1 period of same subject per class per day
        # (spread subjects across the week)
        # ------------------------------------------------------------------
        for i in range(len(allocations)):
            for d in range(NUM_DAYS):
                model.Add(sum(x[(i, d, s)] for s in range(NUM_SLOTS)) <= 1)

        # ------------------------------------------------------------------
        # Solve with generous timeout
        # ------------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 120.0
        solver.parameters.num_search_workers  = 4   # use multiple threads
        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            cur.close()
            return {
                'success': False, 'count': 0,
                'error': (
                    'Solver could not find a feasible schedule. '
                    'Tips: (1) Go to Subjects and reduce "Weekly Hours" to 2. '
                    '(2) Go to Faculty and increase "Max Workload". '
                    '(3) Make sure all faculty have 5 available days.'
                )
            }

        # ------------------------------------------------------------------
        # Save results to timetable table
        # ------------------------------------------------------------------
        cur.execute("DELETE FROM timetable")
        mysql.connection.commit()

        rooms = ['R101', 'R102', 'R103', 'R104', 'R105', 'R106']
        count = 0

        for i, alloc in enumerate(allocations):
            for d in range(NUM_DAYS):
                for s in range(NUM_SLOTS):
                    if solver.Value(x[(i, d, s)]) == 1:
                        room = rooms[(alloc['class_id'] + d + s) % len(rooms)]
                        cur.execute("""
                            INSERT INTO timetable
                                (class_id, faculty_id, subject_id, day, time_slot, room)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (alloc['class_id'], alloc['faculty_id'],
                              alloc['subject_id'], DAYS[d], SLOTS[s], room))
                        count += 1

        mysql.connection.commit()
        cur.close()
        return {'success': True, 'count': count}

    except Exception as e:
        return {'success': False, 'count': 0, 'error': str(e)}
