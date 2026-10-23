import os
import tempfile

os.environ["STUDENTS_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

GOOD = {"name": "Test User", "date_of_birth": "2004-04-04",
        "email": "t@example.com", "course": "Python"}


def test_full_crud_flow():
    with TestClient(app) as c:
        r = c.post("/students", json=GOOD)
        assert r.status_code == 201
        sid = r.json()["id"]

        assert c.get(f"/students/{sid}").json()["name"] == "Test User"
        assert len(c.get("/students").json()) == 1
        assert len(c.get("/students?course=pyth").json()) == 1
        assert len(c.get("/students?born_after=2005-01-01").json()) == 0

        r = c.patch(f"/students/{sid}", json={"course": "Data Science"})
        assert r.json()["course"] == "Data Science"

        r = c.put(f"/students/{sid}", json={**GOOD, "name": "Renamed"})
        assert r.json()["name"] == "Renamed"

        assert c.delete(f"/students/{sid}").status_code == 204
        assert c.get(f"/students/{sid}").status_code == 404


def test_validation_and_errors():
    with TestClient(app) as c:
        assert c.post("/students", json={**GOOD, "email": "bad"}).status_code == 422
        assert c.post("/students", json={"name": "X Y", "date_of_birth": "2004-01-01"}).status_code == 422
        assert c.post("/students", json={**GOOD, "date_of_birth": "2999-01-01"}).status_code == 422
        assert c.post("/students", json={**GOOD, "email": "dup@example.com"}).status_code == 201
        assert c.post("/students", json={**GOOD, "email": "dup@example.com"}).status_code == 409
        assert c.get("/students/9999").status_code == 404
        assert c.delete("/students/9999").status_code == 404
        assert c.patch("/students/9999", json={"name": "Nope"}).status_code == 404
