# modules/db.py - MySQL instance
# --------------------------------
# Initialised in app.py via db.init_app(app)
# All other modules import `mysql` from here — no circular imports.

from flask_mysqldb import MySQL

mysql = MySQL()
