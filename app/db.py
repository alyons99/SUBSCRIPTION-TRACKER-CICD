"""SQLite connection handling."""

import os
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    cost          REAL    NOT NULL,
    billing_cycle TEXT    NOT NULL,
    renewal_date  TEXT    NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    path = app.config["DATABASE"]
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)


def init_app(app):
    init_db(app)
    app.teardown_appcontext(close_db)
