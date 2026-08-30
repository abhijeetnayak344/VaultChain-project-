import { useEffect, useState } from "react";
import { assignUserRoles, createUser, disableUser, listUsers } from "../../api/users";
import { listRoles } from "../../api/rbac";
import { useAuth } from "../../context/AuthContext";

export default function UsersPage() {
  const { hasPermission } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role_ids: [] });

  async function load() {
    try {
      const { data: userPage } = await listUsers();
      setUsers(userPage.results || userPage);
    } catch {
      setError("Unable to load users.");
      return;
    }
    try {
      const { data: rolePage } = await listRoles();
      setRoles(rolePage.results || rolePage);
    } catch {
      setRoles([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(event) {
    event.preventDefault();
    setError("");
    try {
      await createUser(form);
      setForm({ email: "", full_name: "", password: "", role_ids: [] });
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Create failed.");
    }
  }

  async function onDisable(id) {
    setError("");
    try {
      await disableUser(id);
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Disable failed.");
    }
  }

  async function onAssign(id, roleId) {
    const next = roleId ? [Number(roleId)] : [];
    try {
      await assignUserRoles(id, next);
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Role assignment failed.");
    }
  }

  return (
    <section className="space-y-6">
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      {hasPermission("user:create") ? (
        <form onSubmit={onCreate} className="sd-card grid gap-3 md:grid-cols-2">
          <input
            required
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="sd-input"
          />
          <input
            required
            placeholder="Full name"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            className="sd-input"
          />
          <input
            required
            type="password"
            minLength={12}
            placeholder="Temporary password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="sd-input"
          />
          <button type="submit" className="sd-btn md:col-span-2">
            Create user
          </button>
        </form>
      ) : null}

      <div className="sd-card overflow-x-auto p-0">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Roles</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((item) => (
              <tr key={item.id} className="border-t border-white/10">
                <td className="px-4 py-3">{item.email}</td>
                <td className="px-4 py-3">{item.full_name}</td>
                <td className="px-4 py-3">{item.roles?.map((role) => role.name).join(", ") || "—"}</td>
                <td className="px-4 py-3">{item.is_active ? "Active" : "Disabled"}</td>
                <td className="space-x-2 px-4 py-3">
                  {hasPermission("role:assign") ? (
                    <select
                      defaultValue=""
                      onChange={(e) => onAssign(item.id, e.target.value)}
                      className="rounded-md border border-white/10 bg-navy-950 px-2 py-1"
                    >
                      <option value="">Assign role…</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name}
                        </option>
                      ))}
                    </select>
                  ) : null}
                  {hasPermission("user:disable") && item.is_active ? (
                    <button type="button" onClick={() => onDisable(item.id)} className="text-rose-400">
                      Disable
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
