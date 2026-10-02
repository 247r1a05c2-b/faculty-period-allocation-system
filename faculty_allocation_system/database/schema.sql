-- PostgreSQL schema for Faculty Period Allocation System
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'faculty' CHECK (role IN ('admin','faculty')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faculty (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    experience_years INTEGER NOT NULL DEFAULT 0,
    max_workload INTEGER NOT NULL DEFAULT 6,
    available_days VARCHAR(200) DEFAULT 'Mon,Tue,Wed,Thu,Fri'
);

CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100) NOT NULL,
    credits INTEGER NOT NULL DEFAULT 3,
    weekly_hours INTEGER NOT NULL DEFAULT 2
);

CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    semester INTEGER NOT NULL,
    section VARCHAR(5) NOT NULL
);

CREATE TABLE IF NOT EXISTS preferences (
    id SERIAL PRIMARY KEY,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    preference_rank INTEGER NOT NULL,
    UNIQUE (faculty_id, preference_rank)
);

CREATE TABLE IF NOT EXISTS allocations (
    id SERIAL PRIMARY KEY,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    score DOUBLE PRECISION DEFAULT 0,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (subject_id, class_id)
);

CREATE TABLE IF NOT EXISTS timetable (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    day VARCHAR(20) NOT NULL CHECK (day IN ('Monday','Tuesday','Wednesday','Thursday','Friday')),
    time_slot VARCHAR(20) NOT NULL CHECK (time_slot IN ('9:00-10:00','10:00-11:00','11:00-12:00','12:00-1:00','2:00-3:00','3:00-4:00')),
    room VARCHAR(20) DEFAULT 'TBD',
    UNIQUE (class_id, day, time_slot),
    UNIQUE (faculty_id, day, time_slot)
);

INSERT INTO subjects (name, code, department, credits, weekly_hours) VALUES
('Data Structures','CS101','Computer Science',4,2),
('Database Management','CS102','Computer Science',3,2),
('Operating Systems','CS103','Computer Science',3,2),
('Computer Networks','CS104','Computer Science',3,2),
('Machine Learning','CS105','Computer Science',4,2),
('Web Technologies','CS106','Computer Science',3,2)
ON CONFLICT (code) DO NOTHING;

INSERT INTO classes (name, department, semester, section) VALUES
('CS-A','Computer Science',3,'A'),
('CS-B','Computer Science',3,'B')
ON CONFLICT DO NOTHING;
