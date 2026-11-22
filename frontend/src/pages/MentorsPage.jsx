// PB-26 request mentor support, PB-32 book a session, PB-33 view status and mentor feedback.
import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { REQUEST_STATUS_LABELS, REQUEST_TYPES } from "../api.js";
import Alert from "../components/Alert.jsx";
import Field from "../components/Field.jsx";
import { Empty, PageHead, StatusBadge } from "../components/ui.jsx";
import { formatDateTime, formatTimestamp } from "../format.js";

const EMPTY = { request_type: "resume_review", message: "", share_profile: true, share_resume: true, share_progress: false };

function ShareOption({ id, checked, onChange, title, detail }) {
  return (
    <label className="check" htmlFor={id}>
      <input id={id} type="checkbox" checked={checked} onChange={onChange} />
      <span><strong>{title}</strong><span className="muted small"> {detail}</span></span>
    </label>
  );
}

export default function MentorsPage() {
  const { api } = useAuth();
  const [slots, setSlots] = useState([]);
  const [requests, setRequests] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [slot, setSlot] = useState(null); // the slot being booked, or null for a general request
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState({ kind: "error", text: "" });
  const [saving, setSaving] = useState(false);

  function load() {
    api("/api/mentoring/slots").then(setSlots).catch(() => setSlots([]));
    api("/api/mentoring/requests").then(setRequests).catch((err) => setMessage({ kind: "error", text: err.message }));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pickSlot(s) {
    setSlot(s);
    setForm((f) => ({ ...f, request_type: "interview_practice" }));
    document.getElementById("request-form")?.scrollIntoView({ behavior: "smooth" });
  }

  async function submit(e) {
    e.preventDefault();
    setMessage({ kind: "error", text: "" });
    if (form.message.trim().length < 10) return setErrors({ message: "Tell the mentor a bit more (at least 10 characters)." });
    setErrors({});
    setSaving(true);
    try {
      await api("/api/mentoring/requests", { method: "POST", body: { ...form, slot_id: slot?.id ?? null } });
      setMessage({
        kind: "success",
        text: slot
          ? `Booked: ${formatDateTime(slot.start_at)} with ${slot.mentor.full_name}.`
          : "Request sent. A mentor will pick it up soon, and you'll see the status below.",
      });
      setForm(EMPTY);
      setSlot(null);
      load();
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage({ kind: "error", text: err.message });
      load();
    } finally {
      setSaving(false);
    }
  }

  async function cancel(request) {
    if (!window.confirm("Cancel this request?")) return;
    try {
      await api(`/api/mentoring/requests/${request.id}/cancel`, { method: "POST" });
      setMessage({ kind: "success", text: "Request cancelled." });
      load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  const toggle = (key) => (e) => setForm({ ...form, [key]: e.target.checked });

  return (
    <>
      <PageHead title="Mentors" subtitle="Get human advice: request help, or book a time with a mentor." />
      <Alert kind={message.kind}>{message.text}</Alert>

      <div className="two-col">
        <section aria-labelledby="slots-title">
          <h2 id="slots-title" className="section-title">Open session times</h2>
          {slots.length === 0 ? <Empty>No open times right now. You can still send a request.</Empty> : (
            <ul className="slot-list">
              {slots.map((s) => (
                <li key={s.id} className={`card slot${slot?.id === s.id ? " selected" : ""}`}>
                  <div>
                    <strong>{formatDateTime(s.start_at)}</strong>
                    <div className="muted small">{s.duration_minutes} min · {s.mentor.full_name}</div>
                  </div>
                  <button type="button" className="btn btn-small btn-secondary" onClick={() => pickSlot(s)}
                    aria-pressed={slot?.id === s.id}>
                    {slot?.id === s.id ? "Selected" : "Book"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <form id="request-form" className="card" onSubmit={submit} noValidate aria-labelledby="form-title">
          <h2 id="form-title" className="card-title">{slot ? "Book this session" : "Request help"}</h2>
          {slot && (
            <p className="selected-slot">
              {formatDateTime(slot.start_at)} with {slot.mentor.full_name}{" "}
              <button type="button" className="link-button" onClick={() => setSlot(null)}>Remove</button>
            </p>
          )}
          <Field id="request_type" label="What do you need?" as="select" value={form.request_type}
            onChange={(e) => setForm({ ...form, request_type: e.target.value })} error={errors.request_type}>
            {Object.entries(REQUEST_TYPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Field>
          <Field id="message" label="Message to the mentor" as="textarea" rows={4} value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })} error={errors.message} required
            placeholder="e.g. I'm applying for backend internships. Could you check whether my projects section is strong enough?" />
          <fieldset className="share">
            <legend>What can your mentor see?</legend>
            <p className="muted small">Only the mentor who takes this request sees what you tick, and only for this request.</p>
            <ShareOption id="share_profile" checked={form.share_profile} onChange={toggle("share_profile")}
              title="My profile" detail="(education, skills, target role)" />
            <ShareOption id="share_resume" checked={form.share_resume} onChange={toggle("share_resume")}
              title="My current resume" detail="(the text of your current version)" />
            <ShareOption id="share_progress" checked={form.share_progress} onChange={toggle("share_progress")}
              title="My progress summary" detail="(counts of applications, match scores, practice sessions; never your notes)" />
          </fieldset>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Sending…" : slot ? "Book session" : "Send request"}
          </button>
        </form>
      </div>

      <section className="section" aria-labelledby="mine-title">
        <h2 id="mine-title" className="section-title">My requests</h2>
        {requests.length === 0 ? <p className="muted">You haven&apos;t asked for help yet.</p> : (
          <div className="request-list">
            {requests.map((r) => (
              <article key={r.id} className="card request">
                <div className="request-head">
                  <div>
                    <strong>{REQUEST_TYPES[r.request_type]}</strong>{" "}
                    <StatusBadge status={r.status} label={REQUEST_STATUS_LABELS[r.status]} />
                    <div className="muted small">
                      Sent {formatTimestamp(r.created_at)}
                      {r.mentor && <> · Mentor: {r.mentor.full_name}</>}
                      {r.slot && <> · Session: {formatDateTime(r.slot.start_at)}</>}
                    </div>
                  </div>
                  {(r.status === "pending" || r.status === "accepted") && (
                    <button type="button" className="btn btn-small btn-ghost danger" onClick={() => cancel(r)}>Cancel</button>
                  )}
                </div>
                <p className="request-message">{r.message}</p>
                {r.feedback.length > 0 && (
                  <div className="mentor-feedback">
                    <h3 className="sub-title">Feedback from {r.mentor?.full_name ?? "your mentor"}</h3>
                    {r.feedback.map((f) => (
                      <blockquote key={f.id}>
                        <p>{f.body}</p>
                        <footer className="muted small">{formatTimestamp(f.created_at)}</footer>
                      </blockquote>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
