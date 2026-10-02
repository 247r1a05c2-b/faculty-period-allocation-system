import os
import re
from flask import g
import psycopg2
from psycopg2.extras import RealDictCursor

class CompatCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, sql, params=None):
        # Translate the MySQL FIELD(day, ...) ordering function used by the UI.
        sql = re.sub(
            r"FIELD\(t\.day,'Monday','Tuesday','Wednesday','Thursday','Friday'\)",
            "CASE t.day WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 END",
            sql,
            flags=re.IGNORECASE,
        )
        # Preserve the old MySQL lastrowid behavior for legacy routes.
        if re.match(r"\s*INSERT\s+INTO\s+users\b", sql, re.IGNORECASE) and 'RETURNING' not in sql.upper():
            sql = sql.rstrip().rstrip(';') + ' RETURNING id'
            self._cursor.execute(sql, params)
            row = self._cursor.fetchone()
            self.lastrowid = row['id'] if row else None
            return self
        self._cursor.execute(sql, params)
        return self

    def executemany(self, sql, seq_of_params):
        self._cursor.executemany(sql, seq_of_params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()

class PostgresDB:
    def init_app(self, app):
        app.before_request(self._connect)
        app.teardown_appcontext(self._close)

    def _connect(self):
        if 'db_conn' not in g:
            url = os.environ.get('DATABASE_URL')
            if not url:
                raise RuntimeError('DATABASE_URL environment variable is not configured.')
            g.db_conn = psycopg2.connect(url)

    def _close(self, exception=None):
        conn = g.pop('db_conn', None)
        if conn is not None:
            conn.close()

    @property
    def connection(self):
        conn = g.get('db_conn')
        if conn is None:
            self._connect()
            conn = g.db_conn
        return ConnectionProxy(conn)

class ConnectionProxy:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return CompatCursor(self._connection.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

mysql = PostgresDB()
