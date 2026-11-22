// A student's preparation progress, shown to their mentor only when shared (PB-29).
export default function ProgressSummary({ progress }) {
  const statuses = Object.entries(progress.applications_by_status ?? {});
  return (
    <dl className="stats">
      <div><dt>Profile</dt><dd>{progress.profile_complete ? "Complete" : "Incomplete"}</dd></div>
      <div><dt>Resume</dt><dd>{progress.has_resume ? "Added" : "Not yet"}</dd></div>
      <div>
        <dt>Applications</dt>
        <dd>
          {progress.applications_total}
          {statuses.length > 0 && (
            <span className="muted small"> ({statuses.map(([s, n]) => `${n} ${s}`).join(", ")})</span>
          )}
        </dd>
      </div>
      <div>
        <dt>Resume analyses</dt>
        <dd>
          {progress.analyses_total}
          {progress.best_match_score !== null && <span className="muted small"> (best {progress.best_match_score}/100)</span>}
        </dd>
      </div>
      {progress.latest_match && (
        <div>
          <dt>Latest match</dt>
          <dd>{progress.latest_match.job_title} · {progress.latest_match.score}/100</dd>
        </div>
      )}
      <div>
        <dt>Mock interviews</dt>
        <dd>
          {progress.interviews_completed} completed
          {progress.interview_average_score !== null && (
            <span className="muted small"> (avg {progress.interview_average_score}/5)</span>
          )}
        </dd>
      </div>
    </dl>
  );
}
