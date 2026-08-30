import { useEffect, useState } from "react";
import { createRole, listPermissions, listRoles, updateRole } from "../../api/rbac";
import { useAuth } from "../../context/AuthContext";

export default function RolesPage() {
  const { hasPermission } = useAuth();
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  async function load() {
    try {
      const [{ data: rolePage }, { data: permPage }] = await Promise.all([listRoles(), listPermissions()]);
      setRoles(rolePage.results || rolePage);
      setPermissions(permPage.results || permPage);
    } catch {
      setError("Unable to load roles.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(event) {
    event.preventDefault();
    try {
      await createRole({ name, slug, description: "" });
      setName("");
      setSlug("");
      await load();
    } catch {
      setError("Could not create role.");
    }
  }

  async function togglePermission(role, permissionId) {
    const current = new Set(role.permissions.map((item) => item.id));
    if (current.has(permissionId)) current.delete(permissionId);
    else current.add(permissionId);
    try {
      await updateRole(role.id, { permission_ids: [...current] });
      await load();
    } catch {
      setError("Could not update role permissions.");
    }
  }

  return (
    <section className="space-y-6">
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      {hasPermission("role:create") ? (
        <form onSubmit={onCreate} className="sd-card flex flex-wrap gap-3">
          <input
            required
            placeholder="Role name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="sd-input"
          />
          <input
            required
            placeholder="slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            className="sd-input"
          />
          <button type="submit" className="sd-btn">
            Create role
          </button>
        </form>
      ) : null}

      <div className="space-y-4">
        {roles.map((role) => (
          <article key={role.id} className="sd-card">
            <h2 className="font-semibold text-white">
              {role.name} <span className="text-sm font-normal text-slate-500">{role.slug}</span>
            </h2>
            <p className="mt-1 text-sm text-slate-400">{role.description || "—"}</p>
            {hasPermission("role:update") || hasPermission("permission:update") ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {permissions.map((permission) => {
                  const checked = role.permissions.some((item) => item.id === permission.id);
                  return (
                    <label key={permission.id} className="flex items-center gap-2 rounded-md border border-white/10 px-2 py-1 text-xs">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => togglePermission(role, permission.id)}
                      />
                      {permission.codename}
                    </label>
                  );
                })}
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-300">
                {role.permissions.map((item) => item.codename).join(", ") || "No permissions"}
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
