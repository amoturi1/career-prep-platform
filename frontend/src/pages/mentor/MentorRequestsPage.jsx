// PB-27 manage requests, PB-28 review shared materials and give feedback.
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import { REQUEST_STATUS_LABELS, REQUEST_TYPES } from "../../api.js";
import Alert from "../../components/Alert.jsx";
import Field from "../../components/Field.jsx";
import ProgressSummary from "../../components/ProgressSummary.jsx";
import { Empty, PageHead, StatusBadge, Tabs } from "../../components/ui.jsx";
import { formatDateTime, formatTimestamp } from "../../format.js";

const SCOPES = [
  { value: "all", label: "All" },
  { value: "open", label: "Open requests" },
  { value: "mine", label: "Assigned to me" },
];

function Materials({ request, materials }) {
  if (!materials.access) {
    return (
      <p className="lock-note">
        🔒 The student&apos;s materials become visible after you accept this request, and only the items they chose to
        share.
      </p>
    );
  }
  const nothing = !request.share_profile && !request.share_resume && !request.share_progress;
  return (
    <div className="materials">
      {nothing && <p className="muted">The student didn&apos;t share any materials with this request.</p>}
      {request.share_profile && (
        <details open>
          <summary>Profile</summary>
          {materials.profile ? (
            <dl className="mini-dl">
              <dt>Target role</dt><dd>{materials.profile.target_role}</dd>
              <dt>Education</dt><dd>{materials.profile.education}</dd>
              <dt>Skills</dt><dd>{materials.profile.skills}</dd>
              {materials.profile.experience && <><dt>Experience</dt><dd>{materials.profile.experience}</dd></>}
            </dl>
          ) : <p className="muted">No profile yet.</p>}
        </details>
      )}
      {request.share_resume && (
        <details>
          <summary>Current resume</summary>
          {materials.resume ? (
            <>
              <p className="muted small">{materials.resume.filename} · added {formatTimestamp(materials.resume.uploaded_at)}</p>
              <pre className="resume-text">{materials.resume.text}</pre>
            </>
          ) : <p className="muted">No resume added yet.</p>}
        </details>
      )}
      {request.share_progress && materials.progress && (
        <details>
          <summary>Progress summary</summary>
          <ProgressSummary progress={materials.progress} />
        </details>
      )}
    </div>
  );
}

export default function MentorRequestsPage() {
  const { api } = useAuth();
  const [scope, setScope] = useState("all");
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null); // { request, materials }
  const [feedback, setFeedback] = useState("");
  const [feedbackError, setFeedbackError] = useState("");
  const [message, setMessage] = useState({ kind: "error", text: "" });

  function loadList() {
    api(`/api/mentor/requests?scope=${scope}`).then(setItems).catch((err) => setMessage({ kind: "error", text: err.message }));
  }

  useEffect(() => {
    loadList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope]);

  async function open(id) {
    setMessage({ kind: "error", text: "" });
    try {
      setSelected(await api(`/api/mentor/requests/${id}`));
      setFeedback("");
      setFeedbackError("");
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  async function act(path, options, success) {
    setMessage({ kind: "error", text: "" });
    try {
      await api(path, options);
      setMessage({ kind: "success", text: success });
      await open(selected.request.id);
      loadList();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  async function sendFeedback(e) {
    e.preventDefault();
    if (feedback.trim().length < 5) return setFeedbackError("Write a little more feedback (at least 5 characters).");
    setFeedbackError("");
    await act(`/api/mentor/requests/${selected.request.id}/feedback`, { method: "POST", body: { body: feedback } },
      "Feedback sent to the student.");
    setFeedback("");
  }

  const r = selected?.request;
  // A mentor only ever sees open requests or their own, so an assigned request is this mentor's.
  const mine = Boolean(r?.mentor);

  return (
    <>
      <PageHead title="Mentor Requests" subtitle="Pick up requests, review what students shared, and send feedback." />
      <Alert kind={message.kind}>{message.text}</Alert>
      <Tabs tabs={SCOPES} value={scope} onChange={(s) => { setScope(s); setSelected(null); }} label="Which requests" />

      <div className="split">
        <div className="request-list">
          {items.length === 0 ? <Empty>No requests here right now.</Empty> : items.map((item) => (
            <button key={item.id} type="button" onClick={() => open(item.id)}
              className={`card request-pick${r?.id === item.id ? " selected" : ""}`}>
              <span className="request-head">
                <strong>{REQUEST_TYPES[item.request_type]}</strong>
                <StatusBadge status={item.status} label={REQUEST_STATUS_LABELS[item.status]} />
              </span>
              <span className="muted small">
                {item.student.full_name} · {formatTimestamp(item.created_at)}
                {item.slot && <> · 📅 {formatDateTime(item.slot.start_at)}</>}
              </span>
              <span className="clamp-2">{item.message}</span>
            </button>
          ))}
        </div>

        <div>
          {!r ? <Empty>Select a request to see the details.</Empty> : (
            <section className="card" aria-labelledby="detail-title">
              <div className="request-head">
                <div>
                  <h2 id="detail-title" className="card-title">{REQUEST_TYPES[r.request_type]} · {r.student.full_name}</h2>
                  <p className="muted small">
                    Sent {formatTimestamp(r.created_at)}
                    {r.slot && <> · Session {formatDateTime(r.slot.start_at)} ({r.slot.duration_minutes} min)</>}
                  </p>
                </div>
                <StatusBadge status={r.status} label={REQUEST_STATUS_LABELS[r.status]} />
              </div>
              <p className="request-message">{r.message}</p>

              <div className="row-actions start">
                {r.status === "pending" && !r.mentor && (
                  <button type="button" className="btn btn-primary btn-small"
                    onClick={() => act(`/api/mentor/requests/${r.id}/accept`, { method: "POST" }, "You've accepted this request.")}>
                    Accept request
                  </button>
                )}
                {mine && (r.status === "pending" || r.status === "accepted") && (
                  <button type="button" className="btn btn-ghost btn-small danger"
                    onClick={() => window.confirm("Decline this request? The student will see it as declined.") &&
                      act(`/api/mentor/requests/${r.id}/decline`, { method: "POST" }, "Request declined.")}>
                    Decline
                  </button>
                )}
                {r.status === "accepted" && (
                  <button type="button" className="btn btn-secondary btn-small"
                    onClick={() => act(`/api/mentor/requests/${r.id}/status`, { method: "PATCH", body: { status: "in_progress" } }, "Marked in progress.")}>
                    Mark in progress
                  </button>
                )}
                {(r.status === "accepted" || r.status === "in_progress") && (
                  <button type="button" className="btn btn-secondary btn-small"
                    onClick={() => act(`/api/mentor/requests/${r.id}/status`, { method: "PATCH", body: { status: "completed" } }, "Marked completed.")}>
                    Mark completed
                  </button>
                )}
              </div>

              <h3 className="sub-title">Shared by the student</h3>
              <Materials request={r} materials={selected.materials} />

              {["accepted", "in_progress", "completed"].includes(r.status) && (
                <>
                  <h3 className="sub-title">Feedback</h3>
                  {r.feedback.map((f) => (
                    <blockquote key={f.id}>
                      <p>{f.body}</p>
                      <footer className="muted small">{formatTimestamp(f.created_at)}</footer>
                    </blockquote>
                  ))}
                  <form onSubmit={sendFeedback} noValidate>
                    <Field id="feedback" label="Add feedback for the student" as="textarea" rows={5} value={feedback}
                      onChange={(e) => setFeedback(e.target.value)} error={feedbackError}
                      placeholder="Be specific: what's strong, what to change, and one next step." />
                    <button type="submit" className="btn btn-primary">Send feedback</button>
                  </form>
                </>
              )}
            </section>
          )}
        </div>
      </div>
    </>
  );
}
