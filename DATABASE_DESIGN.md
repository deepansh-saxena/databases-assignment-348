# Database design (relational)

SQLite database file: `cs348.db` (created automatically when the Flask app starts).

## Tables, primary keys, and foreign keys

### `courses`

| Column      | Type         | Constraints                                       |
|-------------|--------------|---------------------------------------------------|
| `course_id` | INTEGER      | **PRIMARY KEY**, autoincrement                    |
| `code`      | VARCHAR(32)  | NOT NULL, **UNIQUE** (creates `ix_courses_code`)  |
| `title`     | VARCHAR(200) | NOT NULL                                          |

### `students`

| Column       | Type         | Constraints                    |
|--------------|--------------|--------------------------------|
| `student_id` | INTEGER      | **PRIMARY KEY**, autoincrement |
| `full_name`  | VARCHAR(120) | NOT NULL                       |
| `age`        | INTEGER      | NOT NULL                       |
| `gpa`        | FLOAT        | NOT NULL                       |

### `enrollments` (many-to-many between students and courses)

| Column          | Type    | Constraints                                                                |
|-----------------|---------|----------------------------------------------------------------------------|
| `enrollment_id` | INTEGER | **PRIMARY KEY**, autoincrement                                             |
| `student_id`    | INTEGER | **FOREIGN KEY** → `students(student_id)` ON DELETE CASCADE, NOT NULL       |
| `course_id`     | INTEGER | **FOREIGN KEY** → `courses(course_id)` ON DELETE CASCADE, NOT NULL         |

**Unique constraint:** `(student_id, course_id)` — a student cannot enroll in the same course twice.
SQLite materialises this as the implicit index `sqlite_autoindex_enrollments_1` on
`(student_id, course_id)`, which is also used as a covering index for any query that
filters by `student_id` (see Indexes below).

## Relationships

- One **student** has many **enrollments**; one **course** has many **enrollments**.
- Deleting a student removes their enrollment rows (`ON DELETE CASCADE`).
- Deleting a course removes the related enrollment rows (`ON DELETE CASCADE`).
- FK enforcement is enabled at runtime via `PRAGMA foreign_keys=ON` (SQLite has it
  off by default). See `database.py`.

## Indexes (Stage 3)

All indexes are declared on the SQLAlchemy models in `models.py` and created by
`Base.metadata.create_all()` on first startup.

| Index                          | Table        | Columns          | Query / report it supports |
|--------------------------------|--------------|------------------|---------------------------|
| `idx_students_age_gpa`         | students     | `(age, gpa)`     | `GET /api/students/report` — the filtered students report (Requirement 2). The composite is leading-column friendly: queries that supply only an age range still use the leading prefix. Verified with `EXPLAIN QUERY PLAN` → `SEARCH students USING INDEX idx_students_age_gpa (age>? AND age<?)`. |
| `ix_courses_code` (UNIQUE)     | courses      | `(code)`         | `GET /api/courses` — populates the dynamic course checkboxes and the report's course dropdown (Requirement 3). Backs `ORDER BY code` (planner output: `SCAN courses USING INDEX ix_courses_code`). Also enforces "no duplicate course codes". |
| `idx_enrollments_course_id`    | enrollments  | `(course_id)`    | (1) `GET /api/students/report?course_id=...` — the EXISTS subquery filters by `course_id`. (2) The cascade delete `DELETE FROM enrollments WHERE course_id = ?` that fires when a course is removed (without this index SQLite would full-scan `enrollments`). |
| `sqlite_autoindex_enrollments_1` (implicit) | enrollments | `(student_id, course_id)` | Created automatically by the `UNIQUE(student_id, course_id)` constraint. Serves any lookup whose leading predicate is `student_id`, including: serializing one student's courses (`/api/students`, `/api/students/<id>`), and the cascade delete `DELETE FROM enrollments WHERE student_id = ?` when a student is removed. Because of this we do **not** create a separate `idx_enrollments_student_id` — it would be redundant. |

## How this supports the demos

1. **CRUD (Requirement 1):** Insert, update, and delete rows in `students`; the
   accompanying enrollments are written/replaced/cleared in the **same
   transaction** (`SessionLocal.begin()` in `app.py`).
2. **Filtered report (Requirement 2):** `students` filtered on `age`/`gpa`
   ranges (using `idx_students_age_gpa`) plus an optional `course_id` filter
   served by an EXISTS subquery on `enrollments` (using
   `idx_enrollments_course_id` / the unique index, depending on selectivity).
3. **Dynamic UI (Requirement 3):** Course labels in the React app come from
   `GET /api/courses` (table `courses`), not from hard-coded arrays in the
   frontend. The query is `SELECT * FROM courses ORDER BY code`, served by
   `ix_courses_code`.
