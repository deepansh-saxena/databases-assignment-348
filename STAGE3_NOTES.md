# CS348 — Stage 3 technical notes

This document is the written companion to the Stage 3 demo. It explains the
four discussion items in the Stage 3 rubric so each can be cited directly in
the recording.

---

## 1. SQL Injection protection (rubric: 7%)

**Approach: parameterized queries via the SQLAlchemy ORM, plus type coercion
at the request boundary.**

### Where it happens

Every database access in `app.py` goes through the SQLAlchemy ORM/Core API
(`select(...)`, `session.add(...)`, `session.execute(delete(...).where(...))`,
`session.get(...)`). SQLAlchemy compiles those to **parameterized SQL** and
hands the values to the SQLite driver as bound parameters — they are *never*
concatenated into the SQL string. There is no raw `cursor.execute(f"... {x}")`
or `text("... " + x)` anywhere in the codebase.

### Concrete examples (cite these in the demo)

**The report endpoint** (`app.py`, `students_report`) — every filter is a
bound parameter:

```python
if min_age is not None:
    conditions.append(Student.age >= min_age)
if max_age is not None:
    conditions.append(Student.age <= max_age)
...
if course_id is not None:
    conditions.append(
        exists().where(
            and_(
                Enrollment.student_id == Student.student_id,
                Enrollment.course_id == course_id,
            )
        )
    )
```

The compiled SQL (verifiable with `echo=True` on the engine) looks like:

```
SELECT students.* FROM students
WHERE students.age  >= ?
  AND students.age  <= ?
  AND students.gpa  >= ?
  AND students.gpa  <= ?
  AND EXISTS (SELECT 1 FROM enrollments
              WHERE enrollments.student_id = students.student_id
                AND enrollments.course_id  = ?)
ORDER BY students.student_id;
```

The `?` placeholders are bound by the driver, so a value like
`Robert'); DROP TABLE students;--` is treated as a literal string.

**The student create/update endpoints** also coerce types defensively:

```python
try:
    age = int(age)
    gpa = float(gpa)
except (TypeError, ValueError):
    return jsonify({"error": "age and gpa must be numbers"}), 400
```

This means even a numeric field cannot smuggle SQL — non-numeric input is
rejected with HTTP 400 before it reaches the database.

### Demonstration in the demo

We send `{"full_name": "Robert'); DROP TABLE students;--", "age": 20,
"gpa": 3.0}` to `POST /api/students`. The row is inserted with the literal
name and the table is intact afterwards (`GET /api/students` still works).

### What this protects against

- Classic injection through string fields (name).
- Tautology-style injection through numeric/range fields (the type coercion
  rejects anything that doesn't `int()` / `float()`).
- Order-by / limit injection — the report's `ORDER BY` is a fixed expression
  in code, not user input.

---

## 2. Indexes (rubric: 6%)

All indexes are declared on the SQLAlchemy models in `models.py` and
created by `Base.metadata.create_all()` on first startup. **There is no
separate `CREATE INDEX` script — the indexes are part of the schema.**

| Index                          | Columns          | Query / report it supports                                                                                                                                                                                  |
|--------------------------------|------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `idx_students_age_gpa`         | `(age, gpa)`     | `GET /api/students/report` — the filtered students report (Requirement 2 from Stage 1/2).                                                                                                                   |
| `ix_courses_code` (UNIQUE)     | `(code)`         | `GET /api/courses` — populates the dynamic course checkboxes and the report's course dropdown (Requirement 3). Also enforces unique course codes.                                                           |
| `idx_enrollments_course_id`    | `(course_id)`    | (a) `GET /api/students/report?course_id=...` — the EXISTS subquery filters on `course_id`. (b) Cascade delete `DELETE FROM enrollments WHERE course_id=?` when a course is removed.                         |
| `sqlite_autoindex_enrollments_1` (implicit, from `UNIQUE(student_id, course_id)`) | `(student_id, course_id)` | (a) Listing one student's courses. (b) Cascade delete `DELETE FROM enrollments WHERE student_id=?` when a student is removed. Makes a separate `idx_enrollments_student_id` redundant — we deliberately omit it. |

### Justification with `EXPLAIN QUERY PLAN`

The plans below were captured against the seeded database; SQLite's planner
confirms each index is actually used.

```sql
-- Report (age + gpa filter)
EXPLAIN QUERY PLAN
SELECT * FROM students
WHERE age BETWEEN 18 AND 25 AND gpa BETWEEN 3.0 AND 4.0;
-- → SEARCH students USING INDEX idx_students_age_gpa (age>? AND age<?)

-- Report (course filter via EXISTS)
EXPLAIN QUERY PLAN
SELECT * FROM students s
WHERE EXISTS (SELECT 1 FROM enrollments e
              WHERE e.student_id = s.student_id AND e.course_id = 1);
-- → CORRELATED SCALAR SUBQUERY
--   SEARCH e USING COVERING INDEX sqlite_autoindex_enrollments_1
--          (student_id=? AND course_id=?)

-- Cascade delete on a course
EXPLAIN QUERY PLAN
DELETE FROM enrollments WHERE course_id = 1;
-- → SEARCH enrollments USING COVERING INDEX idx_enrollments_course_id (course_id=?)

-- Courses dropdown / checkbox source
EXPLAIN QUERY PLAN
SELECT * FROM courses ORDER BY code;
-- → SCAN courses USING INDEX ix_courses_code
```

### Why this set is "meaningful" (per rubric language)

- Every index is tied to a **specific** endpoint or a foreign-key cascade
  path, not added speculatively.
- Redundant indexes were removed: `idx_enrollments_student_id` is **not**
  created because the `UNIQUE(student_id, course_id)` index already covers
  any `student_id`-leading lookup.
- The composite `(age, gpa)` is preferred over two single-column indexes so
  the report's range-on-range filter can be served by one index lookup.

---

## 3. Transactions and isolation level (rubric: 6%)

### Isolation level

`database.py` constructs the engine as:

```python
engine = create_engine(DATABASE_URL, echo=False, isolation_level="SERIALIZABLE")
```

Why **SERIALIZABLE**:

- SQLite uses **file-level / database-level write locking**. While a write
  transaction is in progress, no other connection can write, and (with
  default journal mode) other connections also cannot read uncommitted
  state. That behaviour is effectively SERIALIZABLE — there is no anomaly
  that a higher isolation level would prevent, and no benefit to relaxing
  to a lower level.
- Setting it explicitly on the engine makes SQLAlchemy issue an explicit
  `BEGIN` per unit of work and prevents the Python `sqlite3` driver's
  default-autocommit surprises.

### Where transactions are used in the application

The write paths touch **two tables in one operation** (a student row and
its enrollment rows). Those must be atomic — if an enrollment insert fails
we don't want a half-written student. They are wrapped with
`SessionLocal.begin()`, which commits on success and rolls back on any
exception:

```python
# POST /api/students  — create
with SessionLocal.begin() as session:
    student = Student(full_name=name, age=age, gpa=gpa)
    session.add(student)
    session.flush()
    for cid in course_ids:
        ...
        session.add(Enrollment(student_id=student.student_id, course_id=cid_int))
# implicit COMMIT here on success, ROLLBACK on exception
```

```python
# PUT /api/students/<id>  — update + replace enrollments
with SessionLocal.begin() as session:
    student = session.get(Student, sid)
    ...
    if "course_ids" in body:
        session.execute(delete(Enrollment).where(Enrollment.student_id == sid))
        for cid in body["course_ids"] or []:
            ...
            session.add(Enrollment(student_id=sid, course_id=cid_int))
```

```python
# DELETE /api/students/<id>  — student + cascade-delete enrollments
with SessionLocal.begin() as session:
    student = session.get(Student, sid)
    if not student:
        return jsonify({"error": "not found"}), 404
    session.delete(student)
```

### Concurrent access

Although the demo is shown as a single-user application, the design above
*does* tolerate concurrent users:

- Each HTTP request runs its own `Session` and its own transaction.
- SQLite's locking serialises writers; readers see a consistent snapshot
  of the database (no dirty / non-repeatable reads).
- We turned on `PRAGMA foreign_keys=ON` so the cascade behaviour described
  in the schema actually fires inside the transaction — without it, SQLite
  would silently leave orphan enrollment rows on a student delete.

### Anomaly the design prevents

If two TAs simultaneously update the same student's GPA and course list, the
SERIALIZABLE behaviour means the second writer waits for the first to
commit, then sees the new state when it begins — there is no "lost update"
of either field.

---

## 4. AI usage

See [`AI_USAGE.md`](./AI_USAGE.md) for the required disclosure (tools,
tasks, verification process). The demo recording also covers this verbally
as required by the rubric.
