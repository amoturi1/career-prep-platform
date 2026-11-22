// PB-29 mentors see progress for the students they support (only when the student shared it).
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import { REQUEST_STATUS_LABELS, REQUEST_TYPES } from "../../api.js";
import Alert from "../../components/Alert.jsx";
import ProgressSummary from "../../components/ProgressSummary.jsx";
import { Empty, PageHead, StatusBadge } from "../../components/ui.jsx";

export default function MentorStudentsPage() {
  const { api } = useAuth();
  const [students, setStudents] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/mentor/students").then(setStudents).catch((err) => { setError(err.message); setStudents([]); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (students === null) return <p className="page-status">Loading…</p>;

  return (
    <>
      <PageHead title="My Students" subtitle="Students you're supporting through accepted requests." />
      <Alert>{error}</Alert>
      {students.length === 0 ? (
        <Empty>Once you accept a request, the student appears here.</Empty>
      ) : (
        <div className="student-grid">
          {students.map((s) => (
            <article key={s.student.id} className="card">
              <h2 className="card-title">{s.student.full_name}</h2>
              <ul className="plain-list">
                {s.requests.map((r) => (
                  <li key={r.id}>
                    {REQUEST_TYPES[r.request_type]}{" "}
                    <StatusBadge status={r.status} label={REQUEST_STATUS_LABELS[r.status]} />
                  </li>
                ))}
              </ul>
              {s.progress ? <ProgressSummary progress={s.progress} /> : (
                <p className="lock-note">🔒 This student hasn&apos;t shared their progress summary.</p>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}
