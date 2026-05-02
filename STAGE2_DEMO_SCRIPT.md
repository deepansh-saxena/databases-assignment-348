# CS348 Stage 2 — Demo video script

**Length (course spec):** Stage 2 asks for a **5- to 15-minute** demo—not 5–10 specifically. Staying around **8–10 minutes** is a comfortable target; use **5–15** as the hard limits unless your TA gives a different range.

Use this as a talk track. If you need to finish closer to **5 minutes**, use the trims in *If you need to cut time* and shorten the “How to run” segment to ~45 seconds (commands on screen, minimal narration).

**Grader note:** Many submissions lose points for not **showing how to run the code on screen**. Do the **How to run the project** section at the top every time you record—do not skip it.

---

## Before you record (prep only — can be off-camera)

1. Optional: delete `cs348.db` once if you want a clean seed; otherwise keep existing data.
2. Know your paths: project root contains `app.py`, `requirements.txt`, and folder `frontend/`.

---

## 0:00–1:30 — How to run the project (**show in the video**)

Record this segment **at the start** (or repeat a shorter version at the **end** if the grader prefers “summary last”). Use **two terminals** and your browser so someone can repeat your steps later.

**Say:**

> First, here is how to run this project the next time—or on another machine. You need **Python 3** with packages from `requirements.txt`, and **Node.js** with **npm** for the React app.

**Do (show typing or paste commands visibly):**

1. **Project location:** In the IDE or file explorer, show the folder that contains `app.py` and `requirements.txt`.

2. **Install backend dependencies** (first time or after cloning):
   ```bash
   cd /path/to/your/CS348-project
   pip3 install -r requirements.txt
   ```
   If you use a virtual environment, activate it **before** `pip install` (macOS/Linux: `source venv/bin/activate`; Windows: `venv\Scripts\activate`).

3. **Terminal 1 — backend:**
   ```bash
   python3 app.py
   ```
   Point at the line that says the server is running (e.g. `http://127.0.0.1:5050`).

4. **Terminal 2 — frontend:**
   ```bash
   cd frontend
   npm install
   npm start
   ```
   Say that `npm install` is only needed the first time or after pulling changes.

5. **Browser:** Open **`http://localhost:3000`**. Say that the React dev server proxies API calls to the Flask app on **port 5050** (we use 5050 instead of the default 5000 because macOS AirPlay Receiver squats on 5000).

**Say:**

> If the backend is not running, the page may show an error when loading data. Always start **Flask first**, then **npm start** in `frontend`.

---

## 1:30–2:15 — Introduction

**Say:**

> Hi, this is my CS348 project Stage 2 demo. I’m using a Flask backend with SQLAlchemy and SQLite, and a React frontend.  
> Stage 2 has three parts: the relational database design, a live demo of my first two requirements—CRUD and a filtered report—and showing that course choices in the UI come from the database, not hard-coded lists.

**Do:** Briefly show the project folder in the IDE (optional): `models.py`, `database.py`, `app.py`, `frontend/src/App.js`, and `DATABASE_DESIGN.md`.

---

## 2:15–3:30 — Database design (Deliverable 1)

**Say:**

> For the database design, I have three tables.  
> **Courses** has a primary key `course_id`, plus `code` and `title`.  
> **Students** has primary key `student_id`, plus `full_name`, `age`, and `gpa`.  
> **Enrollments** connects students to courses: it has its own primary key `enrollment_id`, and foreign keys to `students` and `courses`, with a unique constraint so a student can’t enroll in the same course twice.

**Do:** Open `DATABASE_DESIGN.md` or `models.py` and scroll slowly so names are visible.

**Say:**

> Deletes cascade from students to their enrollments so the data stays consistent.

---

## 3:30–7:00 — Requirement 1: Insert, update, delete (students)

**Say:**

> Requirement one is full CRUD on the **students** table. I’ll insert a new student, update one, and delete one, and you’ll see the table refresh from the API each time.

**Do:**

1. **Insert:** Fill in full name, age, GPA. Check one or more **course** checkboxes (mention briefly: these labels come from the database—I’ll explain in part three). Click **Add student**. Point to the new row in **All students**.

2. **Update:** Click **Edit** on any student. Change age or GPA (or name). Click **Update student**. Point to the updated row.

3. **Delete:** Click **Delete** on a student you’re okay removing (or the one you just added). Confirm. Point out the row is gone.

**Say:**

> On the backend, create and update go through `POST /api/students` and `PUT /api/students/<id>`, and delete uses `DELETE /api/students/<id>`. The ORM maps those operations to the `students` table and updates `enrollments` when I send `course_ids`.

---

## 7:00–10:00 — Requirement 2: Filter report (before and after a change)

**Say:**

> Requirement two is a **report** with filters. I can restrict by a range of ages, a range of GPAs, and optionally by course. I’ll run the report, then change data, then run the report again so you can see the results **before and after**.

**Do:**

1. Set filters, for example: **Min age** 18, **Max age** 25, **Min GPA** 3.0, **Max GPA** 4.0. Leave course as **All courses** or pick one course from the dropdown. Click **Run report**. Read the **count** and scan the table.

2. **Before/after:** Say “This is the **before** state.” Then either edit a student so they fall **outside** the range (e.g., lower GPA below min) or delete someone who appeared in the report. Click **Run report** again. Say “This is the **after** state—the count or rows changed because the data changed.”

**Say:**

> The report is served by `GET /api/students/report` with query parameters like `min_age`, `max_age`, `min_gpa`, `max_gpa`, and optional `course_id`, which uses the enrollments table when filtering by course.

---

## 10:00–12:30 — Requirement 3: Dynamic UI from the database (show code / query)

**Say:**

> For part three, the assignment asks for interface elements like a drop-down or checkboxes for courses to be built **dynamically** from the database. I don’t hard-code course names in React.

**Do:**

1. Open `frontend/src/App.js`. Scroll to **`loadCourses`** (the `fetch('/api/courses')` call) and the **`courses.map`** that renders the **checkboxes** and the **`<select>`** options in the report section.

2. Open `app.py` and show the **`/api/courses`** route that queries the `courses` table.

**Say:**

> When the page loads, React calls `/api/courses`, gets JSON, and renders the checkboxes and the course filter dropdown from that response. If I added a row to `courses` in the database, the UI would show it without changing the React code.

---

## 12:30–13:30 — Wrap-up

**Say:**

> To summarize: I showed **how to run the backend and frontend**, the relational schema with primary and foreign keys, insert/update/delete on students, a filtered report before and after a data change, and how course UI elements are populated from the database through `/api/courses`. Thanks for watching.

**Optional (15 seconds):** Flash `requirements.txt` and `frontend/package.json` again and repeat: “Install with `pip install -r requirements.txt` and `npm install` inside `frontend`, then `python3 app.py` and `npm start`.”

**Do:** Stop recording.

---

## If you need to cut time

- Shorten the database section to ~30 seconds (only show `DATABASE_DESIGN.md`).
- Do only **one** of edit or delete for CRUD if you’re over time (but the rubric asks for insert, update, and delete—keep all three if possible).
- Show **either** the `loadCourses` **or** the backend `list_courses` route for part three, not both in depth.

## If you need to pad slightly (still under 15 minutes)

- Show `http://localhost:5050/api/courses` in the browser as raw JSON.
- Show SQLite file `cs348.db` in the project folder and mention it’s created on first run.
