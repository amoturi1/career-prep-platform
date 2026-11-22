// PB-01 create account, PB-02 sign in, PB-03 validation messages.
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { homePathFor, useAuth } from "../auth.jsx";
import Field from "../components/Field.jsx";
import Alert from "../components/Alert.jsx";

function validate(mode, form) {
  const errors = {};
  if (mode === "register" && !form.full_name.trim()) errors.full_name = "This field is required.";
  if (!form.email.trim()) errors.email = "This field is required.";
  else if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) errors.email = "Enter a valid email address.";
  if (!form.password) errors.password = "This field is required.";
  else if (mode === "register") {
    if (form.password.length < 8) errors.password = "Password must be at least 8 characters.";
    else if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password))
      errors.password = "Password must contain at least one letter and one number.";
  }
  if (mode === "register" && form.password && form.confirm !== form.password)
    errors.confirm = "Passwords do not match.";
  return errors;
}

export default function AuthPage({ mode }) {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "register";

  // Already signed in (and not mid-submit): skip this page.
  if (user && !busy) return <Navigate to={homePathFor(user)} replace />;

  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    const found = validate(mode, form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setBusy(true);
    try {
      const signedIn = isRegister
        ? await register(form.full_name.trim(), form.email.trim(), form.password)
        : await login(form.email.trim(), form.password);
      const target = isRegister ? "/profile" : location.state?.from ?? homePathFor(signedIn);
      navigate(target, { replace: true });
    } catch (err) {
      setErrors(err.fieldErrors ?? {});
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <section className="card auth-card" aria-labelledby="auth-title">
        <p className="eyebrow">AI Career &amp; Internship Prep Platform</p>
        <h1 id="auth-title">{isRegister ? "Create your account" : "Welcome back"}</h1>
        <p className="muted">
          {isRegister
            ? "Track applications, build your profile, and discover opportunities."
            : "Sign in to continue your career preparation."}
        </p>

        <Alert>{message}</Alert>

        <form onSubmit={handleSubmit} noValidate>
          {isRegister && (
            <Field id="full_name" label="Full name" value={form.full_name} onChange={update}
              error={errors.full_name} autoComplete="name" required />
          )}
          <Field id="email" label="Email" type="email" value={form.email} onChange={update}
            error={errors.email} autoComplete="email" required />
          <Field id="password" label="Password" type="password" value={form.password} onChange={update}
            error={errors.password} autoComplete={isRegister ? "new-password" : "current-password"}
            hint={isRegister ? "At least 8 characters, with a letter and a number." : undefined} required />
          {isRegister && (
            <Field id="confirm" label="Confirm password" type="password" value={form.confirm} onChange={update}
              error={errors.confirm} autoComplete="new-password" required />
          )}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
            {busy ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? (
            <>Already have an account? <Link to="/login">Sign in</Link></>
          ) : (
            <>Don&apos;t have an account? <Link to="/register">Create account</Link></>
          )}
        </p>
      </section>
    </div>
  );
}
