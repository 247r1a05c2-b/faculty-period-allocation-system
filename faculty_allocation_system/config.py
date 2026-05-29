# config.py - Application Configuration for XAMPP
# --------------------------------------------------
# XAMPP defaults:
#   Host     : localhost
#   Username : root
#   Password : (empty string — XAMPP default)
#   DB Name  : faculty_db

import os

class Config:
    # ---- Flask Secret Key ----
    SECRET_KEY = os.environ.get('SECRET_KEY', 'faculty_alloc_secret_2024')

    # ---- MySQL (XAMPP defaults) ----
    MYSQL_HOST     = 'localhost'
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = ''          # XAMPP default is blank — change if you set a password
    MYSQL_DB       = 'faculty_db'
    MYSQL_CURSORCLASS = 'DictCursor'

    # ---- Export folder ----
    EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), 'exports')
