// PB-04 create profile, PB-05 edit profile, PB-06 view profile summary.
import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import Field from "../components/Field.jsx";
import Alert from "../components/Alert.jsx";

const EMPTY = { education: "", skills: "", experience: "", interests: "", target_role: "" };
const REQUIRED = ["education", "skills", "target_role"];

export default function ProfilePage() {
  const { api, user } = useAuth();
  const [profile, setProfile] = useState(null); // saved version
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState({ kind: "error", text: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api("/api/profile")
      .then((data) => setProfile(data))
      .catch((err) => {
        if (err.status === 404) setEditing(true); // no profile yet: show the create form
        else setMessage({ kind: "error", text: err.message });
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  function startEditing() {
    setForm({ ...EMPTY, ...profile });
    setErrors({});
    setMessage({ kind: "error", text: "" });
    setEditing(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const found = {};
    for (const key of REQUIRED) if (!form[key].trim()) found[key] = "This field is required.";
    setErrors(found);
    if (Object.keys(found).length) return;

    setSaving(true);
    try {
      const { education, skills, experience, interests, target_role } = form;
      const saved = await api("/api/profile", {
        method: profile ? "PUT" : "POST",
        body: { education, skills, experience, interests, target_role },
      });
      setProfile(saved);
      setEditing(false);
      setMessage({ kind: "success", text: "Profile saved." });
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage({ kind: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="page-status">Loading your profile…</p>;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My Profile</h1>
          <p className="muted">Your education, skills and goals, used across your career preparation.</p>
        </div>
        {profile && !editing && (
          <button type="button" className="btn btn-secondary" onClick={startEditing}>
            Edit profile
          </button>
        )}
      </div>

      <Alert kind={message.kind}>{message.text}</Alert>

      {editing ? (
        <form className="card" onSubmit={handleSubmit} noValidate>
          {!profile && (
            <p className="muted">
              Welcome, {user.full_name.split(" ")[0]}! Create your profile to get started.
            </p>
          )}
          <Field id="target_role" label="Target role" value={form.target_role} onChange={update}
            error={errors.target_role} placeholder="e.g. Software Engineering Intern" required />
          <Field id="education" label="Education" as="textarea" rows={3} value={form.education} onChange={update}
            error={errors.education} placeholder="Degree, school, expected graduation" required />
          <Field id="skills" label="Skills" as="textarea" rows={3} value={form.skills} onChange={update}
            error={errors.skills} hint="Separate skills with commas." required />
          <Field id="experience" label="Experience" as="textarea" rows={4} value={form.experience} onChange={update}
            error={errors.experience} placeholder="Jobs, internships, projects, volunteering" />
          <Field id="interests" label="Career interests" as="textarea" rows={2} value={form.interests}
            onChange={update} error={errors.interests} />
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : "Save profile"}
            </button>
            {profile && (
              <button type="button" className="btn btn-ghost" onClick={() => setEditing(false)}>
                Cancel
              </button>
            )}
          </div>
        </form>
      ) : (
        <section className="card profile-summary" aria-label="Profile summary">
          <dl>
            <div><dt>Target role</dt><dd>{profile.target_role}</dd></div>
            <div><dt>Education</dt><dd>{profile.education}</dd></div>
            <div>
              <dt>Skills</dt>
              <dd className="chips">
                {profile.skills.split(",").map((s) => s.trim()).filter(Boolean).map((skill) => (
                  <span key={skill} className="chip">{skill}</span>
                ))}
              </dd>
            </div>
            <div><dt>Experience</dt><dd>{profile.experience || <span className="muted">Not added yet</span>}</dd></div>
            <div><dt>Career interests</dt><dd>{profile.interests || <span className="muted">Not added yet</span>}</dd></div>
          </dl>
          <p className="muted small">Last updated {new Date(profile.updated_at).toLocaleString()}</p>
        </section>
      )}
    </>
  );
}
