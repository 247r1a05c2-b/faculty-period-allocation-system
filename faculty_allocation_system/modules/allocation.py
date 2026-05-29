# modules/allocation.py - AI-Based Subject Allocation Algorithm
# ---------------------------------------------------------------
# Weighted scoring:
#   Preference rank 1 = 10 pts
#   Preference rank 2 =  7 pts
#   Preference rank 3 =  5 pts
#   Experience bonus  = min(experience_years, 5) pts
#   Workload penalty  = -2 pts per already-assigned subject

from modules.db import mysql

def run_subject_allocation():
    """
    Runs weighted scoring allocation.
    Returns: {'success': bool, 'count': int, 'error': str}
    """
    try:
        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM faculty")
        faculty_list = cur.fetchall()

        cur.execute("SELECT * FROM subjects")
        subjects = cur.fetchall()

        cur.execute("SELECT * FROM classes")
        classes = cur.fetchall()

        cur.execute("""
            SELECT p.faculty_id, p.subject_id, p.preference_rank,
                   f.experience_years, f.max_workload
            FROM preferences p
            JOIN faculty f ON p.faculty_id = f.id
        """)
        preferences = cur.fetchall()

        # Preference lookup: {(faculty_id, subject_id): rank}
        pref_lookup = {}
        for row in preferences:
            pref_lookup[(row['faculty_id'], row['subject_id'])] = row['preference_rank']

        RANK_SCORE = {1: 10, 2: 7, 3: 5}

        # Clear existing allocations
        cur.execute("DELETE FROM timetable")
        cur.execute("DELETE FROM allocations")
        mysql.connection.commit()

        allocation_count = 0
        # Track load per faculty: {faculty_id: count}
        faculty_load = {f['id']: 0 for f in faculty_list}

        for cls in classes:
            for subj in subjects:
                best_faculty_id = None
                best_score      = -9999

                for fac in faculty_list:
                    fac_id = fac['id']

                    # Skip if at max workload
                    if faculty_load[fac_id] >= fac['max_workload']:
                        continue

                    # Preference score
                    rank  = pref_lookup.get((fac_id, subj['id']), None)
                    score = RANK_SCORE.get(rank, 0)

                    # Experience bonus (capped at 5)
                    score += min(fac['experience_years'], 5)

                    # Workload penalty (favour less-loaded faculty)
                    score -= faculty_load[fac_id] * 2

                    if score > best_score:
                        best_score      = score
                        best_faculty_id = fac_id

                if best_faculty_id is not None:
                    cur.execute("""
                        INSERT INTO allocations (faculty_id, subject_id, class_id, score)
                        VALUES (%s, %s, %s, %s)
                    """, (best_faculty_id, subj['id'], cls['id'], round(best_score, 2)))
                    faculty_load[best_faculty_id] += 1
                    allocation_count += 1

        mysql.connection.commit()
        cur.close()
        return {'success': True, 'count': allocation_count}

    except Exception as e:
        return {'success': False, 'count': 0, 'error': str(e)}
