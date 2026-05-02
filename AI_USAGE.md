# AI Usage

This section satisfies the **Disclosure Requirement** in the CS348 project
spec ("AI Acceptable Use Policy for the Semester Project"). It describes
which AI tools were used, what tasks they assisted with, and how the output
was verified. The same content is summarised verbally in the Stage 3 demo.

## Which AI tools were used

- **Cursor** (IDE with an integrated Anthropic Claude assistant) — used
  during the Stage 2 and Stage 3 work.
- **ChatGPT** (occasional rubber-duck questions about SQLAlchemy 2.0 syntax
  and SQLite isolation semantics).

No code-generation service had access to credentials, and nothing was
deployed using AI-generated infrastructure.

## What the AI assisted with

| Task                                                                                         | Where the AI helped                                                                                                                                                              |
|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Scaffolding the Flask + SQLAlchemy + React layout in Stage 1.                                | Generated the initial `app.py` route skeleton and a starter React component. I rewrote the React form/state to match the way I want the demo to flow.                            |
| Writing the SQLAlchemy 2.0-style models and the `Mapped[...]` annotations.                   | Suggested the syntax. I confirmed the API in the SQLAlchemy 2.0 docs (`DeclarativeBase`, `mapped_column`, the `Mapped[list[...]]` typing form) before keeping it.                  |
| Choosing indexes for Stage 3 and writing `EXPLAIN QUERY PLAN` checks.                        | Brainstormed candidate indexes. I rejected the redundant `idx_enrollments_student_id` after running `EXPLAIN QUERY PLAN` myself and seeing the unique index already covered it. |
| Wording the SQL injection / transactions / isolation level discussion.                       | Drafted explanations. I cross-checked them against the SQLite docs on locking and journal modes, and the SQLAlchemy docs on `Session.begin()` semantics.                          |
| Producing the Stage 2 and Stage 3 demo scripts and the database design markdown.             | Drafted the structure and prose. I edited timing, added project-specific terminal commands, and corrected statements that didn't match my code.                                  |
| Catching bugs (e.g., the early version of the report did the course filter in Python).       | Suggested moving the course filter into SQL via `EXISTS`. I implemented it, then ran `EXPLAIN QUERY PLAN` to confirm the planner uses an index for it.                            |

## How AI output was verified or modified

- **Ran the code.** Every AI-assisted change was followed by an actual run:
  `python3 app.py` plus `curl` against each endpoint, plus `EXPLAIN QUERY
  PLAN` for the index claims.
- **Checked official docs.** SQLAlchemy 2.0 typing, SQLite `PRAGMA
  foreign_keys`, and SQLite locking / isolation behaviour were all
  cross-checked against the official documentation rather than trusted
  blindly from the model.
- **Adversarial test.** Sent a `'); DROP TABLE students;--` payload as a
  student name to confirm the parameterized-queries claim end-to-end.
- **Removed unused code.** Where the AI produced extra endpoints or
  abstractions that weren't needed for the rubric, they were deleted so
  every line in the repo serves a stated purpose.

## Things I did *without* AI

- Picking the project topic and the requirements (Stage 1).
- Designing the schema (three tables, the unique constraint on
  `(student_id, course_id)`, cascade deletes).
- Deciding which indexes belonged in the final submission and being able
  to justify them with query plans.
- Writing this disclosure.

I can explain and justify every line of code, every index, the SQL
injection protection, and the transaction/isolation choices in the demo.
