// PB-16 publish jobs, PB-17 publish events and announcements, PB-34 update or archive content.
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import { KIND_LABELS } from "../../api.js";
import Alert from "../../components/Alert.jsx";
import Field from "../../components/Field.jsx";
import OpportunityCard from "../../components/OpportunityCard.jsx";
import { Empty, PageHead, Tabs } from "../../components/ui.jsx";
import { localDateTimeInput } from "../../format.js";

const EMPTY = {
  kind: "internship",
  title: "",
  organization: "",
  location: "",
  description: "",
  apply_url: "",
  deadline: "",
  event_at: "",
  status: "published",
};

const FILTERS = [
  { value: "", label: "All" },
  { value: "internship", label: "Internships" },
  { value: "job", label: "Jobs" },
  { value: "event", label: "Events" },
  { value: "announcement", label: "Announcements" },
  { value: "archived", label: "Archived" },
];

function validate(form) {
  const errors = {};
  for (const key of ["title", "organization", "description"])
    if (!form[key].trim()) errors[key] = "This field is required.";
  if (form.apply_url && !/^https?:\/\//.test(form.apply_url.trim()))
    errors.apply_url = "Link must start with http:// or https://";
  if (form.kind === "event" && !form.event_at) errors.event_at = "Events need a date and time";
  return errors;
}

export default function AdminContentPage() {
  const { api } = useAuth();
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState({ kind: "error", text: "" });
  const [saving, setSaving] = useState(false);
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");
  const [openId, setOpenId] = useState(null);

  function load() {
    api("/api/opportunities/manage").then(setItems).catch((err) => setMessage({ kind: "error", text: err.message }));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const isRole = form.kind === "job" || form.kind === "internship";

  function startEdit(item) {
    setEditingId(item.id);
    setForm({
      kind: item.kind,
      title: item.title,
      organization: item.organization,
      location: item.location ?? "",
      description: item.description,
      apply_url: item.apply_url ?? "",
      deadline: item.deadline ?? "",
      event_at: item.event_at ? item.event_at.slice(0, 16) : "",
      status: item.status === "archived" ? "published" : item.status,
    });
    setErrors({});
    setMessage({ kind: "error", text: "" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY);
    setErrors({});
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage({ kind: "error", text: "" });
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    const body = {
      ...form,
      deadline: isRole && form.deadline ? form.deadline : null,
      event_at: form.kind === "event" ? form.event_at : null,
      location: form.kind === "announcement" ? "" : form.location,
    };
    setSaving(true);
    try {
      const saved = await api(editingId ? `/api/opportunities/${editingId}` : "/api/opportunities", {
        method: editingId ? "PUT" : "POST",
        body,
      });
      setMessage({
        kind: "success",
        text: editingId
          ? `"${saved.title}" updated.`
          : saved.status === "published" ? `"${saved.title}" is now visible to students.` : `"${saved.title}" saved as a draft.`,
      });
      cancelEdit();
      load();
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage({ kind: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(item, status) {
    try {
      await api(`/api/opportunities/${item.id}/status`, { method: "PATCH", body: { status } });
      const verb = status === "archived" ? "archived and hidden from students" : status === "published" ? "published" : "moved to drafts";
      setMessage({ kind: "success", text: `"${item.title}" ${verb}.` });
      load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  const shown = items.filter((i) =>
    filter === "archived" ? i.status === "archived" : i.status !== "archived" && (!filter || i.kind === filter)
  );

  return (
    <>
      <PageHead title="Manage Content" subtitle="Publish jobs, internships, career events and announcements for students." />
      <Alert kind={message.kind}>{message.text}</Alert>

      <div className="admin-layout">
        <form className="card form-grid" onSubmit={handleSubmit} noValidate aria-labelledby="publish-title">
          <h2 id="publish-title" className="span-2 card-title">
            {editingId ? `Edit ${KIND_LABELS[form.kind].toLowerCase()}` : "Publish something new"}
          </h2>
          <Field id="kind" label="Type" as="select" value={form.kind} onChange={update} full>
            {Object.entries(KIND_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </Field>
          <Field id="title" label={isRole ? "Job title" : "Title"} value={form.title} onChange={update} error={errors.title} required />
          <Field id="organization" label={isRole ? "Organization" : "Posted by"} value={form.organization} onChange={update}
            error={errors.organization} placeholder={isRole ? "" : "e.g. University Career Center"} required />
          {form.kind !== "announcement" && (
            <Field id="location" label="Location" value={form.location} onChange={update} error={errors.location}
              placeholder={form.kind === "event" ? "Building and room, or online" : "City, State or Remote"} full />
          )}
          {form.kind === "event" && (
            <Field id="event_at" label="Date and time" type="datetime-local" value={form.event_at} onChange={update}
              error={errors.event_at} min={editingId ? undefined : localDateTimeInput(0)} required />
          )}
          {isRole && (
            <Field id="deadline" label="Application deadline" type="date" value={form.deadline} onChange={update}
              error={errors.deadline} />
          )}
          <Field id="status" label="Visibility" as="select" value={form.status} onChange={update}>
            <option value="published">Published (visible to students)</option>
            <option value="draft">Draft (hidden)</option>
          </Field>
          <Field id="description" label={form.kind === "announcement" ? "Message" : "Description"} as="textarea" rows={6}
            value={form.description} onChange={update} error={errors.description} required full
            hint={isRole ? "List requirements and 'nice to have' skills on separate lines; students' resume match uses them." : undefined} />
          {form.kind !== "announcement" && (
            <Field id="apply_url" label={isRole ? "Application link" : "Link (optional)"} type="url" value={form.apply_url}
              onChange={update} error={errors.apply_url} placeholder="https://" full />
          )}
          <div className="form-actions span-2">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : editingId ? "Save changes" : "Publish"}
            </button>
            {editingId && <button type="button" className="btn btn-ghost" onClick={cancelEdit}>Cancel</button>}
          </div>
        </form>

        <section aria-labelledby="all-listings">
          <h2 id="all-listings" className="section-title">Everything published ({items.length})</h2>
          <Tabs tabs={FILTERS} value={filter} onChange={setFilter} label="Filter content" />
          {shown.length === 0 ? <Empty>Nothing here.</Empty> : (
            <div className="opp-list">
              {shown.map((item) => (
                <OpportunityCard key={item.id} item={item} showStatus expanded={openId === item.id}
                  onToggle={() => setOpenId(openId === item.id ? null : item.id)}>
                  <span className="row-actions">
                    <button type="button" className="btn btn-small btn-secondary" onClick={() => startEdit(item)}>Edit</button>
                    {item.status === "archived" ? (
                      <button type="button" className="btn btn-small btn-ghost" onClick={() => setStatus(item, "published")}>Restore</button>
                    ) : (
                      <>
                        {item.status === "draft" && (
                          <button type="button" className="btn btn-small btn-ghost" onClick={() => setStatus(item, "published")}>Publish</button>
                        )}
                        <button type="button" className="btn btn-small btn-ghost danger" onClick={() => setStatus(item, "archived")}>Archive</button>
                      </>
                    )}
                  </span>
                </OpportunityCard>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
