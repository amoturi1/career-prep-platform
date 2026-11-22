// PB-08 view applications, PB-09 update status, PB-12 delete, PB-13 filter by status.
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { APPLICATION_STATUSES } from "../api.js";
import Alert from "../components/Alert.jsx";

export default function ApplicationsPage() {
  const { api } = useAuth();
  const location = useLocation();
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(location.state?.notice ?? "");

  useEffect(() => {
    setLoading(true);
    api(`/api/applications${filter ? `?status=${encodeURIComponent(filter)}` : ""}`)
      .then(setItems)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function changeStatus(item, status) {
    setError("");
    setNotice("");
    try {
      const updated = await api(`/api/applications/${item.id}/status`, { method: "PATCH", body: { status } });
      setItems((list) =>
        filter && updated.status !== filter
          ? list.filter((a) => a.id !== item.id)
          : list.map((a) => (a.id === item.id ? updated : a))
      );
      setNotice(`${item.company} moved to ${status}.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(item) {
    if (!window.confirm(`Delete your application to ${item.company}? This can't be undone.`)) return;
    setError("");
    try {
      await api(`/api/applications/${item.id}`, { method: "DELETE" });
      setItems((list) => list.filter((a) => a.id !== item.id));
      setNotice(`Application to ${item.company} deleted.`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My Applications</h1>
          <p className="muted">Every job and internship you&apos;re tracking, in one place.</p>
        </div>
        <Link to="/applications/new" className="btn btn-primary">+ Add application</Link>
      </div>

      <Alert>{error}</Alert>
      <Alert kind="success">{notice}</Alert>

      <div className="toolbar">
        <label htmlFor="status-filter">Filter by status</label>
        <select id="status-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All</option>
          {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading ? (
        <p className="page-status">Loading applications…</p>
      ) : items.length === 0 ? (
        <div className="card empty">
          <p>{filter ? `No applications with status "${filter}".` : "You haven't added any applications yet."}</p>
          {!filter && <Link to="/applications/new" className="btn btn-secondary">Add your first one</Link>}
        </div>
      ) : (
        <div className="card table-card">
          <table>
            <thead>
              <tr>
                <th scope="col">Company</th>
                <th scope="col">Role</th>
                <th scope="col">Date applied</th>
                <th scope="col">Status</th>
                <th scope="col"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td data-label="Company">
                    <strong>{item.company}</strong>
                    {item.notes && <div className="muted small clamp">{item.notes}</div>}
                  </td>
                  <td data-label="Role">{item.job_title}</td>
                  <td data-label="Date applied">
                    {item.date_applied ? new Date(item.date_applied + "T00:00").toLocaleDateString() : "—"}
                  </td>
                  <td data-label="Status">
                    <select
                      aria-label={`Status for ${item.company}`}
                      className={`status-select status-${item.status.toLowerCase()}`}
                      value={item.status}
                      onChange={(e) => changeStatus(item, e.target.value)}
                    >
                      {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="row-actions">
                    <Link to={`/applications/${item.id}/edit`} className="btn btn-small btn-secondary">Edit</Link>
                    <button type="button" className="btn btn-small btn-ghost danger" onClick={() => remove(item)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
