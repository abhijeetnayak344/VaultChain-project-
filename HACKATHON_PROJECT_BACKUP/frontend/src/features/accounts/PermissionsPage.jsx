import { useEffect, useState } from "react";
import { createPermission, listPermissions } from "../../api/rbac";
import { useAuth } from "../../context/AuthContext";

export default function PermissionsPage() {
  const { hasPermission } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [resource, setResource] = useState("");
  const [action, setAction] = useState("");
  const [description, setDescription] = useState("");

  async function load() {
    try {
      const { data } = await listPermissions();
      setItems(data.results || data);
    } catch {
      setError("Unable to load permissions.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(event) {
    event.preventDefault();
    try {
      await createPermission({ resource, action, description });
      setResource("");
      setAction("");
      setDescription("");
      await load();
    } catch {
      setError("Could not create permission.");
    }
  }

  return (
    <section className="space-y-6">
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      {hasPermission("permission:create") ? (
        <form onSubmit={onCreate} className="sd-card grid gap-3 md:grid-cols-3">
          <input
            required
            placeholder="resource (e.g. server)"
            value={resource}
            onChange={(e) => setResource(e.target.value)}
            className="sd-input"
          />
          <input
            required
            placeholder="action (e.g. read)"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="sd-input"
          />
          <input
            placeholder="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="sd-input"
          />
          <button type="submit" className="sd-btn md:col-span-3">
            Create permission
          </button>
        </form>
      ) : null}

      <ul className="sd-card divide-y divide-white/10 p-0">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <span className="font-medium text-white">{item.codename}</span>
            <span className="text-slate-500">{item.description}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
