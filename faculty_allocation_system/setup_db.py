# setup_db.py - Database Setup Script
# =====================================
# Run this ONCE to create all tables and insert sample data
# with correct password hashes.
#
# Usage:
#   (activate your conda env first)
#   python setup_db.py
#
# It will ask for your MySQL root password.

import sys

# Check required packages
try:
    import pymysql
except ImportError:
    print("ERROR: pymysql not found. Run: pip install PyMySQL")
    sys.exit(1)

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("ERROR: werkzeug not found. Run: pip install Werkzeug")
    sys.exit(1)

import getpass

print("=" * 55)
print("  Faculty Allocation System — Database Setup")
print("=" * 55)

# Get connection details
host = input("MySQL Host [localhost]: ").strip() or "localhost"
user = input("MySQL Username [root]: ").strip() or "root"
pwd  = getpass.getpass("MySQL Password: ")

try:
    # Connect without specifying a database first
    conn = pymysql.connect(host=host, user=user, password=pwd, charset='utf8mb4')
    cur  = conn.cursor()
    print("\n✓ Connected to MySQL successfully.")
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
    print("Make sure MySQL is running and credentials are correct.")
    sys.exit(1)

# ---- Create database ----
cur.execute("CREATE DATABASE IF NOT EXISTS faculty_db CHARACTER SET utf8mb4")
cur.execute("USE faculty_db")
print("✓ Database 'faculty_db' ready.")

# ---- Create tables ----
tables = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        username      VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role          ENUM('admin','faculty') NOT NULL DEFAULT 'faculty',
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS faculty (
        id               INT AUTO_INCREMENT PRIMARY KEY,
        user_id          INT UNIQUE NOT NULL,
        name             VARCHAR(100) NOT NULL,
        email            VARCHAR(100) UNIQUE NOT NULL,
        department       VARCHAR(100) NOT NULL,
        experience_years INT NOT NULL DEFAULT 0,
        max_workload     INT NOT NULL DEFAULT 4,
        available_days   VARCHAR(200) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        name         VARCHAR(100) NOT NULL,
        code         VARCHAR(20) UNIQUE NOT NULL,
        department   VARCHAR(100) NOT NULL,
        credits      INT NOT NULL DEFAULT 3,
        weekly_hours INT NOT NULL DEFAULT 3
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS classes (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        name       VARCHAR(50) NOT NULL,
        department VARCHAR(100) NOT NULL,
        semester   INT NOT NULL,
        section    VARCHAR(5) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS preferences (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        faculty_id      INT NOT NULL,
        subject_id      INT NOT NULL,
        preference_rank INT NOT NULL,
        UNIQUE KEY unique_pref (faculty_id, preference_rank),
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS allocations (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        faculty_id   INT NOT NULL,
        subject_id   INT NOT NULL,
        class_id     INT NOT NULL,
        score        FLOAT DEFAULT 0,
        allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_alloc (subject_id, class_id),
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id)   REFERENCES classes(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS timetable (
        id         INT AUTO_INCREMENT PRIMARY KEY,
        class_id   INT NOT NULL,
        faculty_id INT NOT NULL,
        subject_id INT NOT NULL,
        day        ENUM('Monday','Tuesday','Wednesday','Thursday','Friday') NOT NULL,
        time_slot  ENUM('9:00-10:00','10:00-11:00','11:00-12:00','12:00-1:00','2:00-3:00','3:00-4:00') NOT NULL,
        room       VARCHAR(20) DEFAULT 'TBD',
        UNIQUE KEY no_class_conflict   (class_id, day, time_slot),
        UNIQUE KEY no_faculty_conflict (faculty_id, day, time_slot),
        FOREIGN KEY (class_id)   REFERENCES classes(id) ON DELETE CASCADE,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    )
    """
]

for sql in tables:
    cur.execute(sql)
print("✓ All tables created.")

# ---- Insert sample data (only if empty) ----
cur.execute("SELECT COUNT(*) as cnt FROM users")
if cur.fetchone()[0] == 0:
    # Users with properly hashed passwords
    users = [
        ('admin',    generate_password_hash('admin123'),    'admin'),
        ('faculty1', generate_password_hash('faculty123'),  'faculty'),
        ('faculty2', generate_password_hash('faculty123'),  'faculty'),
        ('faculty3', generate_password_hash('faculty123'),  'faculty'),
    ]
    cur.executemany(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        users
    )
    conn.commit()
    print("✓ Users inserted.")

    # Get user IDs
    cur.execute("SELECT id FROM users WHERE username='faculty1'")
    uid1 = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE username='faculty2'")
    uid2 = cur.fetchone()[0]
    cur.execute("SELECT id FROM users WHERE username='faculty3'")
    uid3 = cur.fetchone()[0]

    # Faculty
    faculty = [
        (uid1, 'Dr. Priya Sharma',  'priya.sharma@college.edu',  'Computer Science', 8,  4, 'Mon,Tue,Wed,Thu,Fri'),
        (uid2, 'Prof. Raj Kumar',   'raj.kumar@college.edu',     'Computer Science', 5,  4, 'Mon,Tue,Wed,Thu'),
        (uid3, 'Dr. Anita Patel',   'anita.patel@college.edu',   'Computer Science', 12, 3, 'Mon,Wed,Thu,Fri'),
    ]
    cur.executemany("""
        INSERT INTO faculty (user_id, name, email, department, experience_years, max_workload, available_days)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, faculty)
    print("✓ Faculty inserted.")

    # Subjects
    subjects = [
        ('Data Structures',         'CS101', 'Computer Science', 4, 4),
        ('Database Management',     'CS102', 'Computer Science', 3, 3),
        ('Operating Systems',       'CS103', 'Computer Science', 3, 3),
        ('Computer Networks',       'CS104', 'Computer Science', 3, 3),
        ('Machine Learning',        'CS105', 'Computer Science', 4, 4),
        ('Web Technologies',        'CS106', 'Computer Science', 3, 3),
    ]
    cur.executemany("""
        INSERT INTO subjects (name, code, department, credits, weekly_hours)
        VALUES (%s, %s, %s, %s, %s)
    """, subjects)
    print("✓ Subjects inserted.")

    # Classes
    classes = [
        ('CS-A', 'Computer Science', 3, 'A'),
        ('CS-B', 'Computer Science', 3, 'B'),
    ]
    cur.executemany(
        "INSERT INTO classes (name, department, semester, section) VALUES (%s,%s,%s,%s)",
        classes
    )
    print("✓ Classes inserted.")

    conn.commit()
else:
    print("✓ Sample data already exists — skipped.")

cur.close()
conn.close()

print("\n" + "=" * 55)
print("  Setup Complete!")
print("  Now update config.py with your MySQL password,")
print("  then run:  python app.py")
print("")
print("  Admin login  : admin / admin123")
print("  Faculty login: faculty1 / faculty123")
print("=" * 55)
