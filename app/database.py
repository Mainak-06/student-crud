"""SQLite connection handling and schema setup."""
import os
import sqlite3
from typing import Iterator

DB_PATH = os.getenv("STUDENTS_DB_PATH", "students.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    date_of_birth   TEXT NOT NULL,          -- ISO format YYYY-MM-DD
    email           TEXT UNIQUE,
    phone           TEXT,
    course          TEXT,
    address         TEXT,
    enrollment_date TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request."""
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()
