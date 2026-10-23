"""All SQL lives here. Every query is parameterised (no SQL injection)."""
import sqlite3
from datetime import date
from typing import Optional

COLUMNS = ("name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date")


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _clean(data: dict) -> dict:
    """Convert date objects to ISO strings and email to str for SQLite."""
    out = {}
    for k, v in data.items():
        out[k] = v.isoformat() if isinstance(v, date) else (str(v) if v is not None else None)
    return out


def create_student(db: sqlite3.Connection, data: dict) -> dict:
    data = _clean(data)
    cur = db.execute(
        f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
        [data.get(c) for c in COLUMNS],
    )
    db.commit()
    return get_student(db, cur.lastrowid)


def get_student(db: sqlite3.Connection, student_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_students(
    db: sqlite3.Connection,
    name: Optional[str] = None,
    course: Optional[str] = None,
    email: Optional[str] = None,
    born_after: Optional[date] = None,
    born_before: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    sql, params = "SELECT * FROM students WHERE 1=1", []
    if name:
        sql += " AND name LIKE ?"; params.append(f"%{name}%")
    if course:
        sql += " AND course LIKE ?"; params.append(f"%{course}%")
    if email:
        sql += " AND email = ?"; params.append(email)
    if born_after:
        sql += " AND date_of_birth > ?"; params.append(born_after.isoformat())
    if born_before:
        sql += " AND date_of_birth < ?"; params.append(born_before.isoformat())
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params += [limit, skip]
    return [_row_to_dict(r) for r in db.execute(sql, params).fetchall()]


def count_students(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COUNT(*) FROM students").fetchone()[0]


def update_student(db: sqlite3.Connection, student_id: int, data: dict) -> Optional[dict]:
    data = _clean(data)
    if data:
        sets = ", ".join(f"{k} = ?" for k in data)
        db.execute(f"UPDATE students SET {sets} WHERE id = ?", [*data.values(), student_id])
        db.commit()
    return get_student(db, student_id)


def replace_student(db: sqlite3.Connection, student_id: int, data: dict) -> Optional[dict]:
    full = {c: data.get(c) for c in COLUMNS}  # missing optional fields become NULL
    return update_student(db, student_id, full)


def delete_student(db: sqlite3.Connection, student_id: int) -> bool:
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return cur.rowcount > 0
