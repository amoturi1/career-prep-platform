// PB-23 start a mock interview, PB-24 answer questions, PB-25 review feedback.
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import Alert from "../components/Alert.jsx";
import AnswerFeedback from "../components/AnswerFeedback.jsx";
import Field from "../components/Field.jsx";
import { AiNotice, PageHead, StatusBadge, Working } from "../components/ui.jsx";
import { formatTimestamp } from "../format.js";

function wordCount(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

export default function InterviewPage() {
  const { api } = useAuth();
  const [params] = useSearchParams();
  const [listings, setListings] = useState([]);
  const [setup, setSetup] = useState({ role: "", focus: "", opportunity_id: params.get("listing") ?? "", question_count: "5" });
  const [errors, setErrors] = useState({});
  const [session, setSession] = useState(null);
  const [history, setHistory] = useState([]);
  const [answer, setAnswer] = useState("");
  const [lastIndex, setLastIndex] = useState(null); // question whose feedback is showing
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api("/api/opportunities")
      .then((items) => {
        const roles = items.filter((i) => i.kind === "job" || i.kind === "internship");
        setListings(roles);
        const chosen = roles.find((l) => String(l.id) === params.get("listing"));
        if (chosen) setSetup((s) => ({ ...s, role: chosen.title }));
      })
      .catch(() => setListings([]));
    api("/api/profile")
      .then((p) => setSetup((s) => (s.role ? s : { ...s, role: p.target_role })))
      .catch(() => {});
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function loadHistory() {
    api("/api/interviews").then(setHistory).catch(() => setHistory([]));
  }

  const update = (e) => setSetup({ ...setup, [e.target.name]: e.target.value });

  async function start(e) {
    e.preventDefault();
    setMessage("");
    if (!setup.role.trim()) return setErrors({ role: "Enter the role you're practicing for." });
    setErrors({});
    setBusy("start");
    try {
      const created = await api("/api/interviews", {
        method: "POST",
        body: {
          role: setup.role,
          focus: setup.focus,
          question_count: Number(setup.question_count),
          opportunity_id: setup.opportunity_id ? Number(setup.opportunity_id) : null,
        },
      });
      setSession(created);
      setAnswer("");
      setLastIndex(null);
      loadHistory();
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage(err.message);
    } finally {
      setBusy("");
    }
  }

  async function open(id) {
    setMessage("");
    try {
      setSession(await api(`/api/interviews/${id}`));
      setAnswer("");
      setLastIndex(null);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setMessage(err.message);
    }
  }

  const answered = new Map((session?.answers ?? []).map((a) => [a.question_index, a]));
  const nextIndex = session ? session.questions.findIndex((_, i) => !answered.has(i)) : -1;
  const showingFeedback = lastIndex !== null && answered.has(lastIndex);
  const finished = session && (session.status === "completed" || nextIndex === -1);

  async function submitAnswer(e) {
    e.preventDefault();
    setMessage("");
    if (wordCount(answer) < 1) return setErrors({ answer: "Type your answer first." });
    setErrors({});
    setBusy("answer");
    try {
      await api(`/api/interviews/${session.id}/answers`, {
        method: "POST",
        body: { question_index: nextIndex, answer },
      });
      setLastIndex(nextIndex);
      setAnswer("");
      setSession(await api(`/api/interviews/${session.id}`));
      loadHistory();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy("");
    }
  }

  async function finishEarly() {
    setMessage("");
    try {
      setSession(await api(`/api/interviews/${session.id}/finish`, { method: "POST" }));
      setLastIndex(null);
      loadHistory();
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <>
      <PageHead title="Mock Interview" subtitle="Practice answering interview questions and get feedback on each answer.">
        {session && (
          <button type="button" className="btn btn-secondary" onClick={() => { setSession(null); setMessage(""); }}>
            New practice session
          </button>
        )}
      </PageHead>
      <Alert>{message}</Alert>

      {!session && (
        <form className="card form-grid" onSubmit={start} noValidate>
          <Field id="role" label="Role you're practicing for" value={setup.role} onChange={update} error={errors.role}
            placeholder="e.g. Software Engineering Intern" required />
          <Field id="question_count" label="Number of questions" as="select" value={setup.question_count} onChange={update}>
            {[3, 4, 5, 6, 8].map((n) => <option key={n} value={n}>{n} questions</option>)}
          </Field>
          <Field id="opportunity_id" label="Base questions on a listing (optional)" as="select" full
            value={setup.opportunity_id} onChange={update}>
            <option value="">No listing</option>
            {listings.map((l) => <option key={l.id} value={l.id}>{l.title} · {l.organization}</option>)}
          </Field>
          <Field id="focus" label="Topics or job description (optional)" as="textarea" rows={4} full
            value={setup.focus} onChange={update} error={errors.focus}
            hint="Skills you list here (for example SQL, React, teamwork) shape the technical questions." />
          <div className="form-actions span-2">
            {busy === "start" ? <Working>Preparing your questions…</Working> : (
              <button type="submit" className="btn btn-primary">Start practice</button>
            )}
          </div>
        </form>
      )}

      {session && (
        <section className="card interview" aria-labelledby="session-title">
          <div className="interview-head">
            <div>
              <p className="eyebrow">Practice session</p>
              <h2 id="session-title" className="result-title">{session.role}</h2>
            </div>
            <div className="progress-wrap" aria-label={`${session.answered_count} of ${session.question_count} answered`}>
              <div className="progress-bar"><span style={{ width: `${(100 * session.answered_count) / session.question_count}%` }} /></div>
              <span className="muted small">{session.answered_count}/{session.question_count} answered</span>
            </div>
          </div>

          {showingFeedback && !finished && (
            <div className="qa-block">
              <p className="question"><span className="q-num">Q{lastIndex + 1}</span> {answered.get(lastIndex).question}</p>
              <AnswerFeedback feedback={answered.get(lastIndex).feedback} />
              <button type="button" className="btn btn-primary" onClick={() => setLastIndex(null)}>
                Next question →
              </button>
            </div>
          )}

          {!showingFeedback && !finished && (
            <form className="qa-block" onSubmit={submitAnswer} noValidate>
              <p className="question"><span className="q-num">Q{nextIndex + 1}</span> {session.questions[nextIndex]}</p>
              <Field id="answer" label="Your answer" as="textarea" rows={8} value={answer}
                onChange={(e) => setAnswer(e.target.value)} error={errors.answer}
                hint={`${wordCount(answer)} words · Tip: describe the situation, what you did, and the result.`} />
              <div className="form-actions">
                {busy === "answer" ? <Working>Reviewing your answer…</Working> : (
                  <>
                    <button type="submit" className="btn btn-primary">Submit answer</button>
                    {session.answered_count > 0 && (
                      <button type="button" className="btn btn-ghost" onClick={finishEarly}>Finish session</button>
                    )}
                  </>
                )}
              </div>
            </form>
          )}

          {finished && (
            <div className="summary">
              <h3 className="sub-title">Session complete</h3>
              <p>
                You answered {session.answered_count} of {session.question_count} questions
                {session.average_score !== null && <> with an average score of <strong>{session.average_score}/5</strong></>}.
                Review each answer below.
              </p>
              {session.answers.map((a) => (
                <details key={a.question_index} className="review">
                  <summary><span className="q-num">Q{a.question_index + 1}</span> {a.question}
                    <span className="muted small"> · {a.feedback.rating}</span></summary>
                  <blockquote className="your-answer">{a.answer}</blockquote>
                  <AnswerFeedback feedback={a.feedback} />
                </details>
              ))}
            </div>
          )}
          <AiNotice engine={session.engine} />
        </section>
      )}

      <section className="section" aria-labelledby="history-title">
        <h2 id="history-title" className="section-title">Past sessions</h2>
        {history.length === 0 ? <p className="muted">Your practice sessions will appear here.</p> : (
          <div className="card table-card">
            <table>
              <thead>
                <tr>
                  <th scope="col">Role</th>
                  <th scope="col">Answered</th>
                  <th scope="col">Average</th>
                  <th scope="col">Started</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className={session?.id === h.id ? "row-selected" : ""}>
                    <td data-label="Role"><strong>{h.role}</strong> <StatusBadge status={h.status} /></td>
                    <td data-label="Answered">{h.answered_count}/{h.question_count}</td>
                    <td data-label="Average">{h.average_score !== null ? `${h.average_score}/5` : "—"}</td>
                    <td data-label="Started">{formatTimestamp(h.created_at)}</td>
                    <td className="row-actions">
                      <button type="button" className="btn btn-small btn-secondary" onClick={() => open(h.id)}>
                        {h.status === "active" ? "Continue" : "Review"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
