"""Load DUMMY sample data (no real personal information)."""
from datetime import date

from app import crud
from app.database import _connect, init_db

SAMPLE = [
    ("Aarav Sharma", "2003-05-14", "aarav@example.com", "+91 90000 00001", "Python Backend", "Kolkata", "2024-07-01"),
    ("Diya Patel", "2005-11-02", "diya@example.com", "+91 90000 00002", "Data Science", "Mumbai", "2024-07-01"),
    ("Rohan Das", "2006-03-21", "rohan@example.com", None, "Python Backend", "Howrah", "2024-08-10"),
    ("Sneha Roy", "2004-09-30", None, "+91 90000 00004", "Web Development", "Kolkata", "2024-08-10"),
    ("Kabir Singh", "2007-01-15", "kabir@example.com", "+91 90000 00005", "Data Science", "Delhi", "2025-01-05"),
]

if __name__ == "__main__":
    init_db()
    conn = _connect()
    for n, dob, em, ph, co, ad, en in SAMPLE:
        try:
            crud.create_student(conn, dict(
                name=n, date_of_birth=date.fromisoformat(dob), email=em, phone=ph,
                course=co, address=ad, enrollment_date=date.fromisoformat(en)))
            print("added", n)
        except Exception as e:
            print("skipped", n, "-", e)
    conn.close()
