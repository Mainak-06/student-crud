"""FastAPI app: Students Database CRUD (+ optional Ollama AI endpoint)."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status

from . import ai, crud
from .database import get_db, init_db
from .schemas import AIAnswer, AIQuestion, Student, StudentCreate, StudentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # creates the table on first run; data persists in students.db
    yield


app = FastAPI(
    title="Students Database API",
    description="CRUD API for student records (FastAPI + SQLite) with an optional local-AI endpoint.",
    version="1.0.0",
    lifespan=lifespan,
)


def _not_found(student_id: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"Student with id {student_id} not found")


def _guard_unique_email(db: sqlite3.Connection, email, own_id: Optional[int] = None):
    if not email:
        return
    row = db.execute("SELECT id FROM students WHERE email = ?", (str(email),)).fetchone()
    if row and row["id"] != own_id:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Email '{email}' is already registered")


@app.get("/", tags=["Health"])
def root():
    return {"message": "Students API is running. Open /docs for interactive documentation."}


# ---------- CREATE ----------
@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    _guard_unique_email(db, student.email)
    return crud.create_student(db, student.model_dump())


# ---------- READ (list + filter) ----------
@app.get("/students", response_model=list[Student], tags=["Students"])
def list_students(
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    email: Optional[str] = Query(None, description="Exact email"),
    born_after: Optional[date] = Query(None, description="DOB strictly after YYYY-MM-DD"),
    born_before: Optional[date] = Query(None, description="DOB strictly before YYYY-MM-DD"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.list_students(db, name, course, email, born_after, born_before, skip, limit)


# ---------- READ (single) ----------
@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
def get_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise _not_found(student_id)
    return student


# ---------- UPDATE (full replace) ----------
@app.put("/students/{student_id}", response_model=Student, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    if not crud.get_student(db, student_id):
        raise _not_found(student_id)
    _guard_unique_email(db, student.email, own_id=student_id)
    return crud.replace_student(db, student_id, student.model_dump())


# ---------- UPDATE (partial) ----------
@app.patch("/students/{student_id}", response_model=Student, tags=["Students"])
def update_student(student_id: int, changes: StudentUpdate, db: sqlite3.Connection = Depends(get_db)):
    existing = crud.get_student(db, student_id)
    if not existing:
        raise _not_found(student_id)
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No fields provided to update")
    _guard_unique_email(db, data.get("email"), own_id=student_id)
    merged_email = data["email"] if "email" in data else existing["email"]
    merged_phone = data["phone"] if "phone" in data else existing["phone"]
    if not merged_email and not merged_phone:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "A student must keep at least one contact (email or phone)")
    return crud.update_student(db, student_id, data)


# ---------- DELETE ----------
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Students"])
def delete_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise _not_found(student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- OPTIONAL BONUS: local AI via Ollama ----------
@app.post("/ai/ask", response_model=AIAnswer, tags=["AI (optional)"])
def ask_ai(body: AIQuestion, db: sqlite3.Connection = Depends(get_db)):
    """Backend retrieves records with safe, fixed queries; the model only writes the answer."""
    records, facts = ai.retrieve_context(db, body.question)
    try:
        answer = ai.ask_ollama(body.question, ai.format_context(facts, records))
    except ai.OllamaUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return AIAnswer(question=body.question, answer=answer, records_used=records, model=ai.OLLAMA_MODEL)
