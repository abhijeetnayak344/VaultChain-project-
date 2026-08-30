import { useEffect, useState } from "react";
import { getHealth } from "../api/health";
import { useAuth } from "../context/AuthContext";

export default function HomePage() {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setError("API is not reachable yet. Start the backend / Compose stack."));
  }, []);

  const roleNames = user?.roles?.map((role) => role.name).join(", ") || "No role assigned";

  return (
    <section className="space-y-8">
      <div>
        <p className="text-sm font-medium uppercase tracking-wider text-saffron-500">
          Phase 2 — identity &amp; RBAC
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-navy-900">Welcome, {user?.full_name}</h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Signed in as {user?.email}. Effective roles: {roleNames}. Navigation is filtered by
          your permissions.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-navy-800">API health</h2>
        {error ? (
          <p className="mt-3 text-sm text-red-600">{error}</p>
        ) : health ? (
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            {Object.entries(health).map(([key, value]) => (
              <div key={key}>
                <dt className="text-slate-500">{key}</dt>
                <dd className="font-medium text-navy-900">{String(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-3 text-sm text-slate-500">Checking /api/v1/health/ …</p>
        )}
      </div>
    </section>
  );
}
