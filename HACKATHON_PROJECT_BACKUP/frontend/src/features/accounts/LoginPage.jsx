import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

function errorMessage(err) {
  return err.response?.data?.error?.message || err.response?.data?.detail || "Sign-in failed.";
}

export default function LoginPage() {
  const { login, isAuthenticated, ready } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  if (ready && isAuthenticated) {
    const to = location.state?.from?.pathname || "/";
    return <Navigate to={to} replace />;
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      await login({ email, password });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-white">Sign in</h1>
      <p className="mt-2 text-sm text-slate-400">AICTE SecureDC — authorized personnel only.</p>
      <form onSubmit={onSubmit} className="sd-card mt-6 space-y-4">
        {error ? <p className="text-sm text-rose-400">{error}</p> : null}
        <label className="sd-label">
          Email
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="sd-input"
          />
        </label>
        <label className="sd-label">
          Password
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="sd-input"
          />
        </label>
        <button type="submit" disabled={pending} className="sd-btn w-full">
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-400">
        No account?{" "}
        <Link to="/register" className="text-cyan-400 hover:underline">
          Register
        </Link>
      </p>
    </div>
  );
}
