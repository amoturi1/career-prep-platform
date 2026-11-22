// One job, internship, event or announcement (PB-14, PB-15, NFR-14).
import { Link } from "react-router-dom";
import { KIND_LABELS } from "../api.js";
import { formatDate, formatDateTime, todayISO } from "../format.js";
import { StatusBadge } from "./ui.jsx";

function dateLine(item) {
  if (item.kind === "event") {
    const past = item.event_at && new Date(item.event_at) < new Date();
    return { text: `${formatDateTime(item.event_at)}${past ? " (past event)" : ""}`, past };
  }
  if (item.kind === "announcement") return { text: `Posted ${formatDate(item.created_at)}`, past: false };
  if (!item.deadline) return { text: "No deadline listed", past: false };
  const past = item.deadline < todayISO();
  return { text: past ? `Deadline passed (${formatDate(item.deadline)})` : `Apply by ${formatDate(item.deadline)}`, past };
}

export default function OpportunityCard({ item, expanded, onToggle, showStatus = false, studentActions = false, children }) {
  const detailsId = `opp-${item.id}-details`;
  const when = dateLine(item);
  const isRole = item.kind === "job" || item.kind === "internship";

  return (
    <article className={`card opp-card${when.past ? " opp-past" : ""}`}>
      <div className="opp-head">
        <div>
          <h2 className="opp-title">{item.title}</h2>
          <p className="opp-org">
            {item.organization}
            {item.location && <> · {item.location}</>}
          </p>
        </div>
        <div className="opp-tags">
          <span className={`tag tag-${item.kind}`}>{KIND_LABELS[item.kind] ?? item.kind}</span>
          {showStatus && <StatusBadge status={item.status} />}
        </div>
      </div>
      <p className={`small ${when.past ? "warn-text" : "muted"}`}>{when.text}</p>

      {expanded && (
        <div id={detailsId} className="opp-details">
          <p>{item.description}</p>
          <div className="row-actions start">
            {item.apply_url && (
              <a href={item.apply_url} target="_blank" rel="noreferrer" className="btn btn-primary btn-small">
                {item.kind === "event" ? "Event details ↗" : isRole ? "Apply on company site ↗" : "Learn more ↗"}
              </a>
            )}
            {studentActions && isRole && (
              <>
                <Link to={`/match?listing=${item.id}`} className="btn btn-secondary btn-small">
                  Compare my resume
                </Link>
                <Link to={`/interview?listing=${item.id}`} className="btn btn-secondary btn-small">
                  Practice interview
                </Link>
              </>
            )}
          </div>
        </div>
      )}

      <div className="opp-foot">
        {onToggle && (
          <button type="button" className="link-button" aria-expanded={expanded} aria-controls={detailsId} onClick={onToggle}>
            {expanded ? "Hide details" : "View details"}
          </button>
        )}
        {children}
      </div>
    </article>
  );
}
