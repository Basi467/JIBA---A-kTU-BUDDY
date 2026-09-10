from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from auth_engine import COMPLETE_SUBJECT_FILTER
from db_path import get_db_path

router = APIRouter(prefix="/meta", tags=["meta"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = get_db_path()


class DepartmentOptions(BaseModel):
    department: str
    semesters: List[int]


class SchemeOptions(BaseModel):
    scheme: str
    departments: List[DepartmentOptions]


@router.get("/signup-options", response_model=List[SchemeOptions])
def signup_options():
    """Only returns (scheme, department, semester) combinations that have at
    least one fully-complete subject, so the registration form can never lead
    a student to an empty dashboard."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT DISTINCT scheme, department, semester
            FROM subjects s
            WHERE {COMPLETE_SUBJECT_FILTER}
            ORDER BY scheme, department, semester
            """
        ).fetchall()
    finally:
        conn.close()

    grouped: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["scheme"]][row["department"]].append(row["semester"])

    return [
        SchemeOptions(
            scheme=scheme,
            departments=[
                DepartmentOptions(department=dept, semesters=semesters)
                for dept, semesters in departments.items()
            ],
        )
        for scheme, departments in grouped.items()
    ]
