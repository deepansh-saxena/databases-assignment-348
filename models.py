"""SQLAlchemy models for CS348 project.

Stage 3 additions: explicit indexes on the columns that drive our reports
and dynamic UI lookups. Each index is documented with the query it speeds
up so the choices can be justified in the demo.
"""

from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Stage 3 index: idx_courses_code (UNIQUE)
    # - Supports the dynamic UI dropdown / checkbox list:
    #     SELECT * FROM courses ORDER BY code  (GET /api/courses)
    # - Also enforces "no duplicate course codes" at the DB layer.
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Student(Base):
    __tablename__ = "students"

    # Stage 3 index: idx_students_age_gpa (composite on age, gpa)
    # - Supports the filtered report (Requirement 2):
    #     SELECT * FROM students
    #     WHERE age BETWEEN :min_age AND :max_age
    #       AND gpa BETWEEN :min_gpa AND :max_gpa
    # - The composite is leading-column friendly: queries that filter only
    #   on age (max_gpa/min_gpa left blank) still benefit from the prefix.
    __table_args__ = (
        Index("idx_students_age_gpa", "age", "gpa"),
    )

    student_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gpa: Mapped[float] = mapped_column(Float, nullable=False)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    # Stage 3 indexes:
    # - uq_enrollment_student_course: a UniqueConstraint on
    #   (student_id, course_id). It prevents duplicate enrollments AND,
    #   because student_id is the leading column, also serves any query
    #   that looks up enrollments by student_id (e.g. listing one
    #   student's courses, or the cascade DELETE when a student is
    #   removed). That makes a separate idx_enrollments_student_id
    #   index redundant, so we deliberately do NOT create one.
    # - idx_enrollments_course_id: supports queries that start from
    #   the course side. Specifically:
    #     * the report's optional course filter (EXISTS / JOIN on
    #       enrollments.course_id, GET /api/students/report?course_id=...)
    #     * the cascade DELETE that fires when a course is removed
    #       (DELETE FROM enrollments WHERE course_id = ?), which would
    #       otherwise table-scan because the unique index leads with
    #       student_id, not course_id.
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
        Index("idx_enrollments_course_id", "course_id"),
    )

    enrollment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
