// Feedback on one mock-interview answer, with the reason behind each point (PB-25, NFR-09).
import { Badge } from "./ui.jsx";

const TONE = { Strong: "good", Good: "info", "Needs work": "warn" };

export default function AnswerFeedback({ feedback }) {
  return (
    <div className="feedback">
      <div className="feedback-head">
        <Badge tone={TONE[feedback.rating] ?? "neutral"}>{feedback.rating}</Badge>
        <span className="muted small">
          {feedback.score}/5 · {feedback.word_count} words
        </span>
      </div>
      <div className="feedback-grid">
        <div>
          <h4>What worked</h4>
          {feedback.strengths?.length ? (
            <ul>
              {feedback.strengths.map((p, i) => (
                <li key={i}><strong>{p.point}.</strong> <span className="muted">{p.why}</span></li>
              ))}
            </ul>
          ) : <p className="muted small">Nothing stood out yet. Try the structure below.</p>}
        </div>
        <div>
          <h4>To improve</h4>
          {feedback.improvements?.length ? (
            <ul>
              {feedback.improvements.map((p, i) => (
                <li key={i}><strong>{p.point}.</strong> <span className="muted">{p.why}</span></li>
              ))}
            </ul>
          ) : <p className="muted small">No major issues found.</p>}
        </div>
      </div>
      {feedback.suggestion && <p className="next-step">→ {feedback.suggestion}</p>}
    </div>
  );
}
