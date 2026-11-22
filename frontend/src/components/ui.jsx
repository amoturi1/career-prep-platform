// Small shared building blocks.

export function Badge({ tone = "neutral", children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

const STATUS_TONES = {
  pending: "warn",
  accepted: "info",
  in_progress: "info",
  completed: "good",
  declined: "neutral",
  cancelled: "neutral",
  published: "good",
  draft: "warn",
  archived: "neutral",
  active: "info",
};

export function StatusBadge({ status, label }) {
  return <Badge tone={STATUS_TONES[status] ?? "neutral"}>{label ?? status.replace("_", " ")}</Badge>;
}

// Shown while an AI task runs, so the page never looks stuck (NFR-06).
export function Working({ children = "Working…" }) {
  return (
    <div className="working" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      {children}
    </div>
  );
}

export function Empty({ children }) {
  return <div className="card empty">{children}</div>;
}

export function Tabs({ tabs, value, onChange, label }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {tabs.map((t) => (
        <button key={t.value} type="button" aria-pressed={value === t.value}
          className={value === t.value ? "active" : ""} onClick={() => onChange(t.value)}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function PageHead({ title, subtitle, children }) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function AiNotice({ engine }) {
  return (
    <p className="ai-notice">
      <span aria-hidden="true">ⓘ</span> AI suggestions are advisory and may need checking. They don&apos;t
      predict hiring outcomes.{engine && <span className="muted"> Engine: {engine}.</span>}
    </p>
  );
}
