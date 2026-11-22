// PB-36 platform usage analytics: aggregate numbers only, no individual student data.
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import { REQUEST_STATUS_LABELS } from "../../api.js";
import Alert from "../../components/Alert.jsx";
import { PageHead } from "../../components/ui.jsx";
import { formatDate } from "../../format.js";

function Tile({ label, value, note }) {
  return (
    <div className="card tile">
      <p className="tile-label">{label}</p>
      <p className="tile-value">{value ?? "—"}</p>
      {note && <p className="muted small">{note}</p>}
    </div>
  );
}

function Bars({ title, data, labels = {} }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <section className="card">
      <h2 className="card-title">{title}</h2>
      {entries.length === 0 ? <p className="muted">No data yet.</p> : (
        <ul className="bars">
          {entries.map(([key, value]) => (
            <li key={key}>
              <span className="bar-label">{labels[key] ?? key}</span>
              <span className="bar-track"><span className="bar-fill" style={{ width: `${(100 * value) / max}%` }} /></span>
              <span className="bar-value">{value}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Weekly({ weeks, series }) {
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  return (
    <section className="card">
      <h2 className="card-title">Activity per week</h2>
      <div className="legend">
        {series.map((s) => <span key={s.name}><span className={`swatch ${s.className}`} /> {s.name}</span>)}
      </div>
      <div className="week-chart" role="img"
        aria-label={series.map((s) => `${s.name}: ${s.values.join(", ")}`).join("; ") + " (oldest week first)"}>
        {weeks.map((week, i) => (
          <div key={week} className="week">
            <div className="week-bars">
              {series.map((s) => (
                <span key={s.name} className={`week-bar ${s.className}`} style={{ height: `${(100 * s.values[i]) / max}%` }}
                  title={`${s.name}: ${s.values[i]}`} />
              ))}
            </div>
            <span className="week-label">{formatDate(week).replace(/, \d{4}$/, "")}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function AdminAnalyticsPage() {
  const { api } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/admin/analytics").then(setData).catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) return <Alert>{error}</Alert>;
  if (!data) return <p className="page-status">Loading analytics…</p>;

  return (
    <>
      <PageHead title="Platform Analytics" subtitle="How students are using the platform. Totals only; no individual details." />
      <div className="tiles">
        <Tile label="Students" value={data.users.by_role.student} note={`${data.users.by_role.mentor} mentors · ${data.users.by_role.admin} admins`} />
        <Tile label="Average match score" value={data.match.average_score !== null ? `${data.match.average_score}/100` : null}
          note={`${data.match.total} analyses run`} />
        <Tile label="Mock interviews" value={data.interviews.total} note={`${data.interviews.completed} completed`} />
        <Tile label="Mentor requests" value={Object.values(data.mentor_requests_by_status).reduce((a, b) => a + b, 0)}
          note={`${data.mentor_requests_by_status.completed ?? 0} completed`} />
      </div>

      <Weekly weeks={data.weekly.week_starting} series={[
        { name: "Resume analyses", values: data.weekly.match_analyses, className: "s1" },
        { name: "Interview sessions", values: data.weekly.interview_sessions, className: "s2" },
      ]} />

      <div className="two-col">
        <Bars title="Match score distribution" data={data.match.score_bands} />
        <Bars title="Applications by status" data={data.applications_by_status} />
        <Bars title="Mentor requests by status" data={data.mentor_requests_by_status} labels={REQUEST_STATUS_LABELS} />
        <Bars title="Users by role" data={data.users.by_role} />
      </div>
    </>
  );
}
