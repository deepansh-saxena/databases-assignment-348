"""Flask + SQLAlchemy backend for CS348 project.

Stage 3 — security & correctness highlights
-------------------------------------------
* **SQL injection protection.** Every database access in this file goes
  through SQLAlchemy Core / ORM, which uses **parameterized (bound) SQL
  statements** under the hood — user-supplied values are sent to SQLite
  as parameters, never interpolated into the SQL string. We also do
  defensive type coercion (``int(...)`` / ``float(...)``) on inputs and
  return ``400 Bad Request`` on malformed values, so even non-string
  fields cannot smuggle SQL.
* **Transactions.** Multi-row write paths (``POST``/``PUT``/``DELETE``
  on students, which also touch the ``enrollments`` table) are wrapped
  with ``SessionLocal.begin()`` so the student row and its enrollments
  commit or roll back together.
* **Indexes.** Defined on the model classes (see ``models.py``); each
  index is tied to a specific endpoint:
    - ``idx_students_age_gpa``      → ``GET /api/students/report``
    - ``idx_enrollments_course_id`` → ``GET /api/students/report?course_id=...``
    - ``idx_enrollments_student_id`` → per-student course list join
    - ``idx_courses_code (UNIQUE)`` → ``GET /api/courses`` (dropdown source)
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import and_, delete, exists, select
from sqlalchemy.orm import joinedload

from database import SessionLocal, get_session, init_db, seed_if_empty
from models import Course, Enrollment, Student

app = Flask(__name__)
CORS(app)

_db_initialized = False


@app.before_request
def ensure_db() -> None:
    """Lazy init so imports do not require DB file at import time."""
    global _db_initialized
    if _db_initialized:
        return
    init_db()
    s = get_session()
    try:
        seed_if_empty(s)
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
    _db_initialized = True


def _student_to_dict(student: Student, include_courses: bool = True) -> dict:
    data = {
        "student_id": student.student_id,
        "full_name": student.full_name,
        "age": student.age,
        "gpa": round(float(student.gpa), 2),
    }
    if include_courses and student.enrollments:
        data["courses"] = [
            {
                "course_id": e.course.course_id,
                "code": e.course.code,
                "title": e.course.title,
            }
            for e in student.enrollments
        ]
    else:
        data["courses"] = []
    return data


@app.route("/api/courses", methods=["GET"])
def list_courses():
    """Powers the dynamic checkboxes/dropdown in the React UI.

    Uses ``ORDER BY code`` which is served by the unique index
    ``idx_courses_code``.
    """
    with SessionLocal() as session:
        rows = session.execute(select(Course).order_by(Course.code)).scalars().all()
        return jsonify(
            [
                {"course_id": c.course_id, "code": c.code, "title": c.title}
                for c in rows
            ]
        )


@app.route("/api/students", methods=["GET"])
def list_students():
    with SessionLocal() as session:
        q = (
            select(Student)
            .options(joinedload(Student.enrollments).joinedload(Enrollment.course))
            .order_by(Student.student_id)
        )
        rows = session.execute(q).unique().scalars().all()
        return jsonify([_student_to_dict(s) for s in rows])


@app.route("/api/students", methods=["POST"])
def create_student():
    """Insert one student + their enrollments inside a single transaction."""
    body = request.get_json(silent=True) or {}
    name = (body.get("full_name") or "").strip()
    age = body.get("age")
    gpa = body.get("gpa")
    course_ids = body.get("course_ids") or []

    if not name:
        return jsonify({"error": "full_name is required"}), 400
    try:
        age = int(age)
        gpa = float(gpa)
    except (TypeError, ValueError):
        return jsonify({"error": "age and gpa must be numbers"}), 400

    # SessionLocal.begin() opens an explicit BEGIN; the block commits on
    # success and rolls back if any exception escapes. If an enrollment
    # row blows up (e.g., FK violation) the new student row is undone too.
    with SessionLocal.begin() as session:
        student = Student(full_name=name, age=age, gpa=gpa)
        session.add(student)
        session.flush()
        for cid in course_ids:
            try:
                cid_int = int(cid)
            except (TypeError, ValueError):
                continue
            if session.get(Course, cid_int):
                session.add(
                    Enrollment(student_id=student.student_id, course_id=cid_int)
                )
        new_id = student.student_id

    with SessionLocal() as session:
        st = (
            session.execute(
                select(Student)
                .where(Student.student_id == new_id)
                .options(joinedload(Student.enrollments).joinedload(Enrollment.course))
            )
            .unique()
            .scalar_one()
        )
        return jsonify(_student_to_dict(st)), 201


@app.route("/api/students/<int:sid>", methods=["PUT"])
def update_student(sid: int):
    """Update student fields and (optionally) replace enrollments atomically."""
    body = request.get_json(silent=True) or {}

    with SessionLocal.begin() as session:
        student = session.get(Student, sid)
        if not student:
            return jsonify({"error": "not found"}), 404
        if "full_name" in body:
            student.full_name = (body["full_name"] or "").strip() or student.full_name
        if "age" in body:
            try:
                student.age = int(body["age"])
            except (TypeError, ValueError):
                return jsonify({"error": "age must be an integer"}), 400
        if "gpa" in body:
            try:
                student.gpa = float(body["gpa"])
            except (TypeError, ValueError):
                return jsonify({"error": "gpa must be a number"}), 400
        if "course_ids" in body:
            session.execute(delete(Enrollment).where(Enrollment.student_id == sid))
            for cid in body["course_ids"] or []:
                try:
                    cid_int = int(cid)
                except (TypeError, ValueError):
                    continue
                if session.get(Course, cid_int):
                    session.add(Enrollment(student_id=sid, course_id=cid_int))

    with SessionLocal() as session:
        st = (
            session.execute(
                select(Student)
                .where(Student.student_id == sid)
                .options(joinedload(Student.enrollments).joinedload(Enrollment.course))
            )
            .unique()
            .scalar_one()
        )
        return jsonify(_student_to_dict(st))


@app.route("/api/students/<int:sid>", methods=["DELETE"])
def delete_student(sid: int):
    """Delete one student; CASCADE removes their enrollments in the same tx."""
    with SessionLocal.begin() as session:
        student = session.get(Student, sid)
        if not student:
            return jsonify({"error": "not found"}), 404
        session.delete(student)
    return jsonify({"ok": True, "deleted_id": sid})


@app.route("/api/students/report", methods=["GET"])
def students_report():
    """Filter students by age range, GPA range, and optional course.

    SQL shape (parameterized — values shown as ``:name`` are bound, NEVER
    string-interpolated):

        SELECT students.* FROM students
        WHERE students.age BETWEEN :min_age AND :max_age   -- if provided
          AND students.gpa BETWEEN :min_gpa AND :max_gpa   -- if provided
          AND EXISTS (
                SELECT 1 FROM enrollments
                WHERE enrollments.student_id = students.student_id
                  AND enrollments.course_id  = :course_id  -- if provided
          )
        ORDER BY students.student_id;

    Indexes used:
      * ``idx_students_age_gpa`` — supports the age/gpa range predicates.
      * ``idx_enrollments_course_id`` — supports the EXISTS subquery
        when filtering by course.
    """
    def _float_arg(name: str, default: float | None) -> float | None:
        v = request.args.get(name)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except ValueError:
            return None

    def _int_arg(name: str, default: int | None) -> int | None:
        v = request.args.get(name)
        if v is None or v == "":
            return default
        try:
            return int(v)
        except ValueError:
            return None

    min_age = _int_arg("min_age", None)
    max_age = _int_arg("max_age", None)
    min_gpa = _float_arg("min_gpa", None)
    max_gpa = _float_arg("max_gpa", None)
    course_id = _int_arg("course_id", None)

    with SessionLocal() as session:
        q = select(Student).options(
            joinedload(Student.enrollments).joinedload(Enrollment.course)
        )
        conditions = []
        if min_age is not None:
            conditions.append(Student.age >= min_age)
        if max_age is not None:
            conditions.append(Student.age <= max_age)
        if min_gpa is not None:
            conditions.append(Student.gpa >= min_gpa)
        if max_gpa is not None:
            conditions.append(Student.gpa <= max_gpa)
        if course_id is not None:
            # EXISTS subquery — pushes the course filter into SQL so
            # idx_enrollments_course_id can be used by the planner.
            conditions.append(
                exists().where(
                    and_(
                        Enrollment.student_id == Student.student_id,
                        Enrollment.course_id == course_id,
                    )
                )
            )
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(Student.student_id)

        rows = session.execute(q).unique().scalars().all()

        return jsonify(
            {
                "filters": {
                    "min_age": min_age,
                    "max_age": max_age,
                    "min_gpa": min_gpa,
                    "max_gpa": max_gpa,
                    "course_id": course_id,
                },
                "count": len(rows),
                "students": [_student_to_dict(s) for s in rows],
            }
        )


@app.route("/api/versions")
def versions():
    import flask
    import sqlalchemy
    import sys

    return jsonify(
        {
            "Python": sys.version,
            "Flask": flask.__version__,
            "SQLAlchemy": sqlalchemy.__version__,
            "status": "All components installed successfully!",
        }
    )


if __name__ == "__main__":
    # Port 5050 (not 5000) because macOS AirPlay Receiver squats on :5000.
    app.run(debug=True, port=5050)
