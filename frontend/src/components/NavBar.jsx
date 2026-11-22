import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

const LINKS = {
  student: [
    { to: "/applications", label: "Applications" },
    { to: "/profile", label: "Profile" },
    { to: "/resume", label: "Resume" },
    { to: "/match", label: "Resume Match" },
    { to: "/interview", label: "Mock Interview" },
    { to: "/mentors", label: "Mentors" },
    { to: "/opportunities", label: "Jobs & Events" },
  ],
  mentor: [
    { to: "/mentor/requests", label: "Requests" },
    { to: "/mentor/availability", label: "Availability" },
    { to: "/mentor/students", label: "My Students" },
    { to: "/opportunities", label: "Jobs & Events" },
  ],
  admin: [
    { to: "/admin/content", label: "Content" },
    { to: "/admin/users", label: "Users" },
    { to: "/admin/analytics", label: "Analytics" },
    { to: "/opportunities", label: "Student View" },
  ],
};

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <NavLink to="/" className="brand">
          <span className="brand-mark" aria-hidden="true">CP</span>
          Career Prep
        </NavLink>
        {user && (
          <div className="topbar-user">
            <span className="user-name">
              {user.full_name} <span className="role-tag">{user.role}</span>
            </span>
            <button type="button" className="btn btn-ghost btn-small" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        )}
      </div>
      {user && (
        <nav className="nav-row" aria-label="Main">
          <div className="nav-inner">
            {(LINKS[user.role] ?? []).map((link) => (
              <NavLink key={link.to} to={link.to} className="nav-link">
                {link.label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
