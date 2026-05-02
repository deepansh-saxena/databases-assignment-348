# CS348 Semester Project — Stages 2 & 3

A small student-and-courses tracker. Flask + SQLAlchemy + SQLite on the
backend, React on the frontend. Built to satisfy the CS348 project
rubric for **Stage 2** (database design, CRUD, filtered report, dynamic
UI from the DB) and **Stage 3** (SQL injection protection, indexes,
transactions and isolation level, AI usage disclosure).

## Quick start

You need **Python 3.10+** and **Node.js 18+** with **npm**.

```bash
# Terminal 1 — backend
pip3 install -r requirements.txt
python3 app.py
# → Running on http://127.0.0.1:5050
```

```bash
# Terminal 2 — frontend
cd frontend
npm install            # first time only
npm start
# → http://localhost:3000
```

Always start Flask first; the React dev server proxies `/api/*` to it.

> **Why port 5050?** macOS's AirPlay Receiver binds `*:5000`, which
> intercepts the React proxy before it can reach Flask. On Linux/Windows
> you can change `app.run(port=...)` in `app.py` and the `proxy` field in
> `frontend/package.json` back to 5000.

The SQLite database file `cs348.db` is created and seeded automatically
on the first request — no migrations to run. It's git-ignored, so each
clone gets its own.

## Repository layout

| Path | What it is |
| --- | --- |
| `app.py` | Flask routes — every endpoint and the lazy DB init |
| `models.py` | SQLAlchemy models for `students`, `courses`, `enrollments`, plus index declarations |
| `database.py` | Engine + session factory, `PRAGMA foreign_keys=ON`, `SERIALIZABLE` isolation |
| `requirements.txt` | Python dependencies |
| `frontend/` | Create React App project; `src/App.js` holds the UI |
| `DATABASE_DESIGN.md` | Stage 2 deliverable — schema, keys, constraints |
| `STAGE3_NOTES.md` | Stage 3 deliverable — index/transaction/isolation rationale |
| `AI_USAGE.md` | Stage 3 disclosure — tools used, tasks assisted, verification |
| `STAGE2_DEMO_SCRIPT.md` / `STAGE3_DEMO_SCRIPT.md` | Notes used while recording each demo |

## Where each rubric item lives

**Stage 2**

- *Database design* — `DATABASE_DESIGN.md` and `models.py`
- *Requirement 1 (CRUD on students)* — `POST/PUT/DELETE /api/students` in `app.py`; UI in `frontend/src/App.js`
- *Requirement 2 (filtered report)* — `GET /api/students/report` in `app.py`
- *Requirement 3 (UI built from the DB)* — `GET /api/courses` populates the checkboxes / dropdown in `frontend/src/App.js`

**Stage 3**

- *SQL injection protection* — every DB access in `app.py` goes through SQLAlchemy expressions (parameterized), with `int()` / `float()` coercion at the request boundary
- *Indexes* — declared on the model classes in `models.py`; rationale and supported queries in `STAGE3_NOTES.md`
- *Transactions / isolation* — `SessionLocal.begin()` blocks in `app.py` for every multi-table write; `SERIALIZABLE` isolation and `PRAGMA foreign_keys=ON` set in `database.py`
- *AI usage* — `AI_USAGE.md`

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/courses` | Course list (powers the dynamic UI) |
| `GET` | `/api/students` | All students with their enrollments |
| `POST` | `/api/students` | Create student + enrollments (atomic) |
| `PUT` | `/api/students/<id>` | Update student + replace enrollments (atomic) |
| `DELETE` | `/api/students/<id>` | Delete student; cascades to enrollments |
| `GET` | `/api/students/report` | Filtered report — `min_age`, `max_age`, `min_gpa`, `max_gpa`, optional `course_id` |
| `GET` | `/api/versions` | Stack version sanity check |

## Tech stack

- **Backend:** Python 3.12, Flask 3.1.2, SQLAlchemy 2.0.46, Flask-CORS 6.0.2, SQLite
- **Frontend:** React 18 via Create React App
