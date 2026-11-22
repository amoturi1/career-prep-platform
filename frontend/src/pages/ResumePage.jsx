// PB-18 add a resume, PB-19 replace it (every upload is kept as a version; one is current).
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import Alert from "../components/Alert.jsx";
import Field from "../components/Field.jsx";
import { Badge, PageHead, Tabs, Working } from "../components/ui.jsx";
import { formatTimestamp } from "../format.js";

const SOURCE_LABELS = { pdf: "PDF", docx: "Word", txt: "Text file", pasted: "Pasted" };
const MAX_MB = 2;

export default function ResumePage() {
  const { api } = useAuth();
  const [versions, setVersions] = useState([]);
  const [current, setCurrent] = useState(null);
  const [mode, setMode] = useState("upload");
  const [file, setFile] = useState(null);
  const [pasted, setPasted] = useState("");
  const [busy, setBusy] = useState(false);
  const [showText, setShowText] = useState(false);
  const [message, setMessage] = useState({ kind: "error", text: "" });
  const [fieldError, setFieldError] = useState("");
  const fileInput = useRef(null);

  async function load() {
    try {
      const list = await api("/api/resumes");
      setVersions(list);
      setCurrent(list.length ? await api("/api/resumes/current") : null);
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(e) {
    e.preventDefault();
    setMessage({ kind: "error", text: "" });
    setFieldError("");
    let request;
    if (mode === "upload") {
      if (!file) return setFieldError("Choose a file to upload.");
      if (!/\.(pdf|docx|txt)$/i.test(file.name)) return setFieldError("Upload a PDF, Word (.docx) or .txt file.");
      if (file.size > MAX_MB * 1024 * 1024) return setFieldError(`The file is larger than ${MAX_MB} MB.`);
      const form = new FormData();
      form.append("file", file);
      request = api("/api/resumes/upload", { method: "POST", body: form });
    } else {
      if (pasted.trim().length < 50) return setFieldError("Paste at least a few lines of your resume (50+ characters).");
      request = api("/api/resumes/text", { method: "POST", body: { text: pasted } });
    }
    setBusy(true);
    try {
      const saved = await request;
      setMessage({
        kind: "success",
        text: `${current ? "Resume replaced" : "Resume added"}: we found ${saved.word_count} words. It's now your current version.`,
      });
      setFile(null);
      setPasted("");
      if (fileInput.current) fileInput.current.value = "";
      await load();
    } catch (err) {
      setFieldError(err.fieldErrors?.text ?? "");
      setMessage({ kind: "error", text: err.message });
    } finally {
      setBusy(false);
    }
  }

  async function makeCurrent(version) {
    try {
      await api(`/api/resumes/${version.id}/make-current`, { method: "POST" });
      setMessage({ kind: "success", text: `"${version.filename}" is now your current resume.` });
      await load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  async function remove(version) {
    if (!window.confirm(`Delete "${version.filename}"? Past analyses stay, but this version's text is removed.`)) return;
    try {
      await api(`/api/resumes/${version.id}`, { method: "DELETE" });
      setMessage({ kind: "success", text: "Resume version deleted." });
      await load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
    }
  }

  return (
    <>
      <PageHead title="My Resume" subtitle="Add your resume so you can compare it with jobs and share it with mentors.">
        {current && <Link to="/match" className="btn btn-primary">Compare with a job →</Link>}
      </PageHead>

      <Alert kind={message.kind}>{message.text}</Alert>

      <div className="two-col">
        <section className="card" aria-labelledby="current-title">
          <h2 id="current-title" className="card-title">Current resume</h2>
          {current ? (
            <>
              <p>
                <strong>{current.filename}</strong> <Badge>{SOURCE_LABELS[current.source] ?? current.source}</Badge>
              </p>
              <p className="muted small">
                {current.word_count} words · added {formatTimestamp(current.uploaded_at)}
              </p>
              <button type="button" className="link-button" onClick={() => setShowText(!showText)} aria-expanded={showText}>
                {showText ? "Hide text" : "Show the text we read"}
              </button>
              {showText && <pre className="resume-text">{current.text}</pre>}
              <p className="muted small privacy-note">
                Only the text of your resume is stored, not the file. Mentors see it only if you choose to share it
                on a request.
              </p>
            </>
          ) : (
            <p className="muted">You haven&apos;t added a resume yet.</p>
          )}
        </section>

        <form className="card" onSubmit={submit} noValidate aria-labelledby="add-title">
          <h2 id="add-title" className="card-title">{current ? "Replace your resume" : "Add your resume"}</h2>
          <Tabs label="How to add" value={mode} onChange={(m) => { setMode(m); setFieldError(""); }}
            tabs={[{ value: "upload", label: "Upload a file" }, { value: "paste", label: "Paste text" }]} />
          {mode === "upload" ? (
            <Field id="resume-file" label="Resume file" type="file" accept=".pdf,.docx,.txt" ref={fileInput}
              hint={`PDF, Word (.docx) or .txt, up to ${MAX_MB} MB.`} error={fieldError}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          ) : (
            <Field id="resume-text" label="Resume text" as="textarea" rows={10} value={pasted} error={fieldError}
              onChange={(e) => setPasted(e.target.value)} placeholder="Paste the full text of your resume" />
          )}
          {busy ? <Working>Reading your resume…</Working> : (
            <button type="submit" className="btn btn-primary">{current ? "Replace resume" : "Add resume"}</button>
          )}
        </form>
      </div>

      {versions.length > 0 && (
        <section aria-labelledby="versions-title" className="section">
          <h2 id="versions-title" className="section-title">All versions</h2>
          <div className="card table-card">
            <table>
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Added</th>
                  <th scope="col">Words</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.id}>
                    <td data-label="File">
                      {v.filename} {v.is_current && <Badge tone="good">Current</Badge>}
                    </td>
                    <td data-label="Added">{formatTimestamp(v.uploaded_at)}</td>
                    <td data-label="Words">{v.word_count}</td>
                    <td className="row-actions">
                      {!v.is_current && (
                        <button type="button" className="btn btn-small btn-secondary" onClick={() => makeCurrent(v)}>
                          Use this version
                        </button>
                      )}
                      <button type="button" className="btn btn-small btn-ghost danger" onClick={() => remove(v)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
