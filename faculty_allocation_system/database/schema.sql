-- ============================================================
-- schema.sql  — Faculty Allocation System
-- ============================================================
-- HOW TO IMPORT INTO phpMyAdmin (XAMPP):
--   1. Open phpMyAdmin  →  http://localhost/phpmyadmin
--   2. Click "New" on the left → create database: faculty_db → click Create
--   3. Select faculty_db → click "Import" tab
--   4. Choose this file → click "Go"
--   5. Run the Flask app:  python app.py
--   6. Open browser:       http://localhost:5001/setup   (ONE TIME ONLY)
--      This creates all login accounts automatically.
-- ============================================================

CREATE DATABASE IF NOT EXISTS `faculty_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `faculty_db`;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY,
    `username`      VARCHAR(50)  UNIQUE NOT NULL,
    `password_hash` VARCHAR(512) NOT NULL,
    `role`          ENUM('admin','faculty') NOT NULL DEFAULT 'faculty',
    `created_at`    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: faculty
-- ============================================================
CREATE TABLE IF NOT EXISTS `faculty` (
    `id`               INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`          INT UNIQUE NOT NULL,
    `name`             VARCHAR(100) NOT NULL,
    `email`            VARCHAR(100) UNIQUE NOT NULL,
    `department`       VARCHAR(100) NOT NULL,
    `experience_years` INT NOT NULL DEFAULT 0,
    `max_workload`     INT NOT NULL DEFAULT 6,
    `available_days`   VARCHAR(200) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: subjects
-- ============================================================
CREATE TABLE IF NOT EXISTS `subjects` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `name`         VARCHAR(100) NOT NULL,
    `code`         VARCHAR(20)  UNIQUE NOT NULL,
    `department`   VARCHAR(100) NOT NULL,
    `credits`      INT NOT NULL DEFAULT 3,
    `weekly_hours` INT NOT NULL DEFAULT 2
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: classes
-- ============================================================
CREATE TABLE IF NOT EXISTS `classes` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `name`       VARCHAR(50)  NOT NULL,
    `department` VARCHAR(100) NOT NULL,
    `semester`   INT NOT NULL,
    `section`    VARCHAR(5)   NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: preferences
-- ============================================================
CREATE TABLE IF NOT EXISTS `preferences` (
    `id`              INT AUTO_INCREMENT PRIMARY KEY,
    `faculty_id`      INT NOT NULL,
    `subject_id`      INT NOT NULL,
    `preference_rank` INT NOT NULL,
    UNIQUE KEY `unique_pref` (`faculty_id`, `preference_rank`),
    FOREIGN KEY (`faculty_id`) REFERENCES `faculty`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: allocations
-- ============================================================
CREATE TABLE IF NOT EXISTS `allocations` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `faculty_id`   INT NOT NULL,
    `subject_id`   INT NOT NULL,
    `class_id`     INT NOT NULL,
    `score`        FLOAT DEFAULT 0,
    `allocated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `unique_alloc` (`subject_id`, `class_id`),
    FOREIGN KEY (`faculty_id`) REFERENCES `faculty`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`class_id`)   REFERENCES `classes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABLE: timetable
-- ============================================================
CREATE TABLE IF NOT EXISTS `timetable` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `class_id`   INT NOT NULL,
    `faculty_id` INT NOT NULL,
    `subject_id` INT NOT NULL,
    `day`        ENUM('Monday','Tuesday','Wednesday','Thursday','Friday') NOT NULL,
    `time_slot`  ENUM('9:00-10:00','10:00-11:00','11:00-12:00',
                      '12:00-1:00','2:00-3:00','3:00-4:00') NOT NULL,
    `room`       VARCHAR(20) DEFAULT 'TBD',
    UNIQUE KEY `no_class_conflict`   (`class_id`,   `day`, `time_slot`),
    UNIQUE KEY `no_faculty_conflict` (`faculty_id`,  `day`, `time_slot`),
    FOREIGN KEY (`class_id`)   REFERENCES `classes`(`id`)  ON DELETE CASCADE,
    FOREIGN KEY (`faculty_id`) REFERENCES `faculty`(`id`)  ON DELETE CASCADE,
    FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- SAMPLE DATA: Subjects
-- weekly_hours = 2  (2 periods per week per subject — solver-friendly)
-- ============================================================
INSERT IGNORE INTO `subjects` (`name`, `code`, `department`, `credits`, `weekly_hours`) VALUES
('Data Structures',      'CS101', 'Computer Science', 4, 2),
('Database Management',  'CS102', 'Computer Science', 3, 2),
('Operating Systems',    'CS103', 'Computer Science', 3, 2),
('Computer Networks',    'CS104', 'Computer Science', 3, 2),
('Machine Learning',     'CS105', 'Computer Science', 4, 2),
('Web Technologies',     'CS106', 'Computer Science', 3, 2);

-- ============================================================
-- SAMPLE DATA: Classes (2 class groups)
-- ============================================================
INSERT IGNORE INTO `classes` (`name`, `department`, `semester`, `section`) VALUES
('CS-A', 'Computer Science', 3, 'A'),
('CS-B', 'Computer Science', 3, 'B');

-- ============================================================
-- NOTE: After importing this SQL, run:
--   python app.py
--   Then open: http://localhost:5001/setup
-- This creates all admin + faculty login accounts automatically.
-- ============================================================
