// Shows one resume-to-job analysis: score, explained matches, gaps and suggestions (PB-20, PB-21, PB-22).
import { formatTimestamp, scoreBand } from "../format.js";
import { AiNotice, Badge } from "./ui.jsx";

const PRIORITY = { high: { label: "Required", tone: "bad" }, medium: { label: "Mentioned", tone: "warn" }, low: { label: "Nice to have", tone: "neutral" } };

function ScoreRing({ score }) {
  const band = scoreBand(score);
  const angle = Math.round((score / 100) * 360);
  return (
    <div className={`score-ring tone-${band.tone}`} style={{ "--angle": `${angle}deg` }}
      role="img" aria-label={`Match score ${score} out of 100: ${band.label}`}>
      <div className="score-inner">
        <span className="score-value">{score}</span>
        <span className="score-max">/100</span>
      </div>
    </div>
  );
}

function Gap({ gap }) {
  const p = PRIORITY[gap.priority] ?? PRIORITY.medium;
  return (
    <li className="explain-item">
      <div className="explain-head">
        <strong>{gap.skill}</strong> <Badge tone={p.tone}>{p.label}</Badge>
        {gap.category && <span className="muted small"> · {gap.category}</span>}
      </div>
      {gap.requirement && <p className="quote"><span className="quote-label">Job says:</span> “{gap.requirement}”</p>}
      <p className="next-step">→ {gap.suggestion}</p>
    </li>
  );
}

export default function MatchResultView({ match }) {
  const r = match.result;
  const band = scoreBand(match.score);
  return (
    <section className="card result" aria-labelledby="result-title">
      <div className="result-head">
        <ScoreRing score={match.score} />
        <div>
          <p className="eyebrow">{band.label}</p>
          <h2 id="result-title" className="result-title">
            {match.job_title}{match.company && <span className="muted"> · {match.company}</span>}
          </h2>
          <p>{r.summary}</p>
          <p className="muted small">Analyzed {formatTimestamp(match.created_at)}</p>
        </div>
      </div>

      <div className="result-grid">
        <div>
          <h3 className="sub-title">✓ Where you match ({r.matched.length})</h3>
          {r.matched.length === 0 ? <p className="muted">No matching skills were found yet.</p> : (
            <ul className="explain-list">
              {r.matched.map((m) => (
                <li key={m.skill} className="explain-item">
                  <div className="explain-head"><strong>{m.skill}</strong>
                    {m.category && <span className="muted small"> · {m.category}</span>}</div>
                  {m.requirement && <p className="quote"><span className="quote-label">Job says:</span> “{m.requirement}”</p>}
                  {m.evidence && <p className="quote good"><span className="quote-label">Your resume:</span> “{m.evidence}”</p>}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="sub-title">△ Skill gaps to work on ({r.missing.length})</h3>
          {r.missing.length === 0 ? <p className="muted">No missing skills were found for this posting.</p> : (
            <ul className="explain-list">{r.missing.map((g) => <Gap key={g.skill} gap={g} />)}</ul>
          )}
          {r.under_evidenced?.length > 0 && (
            <>
              <h3 className="sub-title">◐ On your profile, missing from your resume ({r.under_evidenced.length})</h3>
              <ul className="explain-list">{r.under_evidenced.map((g) => <Gap key={g.skill} gap={g} />)}</ul>
            </>
          )}
        </div>
      </div>

      {r.suggestions?.length > 0 && (
        <>
          <h3 className="sub-title">Suggested next steps</h3>
          <ol className="steps">{r.suggestions.map((s, i) => <li key={i}>{s}</li>)}</ol>
        </>
      )}

      {r.limitations?.length > 0 && (
        <details className="limits">
          <summary>What this analysis can&apos;t tell you</summary>
          <ul>{r.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>
        </details>
      )}
      <AiNotice engine={match.engine} />
    </section>
  );
}
