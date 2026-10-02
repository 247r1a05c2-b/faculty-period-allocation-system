import os
from flask import g
import psycopg2
from psycopg2.extras import RealDictCursor

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
        return conn

mysql = PostgresDB()
