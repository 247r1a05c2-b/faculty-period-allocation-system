import os
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from flask import g
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

_POOL = None


def _database_url():
    url = os.environ.get('DATABASE_URL', '').strip()
    if not url:
        raise RuntimeError('DATABASE_URL environment variable is not configured.')

    parts = urlparse(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault('sslmode', 'require')
    query.setdefault('connect_timeout', '5')
    query.setdefault('keepalives', '1')
    query.setdefault('keepalives_idle', '30')
    query.setdefault('keepalives_interval', '10')
    query.setdefault('keepalives_count', '3')
    return urlunparse(parts._replace(query=urlencode(query)))


def _get_pool():
    global _POOL
    if _POOL is None:
        _POOL = pool.ThreadedConnectionPool(1, 4, _database_url())
    return _POOL


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
            conn = _get_pool().getconn()
            conn.autocommit = False
            g.db_conn = conn
        return g.db_conn

    def _close(self, exception=None):
        conn = g.pop('db_conn', None)
        if conn is not None:
            try:
                if exception is not None:
                    conn.rollback()
                else:
                    conn.rollback()
            finally:
                _get_pool().putconn(conn)

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
