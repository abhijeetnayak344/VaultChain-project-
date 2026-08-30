import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createFirewall, updateFirewall } from "../../api/firewalls";

const empty = { name: "", vendor: "", status: "active" };

export default function FirewallForm({ initial = empty, firewallId }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ ...empty, ...initial });
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const editing = Boolean(firewallId);

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setPending(true);
    try {
      const { data } = editing
        ? await updateFirewall(firewallId, form)
        : await createFirewall(form);
      navigate(`/firewalls/${data.firewall_id}`);
    } catch (err) {
      setError(err.response?.data?.error?.message || "Could not save firewall.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="sd-card grid max-w-xl gap-4">
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}
      <label className="sd-label">
        Firewall name
        <input required value={form.name} onChange={(e) => set("name", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        Vendor
        <input required value={form.vendor} onChange={(e) => set("vendor", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        Status
        <select value={form.status} onChange={(e) => set("status", e.target.value)} className="sd-input">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </label>
      <div className="flex gap-3">
        <button type="submit" disabled={pending} className="sd-btn">
          {pending ? "Saving…" : editing ? "Save firewall" : "Add firewall"}
        </button>
        <Link to="/firewalls" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
          Cancel
        </Link>
      </div>
    </form>
  );
}
