# CS348 Stage 3 — Demo notes

A loose 7–9 minute walkthrough (5–10 is the hard limit). Use these as
**talking points**, not a script — phrase them in your own words while you
point at the code.

Required topics (rubric):

1. SQL injection protection (7%)
2. Indexes — each one tied to a specific query/report (6%)
3. Transactions, concurrent access, isolation level (6%)
4. AI usage (6%)
5. *Optional extra credit:* a live cloud URL (1% of the course grade)

The grader wants to see the code on screen for each topic. Open the file,
scroll to the line, talk about it.

---

## Before recording

- Optional: `rm cs348.db` so the seed runs visibly when Flask boots.
- Have these files findable: `app.py`, `models.py`, `database.py`,
  `DATABASE_DESIGN.md`, `STAGE3_NOTES.md`, `AI_USAGE.md`,
  `frontend/src/App.js`.
- Two terminals open — project root and `frontend/`. A third for `sqlite3`
  is handy.

---

## 0:00 — How to run

Show on camera:

```bash
# Terminal 1
pip3 install -r requirements.txt
python3 app.py        # Running on http://127.0.0.1:5050
```

```bash
# Terminal 2
cd frontend
npm install           # first time only
npm start             # http://localhost:3000
```

Heads-up to mention: **port 5050, not 5000** — macOS AirPlay Receiver
binds 5000, so the Flask port and the React proxy in
`frontend/package.json` both use 5050. On Linux/Windows you can use 5000.

Always start Flask first, since the React dev server proxies `/api/*`
to it.

---

## 0:45 — One-line context

Same project as Stage 2 — Flask + SQLAlchemy + SQLite, React frontend.
CRUD on students and the filtered report still work. Stage 3 added the
indexes and the explicit transactions; both are written up in
`STAGE3_NOTES.md`.

(Flash `STAGE3_NOTES.md` so the grader sees it.)

---

## 1:15 — SQL injection (7%)

**Two layers of defence:** parameterized queries through SQLAlchemy, plus
type coercion at the request boundary.

Open `app.py` → `students_report`:

- Point at the `Student.age >= min_age`, `Student.gpa <= max_gpa`,
  `Enrollment.course_id == course_id` expressions.
- These are SQLAlchemy expressions — they compile to bound `?`
  parameters, never f-strings or string concat.

Open `app.py` → `create_student`:

- Point at the `int(age)` / `float(gpa)` coercion. Anything non-numeric
  returns 400 before it touches the DB.

**Live demo** (terminal):

```bash
curl -X POST http://127.0.0.1:5050/api/students \
     -H 'Content-Type: application/json' \
     -d "{\"full_name\":\"Robert'); DROP TABLE students;--\",\"age\":20,\"gpa\":3.0}"
curl http://127.0.0.1:5050/api/students | head -c 400
```

What to point out:

- The student is stored with the literal name — no quoting tricks
  executed.
- `students` table is intact.

That's the parameterized-query claim verified end-to-end, not just
asserted.

---

## 3:00 — Indexes (6%)

Indexes live on the SQLAlchemy models, created by
`Base.metadata.create_all()` at startup — schema and indexes ship
together.

Open `models.py` and walk through the four:

- `idx_students_age_gpa` on `students(age, gpa)` → the filtered
  students report (`GET /api/students/report`).
- `ix_courses_code` UNIQUE on `courses(code)` → `GET /api/courses`
  (powers the dynamic course checkboxes — Requirement 3).
- `idx_enrollments_course_id` on `enrollments(course_id)` → the
  optional `course_id` filter, and the cascade DELETE when a course is
  removed.
- The implicit `sqlite_autoindex_enrollments_1` from
  `UNIQUE(student_id, course_id)` → listing one student's courses, plus
  the cascade DELETE when a student is removed. Mention I deliberately
  do **not** add a separate `idx_enrollments_student_id` — the unique
  index already covers it.

**Prove the planner uses them** in a SQLite shell:

```bash
sqlite3 cs348.db
```

```sql
EXPLAIN QUERY PLAN
SELECT * FROM students
WHERE age BETWEEN 18 AND 25 AND gpa BETWEEN 3.0 AND 4.0;
-- SEARCH students USING INDEX idx_students_age_gpa

EXPLAIN QUERY PLAN
SELECT * FROM students s
WHERE EXISTS (SELECT 1 FROM enrollments e
              WHERE e.student_id = s.student_id AND e.course_id = 1);
-- COVERING INDEX sqlite_autoindex_enrollments_1 (student_id=? AND course_id=?)

EXPLAIN QUERY PLAN
DELETE FROM enrollments WHERE course_id = 1;
-- SEARCH enrollments USING INDEX idx_enrollments_course_id

EXPLAIN QUERY PLAN
SELECT * FROM courses ORDER BY code;
-- SCAN courses USING INDEX ix_courses_code
```

For each plan, just say which index the planner picked and which
endpoint it serves.

---

## 5:00 — Transactions & isolation (6%)

Open `database.py`:

- `create_engine(..., isolation_level="SERIALIZABLE")` — set explicitly
  so SQLAlchemy issues a real `BEGIN` per request and we sidestep the
  Python `sqlite3` driver's autocommit defaults. SQLite already
  serialises writers via its file lock, so SERIALIZABLE is a no-cost
  match.
- The `_enable_sqlite_fk` listener turns on `PRAGMA foreign_keys=ON`
  per connection. Without it, the `ON DELETE CASCADE` on enrollments
  silently does nothing.

Open `app.py` → `create_student`:

- Point at `with SessionLocal.begin() as session:` — this opens a
  transaction that commits on success and rolls back on any exception.
  So inserting the student row plus its enrollment rows is **atomic**:
  if any FK or unique check fails on an enrollment, the new student is
  undone too.

Show the same `SessionLocal.begin()` in `update_student` (deletes the
old enrollments and inserts the new ones in one transaction) and in
`delete_student` (the cascade fires inside the same tx).

**Concurrent access:** even though I'm a single user during the demo,
each request gets its own session and transaction; SQLite serialises
writers via its file lock; readers see a consistent snapshot. Two
people editing the same student at the same time can't lose updates —
the second writer waits and sees the committed state.

---

## 7:00 — AI usage (6%)

Open `AI_USAGE.md` and talk through it in your own words. Hit the three
required bullets:

- **Tools:** Cursor (with its built-in Claude assistant); occasional
  ChatGPT for SQLAlchemy 2.0 / SQLite isolation rubber-ducking.
- **What it helped with:** scaffolding, SQLAlchemy 2.0 syntax,
  brainstorming index candidates, drafting the demo notes and the
  `STAGE3_NOTES.md` write-up.
- **How I verified:** ran every endpoint with `curl`, ran
  `EXPLAIN QUERY PLAN` myself for every index claim, sent the
  `'); DROP TABLE students;--` payload to verify the SQL injection
  defence end-to-end, and cross-checked SQLAlchemy and SQLite docs.

A concrete "I overrode the AI" example that lands well: removed an
`idx_enrollments_student_id` the AI suggested, because the unique
index already covered the same access pattern.

Close with: "I can explain and justify every part of this project."

---

## 8:00 — Optional: live functional check

Switch to the browser at `http://localhost:3000` and reinforce that the
rubric items are live, not just on slides.

1. Run the report with min age 18, max age 25, min GPA 3.0, max GPA 4.0
   — show the count.
2. Edit a student's GPA so they fall outside the range, click **Update**,
   re-run the report — count drops by one.
3. Pick a course in the dropdown and re-run — the index-backed course
   filter narrows it further.

Each click goes through `SessionLocal.begin()` for writes,
parameterized SQL on the backend, and `idx_students_age_gpa` for the
read.

---

## 8:45 — Wrap-up

One sentence each:

- Parameterized queries everywhere, plus a live injection demo.
- Four indexes, each tied to a specific endpoint, with
  `EXPLAIN QUERY PLAN` proof.
- Explicit `SessionLocal.begin()` transactions on every multi-table
  write, SERIALIZABLE engine, `PRAGMA foreign_keys=ON`.
- AI usage disclosed.

"Code, schema, and notes are in the repo. Thanks."

Stop recording.

---

## Cuts if you're long

- Skip the live functional check (8:00).
- Show *either* the `models.py` index declarations *or* the
  `EXPLAIN QUERY PLAN` outputs — not both.
- AI section can be ~30s if needed (just the three bullets).

## Pads if you're short

- Show `STAGE3_NOTES.md`'s "Indexes" table on screen.
- In `sqlite3`: `.schema students`, `.schema enrollments`,
  `.schema courses` — index DDL appears.
- `http://localhost:5050/api/versions` to confirm the stack.
