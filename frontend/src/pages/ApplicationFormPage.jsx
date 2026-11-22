// PB-07 add application, PB-10 edit application details.
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { APPLICATION_STATUSES } from "../api.js";
import Field from "../components/Field.jsx";
import Alert from "../components/Alert.jsx";

const EMPTY = { company: "", job_title: "", date_applied: "", url: "", status: "Applied", notes: "" };
// Today's date in the user's own time zone, as YYYY-MM-DD.
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

function validate(form) {
  const errors = {};
  if (!form.company.trim()) errors.company = "This field is required.";
  if (!form.job_title.trim()) errors.job_title = "This field is required.";
  if (form.url && !/^https?:\/\//.test(form.url.trim())) errors.url = "Link must start with http:// or https://";
  if (form.date_applied && form.date_applied > today()) errors.date_applied = "Date applied cannot be in the future";
  return errors;
}

export default function ApplicationFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const { api } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(isEdit);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isEdit) return;
    api(`/api/applications/${id}`)
      .then((data) =>
        setForm({
          company: data.company,
          job_title: data.job_title,
          date_applied: data.date_applied ?? "",
          url: data.url,
          status: data.status,
          notes: data.notes,
        })
      )
      .catch((err) => setMessage(err.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setSaving(true);
    try {
      const body = { ...form, date_applied: form.date_applied || null };
      await api(isEdit ? `/api/applications/${id}` : "/api/applications", {
        method: isEdit ? "PUT" : "POST",
        body,
      });
      navigate("/applications", {
        state: { notice: isEdit ? "Application updated." : `Added ${form.company.trim()} to your tracker.` },
      });
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="page-status">Loading application…</p>;

  return (
    <>
      <div className="page-head">
        <div>
          <Link to="/applications" className="back-link">← Back to applications</Link>
          <h1>{isEdit ? "Edit application" : "Add application"}</h1>
        </div>
      </div>

      <Alert>{message}</Alert>

      <form className="card form-grid" onSubmit={handleSubmit} noValidate>
        <Field id="company" label="Company name" value={form.company} onChange={update} error={errors.company} required />
        <Field id="job_title" label="Job title" value={form.job_title} onChange={update} error={errors.job_title} required />
        <Field id="date_applied" label="Date applied" type="date" max={today()} value={form.date_applied}
          onChange={update} error={errors.date_applied} />
        <Field id="status" label="Status" as="select" value={form.status} onChange={update} error={errors.status}>
          {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </Field>
        <Field id="url" label="Application link" type="url" value={form.url} onChange={update} error={errors.url}
          placeholder="https://" full />
        <Field id="notes" label="Notes" as="textarea" rows={4} value={form.notes} onChange={update}
          error={errors.notes} placeholder="Contacts, next steps, interview dates…" full />
        <div className="form-actions span-2">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save application"}
          </button>
          <Link to="/applications" className="btn btn-ghost">Cancel</Link>
        </div>
      </form>
    </>
  );
}
