import './App.css';
import { useCallback, useEffect, useState } from 'react';

const API = '';

function App() {
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    student_id: null,
    full_name: '',
    age: '',
    gpa: '',
    course_ids: [],
  });

  const [reportFilters, setReportFilters] = useState({
    min_age: '',
    max_age: '',
    min_gpa: '',
    max_gpa: '',
    course_id: '',
  });
  const [reportResult, setReportResult] = useState(null);

  const loadCourses = useCallback(() => {
    return fetch(`${API}/api/courses`)
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load courses');
        return r.json();
      })
      .then(setCourses);
  }, []);

  const loadStudents = useCallback(() => {
    return fetch(`${API}/api/students`)
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load students');
        return r.json();
      })
      .then(setStudents);
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([loadCourses(), loadStudents()])
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [loadCourses, loadStudents]);

  const toggleCourse = (courseId) => {
    setForm((f) => {
      const set = new Set(f.course_ids);
      if (set.has(courseId)) set.delete(courseId);
      else set.add(courseId);
      return { ...f, course_ids: [...set] };
    });
  };

  const resetForm = () => {
    setForm({
      student_id: null,
      full_name: '',
      age: '',
      gpa: '',
      course_ids: [],
    });
  };

  const submitStudent = (e) => {
    e.preventDefault();
    setError(null);
    const payload = {
      full_name: form.full_name,
      age: form.age,
      gpa: form.gpa,
      course_ids: form.course_ids,
    };
    const url =
      form.student_id != null
        ? `${API}/api/students/${form.student_id}`
        : `${API}/api/students`;
    const method = form.student_id != null ? 'PUT' : 'POST';
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json().then((j) => ({ ok: r.ok, body: j })))
      .then(({ ok, body }) => {
        if (!ok) throw new Error(body.error || 'Save failed');
        return loadStudents();
      })
      .then(() => {
        resetForm();
        runReport();
      })
      .catch((e) => setError(e.message));
  };

  const editStudent = (s) => {
    setForm({
      student_id: s.student_id,
      full_name: s.full_name,
      age: String(s.age),
      gpa: String(s.gpa),
      course_ids: (s.courses || []).map((c) => c.course_id),
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const deleteStudent = (sid) => {
    if (!window.confirm(`Delete student #${sid}?`)) return;
    setError(null);
    fetch(`${API}/api/students/${sid}`, { method: 'DELETE' })
      .then((r) => r.json().then((j) => ({ ok: r.ok, body: j })))
      .then(({ ok, body }) => {
        if (!ok) throw new Error(body.error || 'Delete failed');
        return loadStudents();
      })
      .then(() => {
        if (form.student_id === sid) resetForm();
        runReport();
      })
      .catch((e) => setError(e.message));
  };

  const runReport = useCallback(() => {
    const q = new URLSearchParams();
    if (reportFilters.min_age !== '') q.set('min_age', reportFilters.min_age);
    if (reportFilters.max_age !== '') q.set('max_age', reportFilters.max_age);
    if (reportFilters.min_gpa !== '') q.set('min_gpa', reportFilters.min_gpa);
    if (reportFilters.max_gpa !== '') q.set('max_gpa', reportFilters.max_gpa);
    if (reportFilters.course_id !== '') q.set('course_id', reportFilters.course_id);
    return fetch(`${API}/api/students/report?${q.toString()}`)
      .then((r) => {
        if (!r.ok) throw new Error('Report failed');
        return r.json();
      })
      .then(setReportResult);
  }, [reportFilters]);

  useEffect(() => {
    if (!loading) runReport().catch(() => {});
    // Only refresh the report when the initial load completes; use "Run report" after that.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  return (
    <div className="app-root">
      <header className="hero">
        <h1>CS348 — Stage 2</h1>
        <p>
          Students CRUD (Requirement 1), filtered report (Requirement 2), courses from the
          database (Requirement 3 — checkboxes are built from <code>/api/courses</code>, not
          hard-coded).
        </p>
      </header>

      {error && <div className="banner error">{error}</div>}

      <section className="panel">
        <h2>Requirement 1 — Insert / update / delete (students table)</h2>
        <form className="form-grid" onSubmit={submitStudent}>
          <label>
            Full name
            <input
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              required
            />
          </label>
          <label>
            Age
            <input
              type="number"
              min="16"
              max="120"
              value={form.age}
              onChange={(e) => setForm((f) => ({ ...f, age: e.target.value }))}
              required
            />
          </label>
          <label>
            GPA
            <input
              type="number"
              step="0.01"
              min="0"
              max="4"
              value={form.gpa}
              onChange={(e) => setForm((f) => ({ ...f, gpa: e.target.value }))}
              required
            />
          </label>
          <fieldset className="courses-fieldset">
            <legend>Courses (loaded from DB)</legend>
            {loading && <p className="muted">Loading courses…</p>}
            {!loading &&
              courses.map((c) => (
                <label key={c.course_id} className="check-row">
                  <input
                    type="checkbox"
                    checked={form.course_ids.includes(c.course_id)}
                    onChange={() => toggleCourse(c.course_id)}
                  />
                  <span>
                    {c.code} — {c.title}
                  </span>
                </label>
              ))}
          </fieldset>
          <div className="actions">
            <button type="submit">{form.student_id != null ? 'Update student' : 'Add student'}</button>
            {form.student_id != null && (
              <button type="button" className="secondary" onClick={resetForm}>
                Cancel edit
              </button>
            )}
          </div>
        </form>

        <h3>All students</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Age</th>
                <th>GPA</th>
                <th>Courses</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td>{s.student_id}</td>
                  <td>{s.full_name}</td>
                  <td>{s.age}</td>
                  <td>{s.gpa}</td>
                  <td className="courses-cell">
                    {(s.courses || []).map((c) => c.code).join(', ') || '—'}
                  </td>
                  <td className="row-actions">
                    <button type="button" onClick={() => editStudent(s)}>
                      Edit
                    </button>
                    <button type="button" className="danger" onClick={() => deleteStudent(s.student_id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Requirement 2 — Filter report (age &amp; GPA ranges; optional course)</h2>
        <p className="hint">
          Run the report, change a student above, then run again — your demo can show the report
          before and after the change.
        </p>
        <div className="report-filters">
          <label>
            Min age
            <input
              type="number"
              value={reportFilters.min_age}
              onChange={(e) =>
                setReportFilters((f) => ({ ...f, min_age: e.target.value }))
              }
            />
          </label>
          <label>
            Max age
            <input
              type="number"
              value={reportFilters.max_age}
              onChange={(e) =>
                setReportFilters((f) => ({ ...f, max_age: e.target.value }))
              }
            />
          </label>
          <label>
            Min GPA
            <input
              type="number"
              step="0.01"
              value={reportFilters.min_gpa}
              onChange={(e) =>
                setReportFilters((f) => ({ ...f, min_gpa: e.target.value }))
              }
            />
          </label>
          <label>
            Max GPA
            <input
              type="number"
              step="0.01"
              value={reportFilters.max_gpa}
              onChange={(e) =>
                setReportFilters((f) => ({ ...f, max_gpa: e.target.value }))
              }
            />
          </label>
          <label>
            Course filter
            <select
              value={reportFilters.course_id}
              onChange={(e) =>
                setReportFilters((f) => ({ ...f, course_id: e.target.value }))
              }
            >
              <option value="">All courses</option>
              {courses.map((c) => (
                <option key={c.course_id} value={c.course_id}>
                  {c.code} — {c.title}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="primary" onClick={() => runReport()}>
            Run report
          </button>
        </div>

        {reportResult && (
          <div className="report-out">
            <p>
              <strong>{reportResult.count}</strong> student(s) match. Filters:{' '}
              <code>{JSON.stringify(reportResult.filters)}</code>
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Age</th>
                    <th>GPA</th>
                    <th>Courses</th>
                  </tr>
                </thead>
                <tbody>
                  {reportResult.students.map((s) => (
                    <tr key={s.student_id}>
                      <td>{s.student_id}</td>
                      <td>{s.full_name}</td>
                      <td>{s.age}</td>
                      <td>{s.gpa}</td>
                      <td>{(s.courses || []).map((c) => c.code).join(', ') || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      <footer className="footer muted">
        Backend: Flask + SQLAlchemy · SQLite file <code>cs348.db</code> · Courses:{' '}
        <code>GET /api/courses</code>
      </footer>
    </div>
  );
}

export default App;
