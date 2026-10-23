"""Optional Ollama extension.

SECURITY DESIGN: the model NEVER writes or runs SQL. Our code decides which
fixed, parameterised query to run (via simple intent detection), then hands
the retrieved rows to the model purely as text context.
"""
import json
import os
import re
import sqlite3
from datetime import date

import httpx

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_RECORDS = 50


class OllamaUnavailable(Exception):
    pass


def retrieve_context(db: sqlite3.Connection, question: str) -> tuple[list[dict], str]:
    """Return (records, facts_text) using safe, fixed queries."""
    q = question.lower()
    total = crud.count_students(db)
    facts = [f"Total students in database: {total}."]
    records: list[dict] = []

    year = re.search(r"\b(19\d{2}|20\d{2})\b", q)
    if year and re.search(r"born|birth|dob", q):
        y = int(year.group(1))
        if re.search(r"after|since|later than", q):
            records = crud.list_students(db, born_after=date(y, 12, 31), limit=MAX_RECORDS)
            facts.append(f"Students born after {y}: {len(records)} match.")
        elif re.search(r"before|earlier than", q):
            records = crud.list_students(db, born_before=date(y, 1, 1), limit=MAX_RECORDS)
            facts.append(f"Students born before {y}: {len(records)} match.")
        else:  # born in a specific year
            records = crud.list_students(db, born_after=date(y - 1, 12, 31),
                                         born_before=date(y + 1, 1, 1), limit=MAX_RECORDS)
            facts.append(f"Students born in {y}: {len(records)} match.")
    else:
        courses = [r["course"] for r in db.execute(
            "SELECT DISTINCT course FROM students WHERE course IS NOT NULL").fetchall()]
        matched = [c for c in courses if c.lower() in q]
        if matched:
            records = crud.list_students(db, course=matched[0], limit=MAX_RECORDS)
            facts.append(f"Students in course '{matched[0]}': {len(records)} match.")
        else:
            records = crud.list_students(db, limit=MAX_RECORDS)
            facts.append(f"Showing up to {MAX_RECORDS} students.")
    return records, "\n".join(facts)


def format_context(facts: str, records: list[dict]) -> str:
    lines = [facts, "", "Records:"]
    for r in records:
        lines.append(f"- id={r['id']}, name={r['name']}, dob={r['date_of_birth']}, "
                     f"course={r['course']}, email={r['email']}")
    return "\n".join(lines)


def ask_ollama(question: str, context: str) -> str:
    prompt = (
        "You are an assistant for a students database. Answer ONLY using the data "
        "below. If the data does not contain the answer, say you don't know. "
        "Be concise.\n\n"
        f"DATA:\n{context}\n\nQUESTION: {question}\nANSWER:"
    )
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0}},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()
    except (httpx.ConnectError, httpx.TimeoutException):
        raise OllamaUnavailable(
            f"Cannot reach Ollama at {OLLAMA_URL}. Start it with 'ollama serve' "
            f"and pull the model with 'ollama pull {OLLAMA_MODEL}'.")
    except (httpx.HTTPStatusError, KeyError, json.JSONDecodeError) as exc:
        raise OllamaUnavailable(f"Ollama error: {exc}. Is the model '{OLLAMA_MODEL}' pulled?")
