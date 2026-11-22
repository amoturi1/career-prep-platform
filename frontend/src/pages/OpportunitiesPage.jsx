// PB-14 browse jobs and internships, PB-15 event details, plus announcements.
import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import Alert from "../components/Alert.jsx";
import OpportunityCard from "../components/OpportunityCard.jsx";
import { Empty, PageHead, Tabs } from "../components/ui.jsx";

const KINDS = [
  { value: "", label: "All" },
  { value: "internship", label: "Internships" },
  { value: "job", label: "Jobs" },
  { value: "event", label: "Events" },
  { value: "announcement", label: "Announcements" },
];

export default function OpportunitiesPage() {
  const { api, user } = useAuth();
  const [items, setItems] = useState([]);
  const [kind, setKind] = useState("");
  const [openId, setOpenId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    api(`/api/opportunities${kind ? `?kind=${kind}` : ""}`)
      .then((data) => {
        // Upcoming events first (soonest on top), then everything else newest first.
        const events = data.filter((d) => d.kind === "event").sort((a, b) => (a.event_at ?? "").localeCompare(b.event_at ?? ""));
        setItems(kind === "event" ? events : data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);

  return (
    <>
      <PageHead title="Jobs & Events" subtitle="Opportunities, career events and news from your career center." />
      <Alert>{error}</Alert>
      <Tabs tabs={KINDS} value={kind} onChange={setKind} label="Filter by type" />

      {loading ? (
        <p className="page-status">Loading…</p>
      ) : items.length === 0 ? (
        <Empty>Nothing is published here right now. Check back soon.</Empty>
      ) : (
        <div className="opp-list">
          {items.map((item) => (
            <OpportunityCard key={item.id} item={item} expanded={openId === item.id}
              studentActions={user.role === "student"}
              onToggle={() => setOpenId(openId === item.id ? null : item.id)} />
          ))}
        </div>
      )}
    </>
  );
}
