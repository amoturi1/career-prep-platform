// PB-30 manage account status and roles.
import { useEffect, useState } from "react";
import { useAuth } from "../../auth.jsx";
import Alert from "../../components/Alert.jsx";
import { Badge, Empty, PageHead } from "../../components/ui.jsx";
import { formatTimestamp } from "../../format.js";

const ROLES = ["student", "mentor", "admin"];

export default function AdminUsersPage() {
  const { api, user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [role, setRole] = useState("");
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState({ kind: "error", text: "" });

  function load() {
    const params = new URLSearchParams();
    if (role) params.set("role", role);
    if (search.trim()) params.set("search", search.trim());
    api(`/api/admin/users?${params}`).then(setUsers).catch((err) => setMessage({ kind: "error", text: err.message }));
  }

  useEffect(() => {
    const timer = setTimeout(load, 250); // wait for typing to pause
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, search]);

  async function change(target, body, text) {
    if (body.role === "admin" && !window.confirm(`Give ${target.full_name} full administrator access?`)) return;
    try {
      await api(`/api/admin/users/${target.id}`, { method: "PATCH", body });
      setMessage({ kind: "success", text });
      load();
    } catch (err) {
      setMessage({ kind: "error", text: err.message });
      load();
    }
  }

  return (
    <>
      <PageHead title="Users" subtitle="Change roles (for example, make someone a mentor) and activate or deactivate accounts." />
      <Alert kind={message.kind}>{message.text}</Alert>

      <div className="toolbar">
        <label htmlFor="user-search">Search</label>
        <input id="user-search" type="search" value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Name or email" className="toolbar-input" />
        <label htmlFor="role-filter">Role</label>
        <select id="role-filter" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">All</option>
          {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {users.length === 0 ? <Empty>No users match.</Empty> : (
        <div className="card table-card">
          <table>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Role</th>
                <th scope="col">Status</th>
                <th scope="col">Joined</th>
                <th scope="col"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isMe = u.id === me.id;
                return (
                  <tr key={u.id}>
                    <td data-label="Name"><strong>{u.full_name}</strong>{isMe && <span className="muted"> (you)</span>}
                      <div className="muted small">{u.email}</div></td>
                    <td data-label="Role">
                      <select aria-label={`Role for ${u.full_name}`} value={u.role} disabled={isMe}
                        onChange={(e) => change(u, { role: e.target.value }, `${u.full_name} is now a ${e.target.value}.`)}>
                        {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </td>
                    <td data-label="Status">
                      {u.is_active ? <Badge tone="good">Active</Badge> : <Badge tone="neutral">Deactivated</Badge>}
                    </td>
                    <td data-label="Joined">{formatTimestamp(u.created_at)}</td>
                    <td className="row-actions">
                      {!isMe && (u.is_active ? (
                        <button type="button" className="btn btn-small btn-ghost danger"
                          onClick={() => window.confirm(`Deactivate ${u.full_name}? They'll be signed out and can't sign in.`) &&
                            change(u, { is_active: false }, `${u.full_name} has been deactivated.`)}>
                          Deactivate
                        </button>
                      ) : (
                        <button type="button" className="btn btn-small btn-secondary"
                          onClick={() => change(u, { is_active: true }, `${u.full_name} can sign in again.`)}>
                          Reactivate
                        </button>
                      ))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
