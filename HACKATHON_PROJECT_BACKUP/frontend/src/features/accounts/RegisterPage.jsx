import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

function errorMessage(err) {
  const details = err.response?.data?.error?.details;
  if (details && typeof details === "object") {
    const first = Object.values(details).flat()[0];
    if (first) return String(first);
  }
  return err.response?.data?.error?.message || "Registration failed.";
}

export default function RegisterPage() {
  const { register, isAuthenticated, ready } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  if (ready && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      await register({ full_name: fullName, email, password });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-white">Create account</h1>
      <p className="mt-2 text-sm text-slate-400">
        New accounts have no admin role until a Super Admin assigns one.
      </p>
      <form onSubmit={onSubmit} className="sd-card mt-6 space-y-4">
        {error ? <p className="text-sm text-rose-400">{error}</p> : null}
        <label className="sd-label">
          Full name
          <input required value={fullName} onChange={(e) => setFullName(e.target.value)} className="sd-input" />
        </label>
        <label className="sd-label">
          Email
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="sd-input" />
        </label>
        <label className="sd-label">
          Password (min 12 characters)
          <input
            type="password"
            required
            minLength={12}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="sd-input"
          />
        </label>
        <button type="submit" disabled={pending} className="sd-btn w-full">
          {pending ? "Creating…" : "Register"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-400">
        Already registered?{" "}
        <Link to="/login" className="text-cyan-400 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
