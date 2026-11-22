import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { homePathFor, useAuth } from "./auth.jsx";
import NavBar from "./components/NavBar.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import ApplicationsPage from "./pages/ApplicationsPage.jsx";
import ApplicationFormPage from "./pages/ApplicationFormPage.jsx";
import OpportunitiesPage from "./pages/OpportunitiesPage.jsx";
import ResumePage from "./pages/ResumePage.jsx";
import MatchPage from "./pages/MatchPage.jsx";
import InterviewPage from "./pages/InterviewPage.jsx";
import MentorsPage from "./pages/MentorsPage.jsx";
import MentorRequestsPage from "./pages/mentor/MentorRequestsPage.jsx";
import MentorAvailabilityPage from "./pages/mentor/MentorAvailabilityPage.jsx";
import MentorStudentsPage from "./pages/mentor/MentorStudentsPage.jsx";
import AdminContentPage from "./pages/admin/AdminContentPage.jsx";
import AdminUsersPage from "./pages/admin/AdminUsersPage.jsx";
import AdminAnalyticsPage from "./pages/admin/AdminAnalyticsPage.jsx";

// Only lets signed-in users with an allowed role through (NFR-01).
function Protected({ roles, children }) {
  const { user, checking } = useAuth();
  const location = useLocation();
  if (checking) return <p className="page-status">Loading…</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homePathFor(user)} replace />;
  return children;
}

const student = ["student"];
const mentor = ["mentor"];
const admin = ["admin"];

export default function App() {
  const { user } = useAuth();

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <NavBar />
      <main id="main" className="container">
        <Routes>
          <Route path="/" element={<Navigate to={homePathFor(user)} replace />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/register" element={<AuthPage mode="register" />} />

          {/* Students */}
          <Route path="/applications" element={<Protected roles={student}><ApplicationsPage /></Protected>} />
          <Route path="/applications/new" element={<Protected roles={student}><ApplicationFormPage /></Protected>} />
          <Route path="/applications/:id/edit" element={<Protected roles={student}><ApplicationFormPage /></Protected>} />
          <Route path="/profile" element={<Protected roles={student}><ProfilePage /></Protected>} />
          <Route path="/resume" element={<Protected roles={student}><ResumePage /></Protected>} />
          <Route path="/match" element={<Protected roles={student}><MatchPage /></Protected>} />
          <Route path="/interview" element={<Protected roles={student}><InterviewPage /></Protected>} />
          <Route path="/mentors" element={<Protected roles={student}><MentorsPage /></Protected>} />

          {/* Everyone signed in */}
          <Route path="/opportunities" element={<Protected><OpportunitiesPage /></Protected>} />
          <Route path="/jobs" element={<Navigate to="/opportunities" replace />} />

          {/* Mentors */}
          <Route path="/mentor/requests" element={<Protected roles={mentor}><MentorRequestsPage /></Protected>} />
          <Route path="/mentor/availability" element={<Protected roles={mentor}><MentorAvailabilityPage /></Protected>} />
          <Route path="/mentor/students" element={<Protected roles={mentor}><MentorStudentsPage /></Protected>} />

          {/* Administrators */}
          <Route path="/admin/content" element={<Protected roles={admin}><AdminContentPage /></Protected>} />
          <Route path="/admin/jobs" element={<Navigate to="/admin/content" replace />} />
          <Route path="/admin/users" element={<Protected roles={admin}><AdminUsersPage /></Protected>} />
          <Route path="/admin/analytics" element={<Protected roles={admin}><AdminAnalyticsPage /></Protected>} />

          <Route path="*" element={<p className="page-status">Page not found.</p>} />
        </Routes>
      </main>
    </>
  );
}
