import os
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from flask import g
import psycopg2
from psycopg2.extras import RealDictCursor


def _database_url():
    url = os.environ.get('DATABASE_URL', '').strip()
    if not url:
        raise RuntimeError('DATABASE_URL environment variable is not configured.')

    parts = urlparse(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault('sslmode', 'require')
    query.setdefault('connect_timeout', '10')
    return urlunparse(parts._replace(query=urlencode(query)))


class CompatCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, sql, params=None):
        sql = re.sub(
            r"FIELD\(t\.day,'Monday','Tuesday','Wednesday','Thursday','Friday'\)",
            "CASE t.day WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 END",
            sql,
            flags=re.IGNORECASE,
        )
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
        app.teardown_appcontext(self._close)

    def _connect(self):
        if 'db_conn' not in g:
            g.db_conn = psycopg2.connect(_database_url())
        return g.db_conn

    def _close(self, exception=None):
        conn = g.pop('db_conn', None)
        if conn is not None:
            conn.close()

    @property
    def connection(self):
        return ConnectionProxy(self._connect())


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
