# Students Database CRUD API

Python backend for managing student records: **FastAPI + SQLite**, with an optional **local AI (Ollama)** endpoint.
Built for the EWB Edu Tech internship project. All sample data is dummy data.

## Features
- **Create / Read / Update / Delete** students (full CRUD)
- Filtering: by name, course, email, born_after, born_before + pagination (`skip`, `limit`)
- Input validation (email format, phone format, DOB in the past, at least one contact)
- Proper errors: `404` missing record, `409` duplicate email, `422` invalid input
- SQLite persistence (`students.db`, created automatically)
- Auto docs at `/docs` (Swagger UI)
- Optional: `POST /ai/ask` answers natural-language questions using Ollama

## Project structure
```
app/
  main.py      # FastAPI routes
  schemas.py   # Pydantic models / validation
  crud.py      # All SQL (parameterised queries)
  database.py  # SQLite connection + table creation
  ai.py        # Optional Ollama integration
tests/test_api.py
seed.py        # loads dummy sample data
requirements.txt
```

## Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.com) for the AI bonus

## Installation
```bash
git clone https://github.com/Mainak-06/student-crud.git
cd student-crud
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to test every endpoint in the browser.

Optional dummy data:
```bash
python seed.py
```

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students` | Create a student |
| GET | `/students` | List / filter students |
| GET | `/students/{id}` | View one student |
| PUT | `/students/{id}` | Replace all details |
| PATCH | `/students/{id}` | Update some details |
| DELETE | `/students/{id}` | Delete a student |
| POST | `/ai/ask` | (Optional) Ask AI about the data |

Filters: `GET /students?name=aar&course=python&born_after=2005-01-01&born_before=2008-01-01&skip=0&limit=10`

## Sample requests (curl)
```bash
# Create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"Aarav Sharma","date_of_birth":"2003-05-14","email":"aarav@example.com","phone":"+91 90000 00001","course":"Python Backend"}'

# List all / filter
curl http://127.0.0.1:8000/students
curl "http://127.0.0.1:8000/students?born_after=2005-01-01"

# Get one
curl http://127.0.0.1:8000/students/1

# Partial update
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" -d '{"course":"Data Science"}'

# Full update
curl -X PUT http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" \
  -d '{"name":"Aarav S","date_of_birth":"2003-05-14","email":"aarav@example.com"}'

# Delete (returns 204)
curl -X DELETE http://127.0.0.1:8000/students/1
```

## Run tests
```bash
pytest -q
```

## Optional: Local AI with Ollama
```bash
ollama pull llama3.2:1b
ollama serve            # keep running
python seed.py
uvicorn app.main:app --reload
```
```bash
curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" \
  -d '{"question":"List students born after 2005"}'
```
Response includes the `answer` and the exact `records_used` it was grounded on.

**How it stays safe and accurate**
1. The model never writes or runs SQL.
2. Backend code detects the question type (count, born before/after/in a year, course) and runs a fixed, parameterised query.
3. Only those retrieved rows are given to the model, which is told to answer from them only.
4. If Ollama is not running, the endpoint returns a clear `503` message (the CRUD API is unaffected).

Config via env vars: `OLLAMA_URL` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3.2:1b`), `STUDENTS_DB_PATH` (default `students.db`).

## Security notes
- No secrets or real student data in the repo; `*.db` is git-ignored.
- All SQL uses parameter binding.
