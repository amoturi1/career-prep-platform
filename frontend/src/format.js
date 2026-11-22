// Date and number formatting shared by the pages.

export function formatDate(value) {
  if (!value) return "";
  const date = value.length === 10 ? new Date(value + "T00:00") : new Date(value);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return "";
  return new Date(value).toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// Server timestamps are UTC; SQLite may drop the "Z", so add it back before parsing.
export function formatTimestamp(value) {
  if (!value) return "";
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(value);
  return new Date(hasZone ? value : value + "Z").toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// Today's date in the user's own time zone, as YYYY-MM-DD.
export function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// A local date-time string for <input type="datetime-local">, `minutesAhead` from now.
export function localDateTimeInput(minutesAhead = 0) {
  const d = new Date(Date.now() + minutesAhead * 60000);
  d.setSeconds(0, 0);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function scoreBand(score) {
  if (score >= 75) return { label: "Strong match", tone: "good" };
  if (score >= 50) return { label: "Moderate match", tone: "ok" };
  if (score >= 25) return { label: "Early-stage match", tone: "warn" };
  return { label: "Weak match", tone: "bad" };
}
