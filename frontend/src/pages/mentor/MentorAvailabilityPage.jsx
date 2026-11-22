// PB-31 mentors set the times students can book.
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import Alert from "../../components/Alert.jsx";
import Field from "../../components/Field.jsx";
import { Badge, Empty, PageHead } from "../../components/ui.jsx";
import { formatDateTime, localDateTimeInput } from "../../format.js";

export default function MentorAvailabilityPage() {
  const { api } = useAuth();
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ start_at: localDateTimeInput(24 * 60), duration_minutes: "30" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState({ kind: "error", text: "" });

  function load() {
    api("/api/mentor/slots").then(setSlots).catch((err) => setMessage({ kind: "error", text: err.message }));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function add(e) {
    e.preventDefault();
    setMessage({ kind: "error", text: "" });
    if (!form.start_at) return setErrors({ start_at: "Pick a date and time." });
    if (new Date(form.start_at) <= new Date()) return setErrors({ start_at: "Pick a time in the future." });
    setErrors({});
    try {
      await api("/api/mentor/slots", {
        method: "POST",
        body: { start_at: form.start_at, duration_minutes: Number(form.duration_minutes) },
      });
      setMessage({ kind: "success", text: `Added ${formatDateTime(form.start_at)}. Students can book it now.` });
      load();
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage({ kind: "error", text: err.message });
    }
  }

  async function remove(slot) {
    try {
      await api(`/api/mentor/slots/${slot.id}`, { method: "DELETE" });
      setMessage({ kind: "success", text: "Time removed." });
      load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  const now = new Date();
  const upcoming = slots.filter((s) => new Date(s.start_at) > now);
  const past = slots.filter((s) => new Date(s.start_at) <= now);

  return (
    <>
      <PageHead title="My Availability" subtitle="Add times when students can book a session with you." />
      <Alert kind={message.kind}>{message.text}</Alert>

      <form className="card form-grid" onSubmit={add} noValidate>
        <Field id="start_at" label="Start time" type="datetime-local" value={form.start_at} min={localDateTimeInput(5)}
          onChange={(e) => setForm({ ...form, start_at: e.target.value })} error={errors.start_at} required />
        <Field id="duration_minutes" label="Length" as="select" value={form.duration_minutes}
          onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} error={errors.duration_minutes}>
          {[15, 30, 45, 60, 90].map((m) => <option key={m} value={m}>{m} minutes</option>)}
        </Field>
        <div className="form-actions span-2">
          <button type="submit" className="btn btn-primary">Add time</button>
        </div>
      </form>

      <section className="section" aria-labelledby="upcoming-title">
        <h2 id="upcoming-title" className="section-title">Upcoming times ({upcoming.length})</h2>
        {upcoming.length === 0 ? <Empty>No upcoming times. Add one above.</Empty> : (
          <ul className="slot-list">
            {upcoming.map((s) => (
              <li key={s.id} className="card slot">
                <div>
                  <strong>{formatDateTime(s.start_at)}</strong>
                  <div className="muted small">{s.duration_minutes} minutes</div>
                </div>
                {s.is_booked ? <Badge tone="info">Booked</Badge> : (
                  <button type="button" className="btn btn-small btn-ghost danger" onClick={() => remove(s)}>Remove</button>
                )}
              </li>
            ))}
          </ul>
        )}
        {past.length > 0 && <p className="muted small">{past.length} past time{past.length > 1 ? "s" : ""} not shown.</p>}
      </section>
    </>
  );
}
