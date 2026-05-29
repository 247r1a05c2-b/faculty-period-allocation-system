# Faculty Subject Allocation & Timetable Generation System
### XAMPP + phpMyAdmin Setup Guide

---

## Step-by-Step Setup (Windows with XAMPP)

### Step 1 — Install XAMPP
Download from: https://www.apachefriends.org/download.html  
Install and open **XAMPP Control Panel** → Start **MySQL** (and Apache if needed).

---

### Step 2 — Import SQL into phpMyAdmin

1. Open browser → go to **http://localhost/phpmyadmin**
2. On the left panel, click **"New"**
3. Type database name: **`faculty_db`** → click **Create**
4. Click the **`faculty_db`** database (now selected on left)
5. Click the **"Import"** tab at the top
6. Click **"Choose File"** → select `database/schema.sql` from this folder
7. Scroll down → click **"Go"**
8. You should see: **"Import has been successfully finished"**

---

### Step 3 — Install Anaconda & Create Environment

Open **Anaconda Prompt** and run:

```bash
conda create -n faculty_env python=3.10 -y
conda activate faculty_env
```

---

### Step 4 — Install Python Packages

```bash
conda install -c conda-forge mysqlclient -y
pip install Flask Flask-MySQLdb Werkzeug pandas openpyxl reportlab ortools PyMySQL
```

---

### Step 5 — Check config.py

Open `config.py` — XAMPP defaults are already set:
```python
MYSQL_HOST     = 'localhost'
MYSQL_USER     = 'root'
MYSQL_PASSWORD = ''        # XAMPP default = blank password
MYSQL_DB       = 'faculty_db'
```
If you set a MySQL password in XAMPP, change `MYSQL_PASSWORD` accordingly.

---

### Step 6 — Run the App

```bash
cd C:\path\to\faculty_allocation_system
python app.py
```

---

### Step 7 — First-Time Setup (IMPORTANT — do this once)

Open browser → go to: **http://localhost:5001/setup**

This page creates all user accounts (admin + 3 faculty).  
You will see a table with login credentials.

---

### Step 8 — Login

Go to: **http://localhost:5001**

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin123    |
| Faculty | faculty1 | faculty123  |
| Faculty | faculty2 | faculty123  |
| Faculty | faculty3 | faculty123  |

---

## How to Use

### Admin Workflow:
1. Log in as **admin**
2. Go to **Faculty** — view/add faculty members
3. Go to **Subjects** — view/add subjects  
4. Go to **Classes** — view/add class groups
5. Log in as faculty → set preferences (or skip — allocation works without preferences too)
6. Admin → **Allocation** → click **Run Allocation** (AI scoring)
7. Admin → **Timetable** → click **Generate Timetable** (OR-Tools)
8. Export as PDF or Excel

### Faculty Workflow:
1. Log in as **faculty1/2/3**
2. Go to **Preferences** → select 3 preferred subjects
3. Update experience, workload, available days
4. After admin generates timetable, view **My Timetable**

---

## Folder Structure

```
faculty_allocation_system/
├── app.py                  ← Run this file
├── config.py               ← XAMPP database settings
├── requirements.txt
├── database/
│   └── schema.sql          ← Import this into phpMyAdmin
├── modules/
│   ├── db.py               ← MySQL connection
│   ├── auth.py             ← Login/logout
│   ├── admin_routes.py     ← Admin pages
│   ├── faculty_routes.py   ← Faculty pages
│   ├── allocation.py       ← AI scoring algorithm
│   ├── timetable.py        ← OR-Tools scheduler
│   └── export.py           ← PDF + Excel export
├── templates/
│   ├── login.html
│   ├── setup_done.html     ← First-run setup result page
│   ├── base.html           ← Sidebar layout
│   ├── admin/              ← 7 admin page templates
│   └── faculty/            ← 3 faculty page templates
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## Troubleshooting

**`Access denied for user 'root'@'localhost'`**  
→ Open `config.py`, set `MYSQL_PASSWORD = 'your_xampp_mysql_password'`

**`Unknown database 'faculty_db'`**  
→ You haven't imported `schema.sql` yet — follow Step 2 above.

**`ModuleNotFoundError: flask_mysqldb`**  
→ Run: `conda install -c conda-forge mysqlclient -y` then `pip install Flask-MySQLdb`

**`/setup says "Error: Table users doesn't exist"`**  
→ The SQL import didn't work. Redo Step 2 carefully.

**Port 5001 in use**  
→ Change `port=5001` to `port=5002` in `app.py`

**Timetable solver fails**  
→ Reduce `weekly_hours` to 2 for each subject in the Subjects page, then re-run.
