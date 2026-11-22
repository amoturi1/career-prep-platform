// PB-20 compare resume with a job, PB-21 skill gaps, PB-22 explanations, PB-35 past results.
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import Alert from "../components/Alert.jsx";
import Field from "../components/Field.jsx";
import MatchResultView from "../components/MatchResultView.jsx";
import { Empty, PageHead, Tabs, Working } from "../components/ui.jsx";
import { formatTimestamp, scoreBand } from "../format.js";

export default function MatchPage() {
  const { api } = useAuth();
  const [params] = useSearchParams();
  const [resume, setResume] = useState(undefined); // undefined = loading, null = none
  const [listings, setListings] = useState([]);
  const [source, setSource] = useState(params.get("listing") ? "listing" : "paste");
  const [form, setForm] = useState({ opportunity_id: params.get("listing") ?? "", job_title: "", company: "", job_description: "" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api("/api/resumes/current").then(setResume).catch(() => setResume(null));
    api("/api/opportunities")
      .then((items) => setListings(items.filter((i) => i.kind === "job" || i.kind === "internship")))
      .catch(() => setListings([]));
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadHistory() {
    api("/api/match").then(setHistory).catch(() => setHistory([]));
  }

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function analyze(e) {
    e.preventDefault();
    setMessage("");
    const found = {};
    if (source === "listing" && !form.opportunity_id) found.opportunity_id = "Choose a listing.";
    if (source === "paste" && form.job_description.trim().length < 30)
      found.job_description = "Paste the job description (at least 30 characters).";
    setErrors(found);
    if (Object.keys(found).length) return;

    const body =
      source === "listing"
        ? { opportunity_id: Number(form.opportunity_id) }
        : { job_title: form.job_title, company: form.company, job_description: form.job_description };
    setBusy(true);
    setResult(null);
    try {
      const saved = await api("/api/match", { method: "POST", body });
      setResult(saved);
      loadHistory();
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function openPast(id) {
    setMessage("");
    try {
      setResult(await api(`/api/match/${id}`));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function removePast(item) {
    if (!window.confirm(`Delete the analysis for "${item.job_title}"?`)) return;
    try {
      await api(`/api/match/${item.id}`, { method: "DELETE" });
      if (result?.id === item.id) setResult(null);
      loadHistory();
    } catch (err) {
      setMessage(err.message);
    }
  }

  if (resume === undefined) return <p className="page-status">Loading…</p>;

  return (
    <>
      <PageHead title="Resume Match"
        subtitle="Compare your resume with a job description to see where you match and what to work on." />
      <Alert>{message}</Alert>

      {!resume ? (
        <Empty>
          <p>Add your resume first. Then you can compare it with any job.</p>
          <Link to="/resume" className="btn btn-primary">Add my resume</Link>
        </Empty>
      ) : (
        <form className="card" onSubmit={analyze} noValidate>
          <p className="muted small">
            Using your current resume: <strong>{resume.filename}</strong> ({resume.word_count} words).{" "}
            <Link to="/resume">Change</Link>
          </p>
          <Tabs label="Job source" value={source} onChange={(v) => { setSource(v); setErrors({}); }}
            tabs={[{ value: "paste", label: "Paste a job description" }, { value: "listing", label: "Choose a published listing" }]} />

          {source === "listing" ? (
            <Field id="opportunity_id" label="Listing" as="select" value={form.opportunity_id} onChange={update}
              error={errors.opportunity_id} required>
              <option value="">Choose a job or internship…</option>
              {listings.map((l) => <option key={l.id} value={l.id}>{l.title} · {l.organization}</option>)}
            </Field>
          ) : (
            <div className="form-grid">
              <Field id="job_title" label="Job title" value={form.job_title} onChange={update} error={errors.job_title}
                placeholder="e.g. Software Engineering Intern" />
              <Field id="company" label="Company" value={form.company} onChange={update} error={errors.company} />
              <Field id="job_description" label="Job description" as="textarea" rows={9} full required
                value={form.job_description} onChange={update} error={errors.job_description}
                hint="Paste the whole posting, including the requirements and 'nice to have' sections."
                placeholder={"Requirements:\n- Python or Java\n- SQL\nNice to have:\n- AWS"} />
            </div>
          )}
          {busy ? <Working>Comparing your resume with the job…</Working> : (
            <button type="submit" className="btn btn-primary">Analyze match</button>
          )}
        </form>
      )}

      {result && <MatchResultView match={result} />}

      <section className="section" aria-labelledby="past-title">
        <h2 id="past-title" className="section-title">Past results</h2>
        {history.length === 0 ? (
          <p className="muted">Your analyses will be saved here so you can compare postings over time.</p>
        ) : (
          <div className="card table-card">
            <table>
              <thead>
                <tr>
                  <th scope="col">Role</th>
                  <th scope="col">Score</th>
                  <th scope="col">Date</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => {
                  const band = scoreBand(h.score);
                  return (
                    <tr key={h.id} className={result?.id === h.id ? "row-selected" : ""}>
                      <td data-label="Role"><strong>{h.job_title}</strong>{h.company && <div className="muted small">{h.company}</div>}</td>
                      <td data-label="Score"><span className={`score-pill tone-${band.tone}`}>{h.score}</span></td>
                      <td data-label="Date">{formatTimestamp(h.created_at)}</td>
                      <td className="row-actions">
                        <button type="button" className="btn btn-small btn-secondary" onClick={() => openPast(h.id)}>View</button>
                        <button type="button" className="btn btn-small btn-ghost danger" onClick={() => removePast(h)}>Delete</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
