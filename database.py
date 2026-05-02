"""Database engine, session, transactions, and seed data.

Stage 3 notes
-------------
* **Isolation level.** SQLite uses file-level locking for writes; with the
  default driver setting any write transaction effectively runs at
  ``SERIALIZABLE``. We explicitly set ``isolation_level="SERIALIZABLE"``
  on the engine so SQLAlchemy issues an explicit ``BEGIN`` for every
  unit of work — no surprise autocommits.
* **Foreign keys.** SQLite does not enforce ``FOREIGN KEY`` by default.
  We turn it on per-connection via ``PRAGMA foreign_keys=ON`` so the
  ``ON DELETE CASCADE`` we declared on ``enrollments`` actually fires.
* **Transactions.** ``app.py`` opens write paths with
  ``with SessionLocal.begin() as session: ...`` which commits on success
  and rolls back on any exception, keeping student + enrollment writes
  atomic.
"""

import os

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from models import Base, Course, Enrollment, Student

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cs348.db")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    isolation_level="SERIALIZABLE",
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _record):
    """Force SQLite to enforce FK constraints (off by default)."""
    cur = dbapi_connection.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create tables and indexes if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def seed_if_empty(session: Session) -> None:
    if session.execute(select(Course).limit(1)).scalars().first() is not None:
        return

    courses = [
        Course(code="CS348", title="Introduction to Database Management"),
        Course(code="CS240", title="Data Structures"),
        Course(code="MATH165", title="Calculus I"),
    ]
    session.add_all(courses)
    session.flush()

    students = [
        Student(full_name="Alex Chen", age=20, gpa=3.6),
        Student(full_name="Jordan Lee", age=22, gpa=3.2),
        Student(full_name="Sam Patel", age=19, gpa=3.9),
    ]
    session.add_all(students)
    session.flush()

    session.add_all(
        [
            Enrollment(student_id=students[0].student_id, course_id=courses[0].course_id),
            Enrollment(student_id=students[0].student_id, course_id=courses[1].course_id),
            Enrollment(student_id=students[1].student_id, course_id=courses[0].course_id),
            Enrollment(student_id=students[2].student_id, course_id=courses[2].course_id),
        ]
    )


def get_session() -> Session:
    return SessionLocal()
