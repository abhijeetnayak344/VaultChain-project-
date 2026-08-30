import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createServer, updateServer } from "../../api/servers";

const empty = {
  code: "",
  name: "",
  hostname: "",
  ip_address: "",
  operating_system: "",
  location: "",
  environment: "production",
  status: "online",
  cpu_percent: 0,
  ram_percent: 0,
  storage_percent: 0,
};

function fieldError(err, name) {
  const details = err.response?.data?.error?.details;
  if (details && details[name]) {
    return Array.isArray(details[name]) ? details[name][0] : String(details[name]);
  }
  return "";
}

export default function ServerForm({ initial = empty, serverId }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ ...empty, ...initial });
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const editing = Boolean(serverId);

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setPending(true);
    const payload = {
      ...form,
      cpu_percent: Number(form.cpu_percent),
      ram_percent: Number(form.ram_percent),
      storage_percent: Number(form.storage_percent),
    };
    if (!payload.code) {
      delete payload.code;
    }
    try {
      const { data } = editing ? await updateServer(serverId, payload) : await createServer(payload);
      navigate(`/servers/${data.server_id}`);
    } catch (err) {
      setError(err.response?.data?.error?.message || "Could not save server.");
      const hostname = fieldError(err, "hostname");
      const ip = fieldError(err, "ip_address");
      const code = fieldError(err, "code");
      if (hostname || ip || code) {
        setError([hostname, ip, code].filter(Boolean).join(" "));
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="sd-card grid max-w-3xl gap-4 md:grid-cols-2">
      {error ? <p className="text-sm text-rose-400 md:col-span-2">{error}</p> : null}
      <label className="sd-label">
        Server ID
        <input
          value={form.code}
          onChange={(e) => set("code", e.target.value)}
          placeholder="Auto if empty"
          className="sd-input"
        />
      </label>
      <label className="sd-label">
        Name
        <input required value={form.name} onChange={(e) => set("name", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        Hostname
        <input required value={form.hostname} onChange={(e) => set("hostname", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        IP address
        <input required value={form.ip_address} onChange={(e) => set("ip_address", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        Operating system
        <input
          required
          value={form.operating_system}
          onChange={(e) => set("operating_system", e.target.value)}
          className="sd-input"
        />
      </label>
      <label className="sd-label">
        Location
        <input required value={form.location} onChange={(e) => set("location", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        Status
        <select value={form.status} onChange={(e) => set("status", e.target.value)} className="sd-input">
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="maintenance">Maintenance</option>
        </select>
      </label>
      <label className="sd-label">
        Environment
        <input value={form.environment} onChange={(e) => set("environment", e.target.value)} className="sd-input" />
      </label>
      <label className="sd-label">
        CPU usage %
        <input
          type="number"
          min="0"
          max="100"
          step="0.01"
          value={form.cpu_percent}
          onChange={(e) => set("cpu_percent", e.target.value)}
          className="sd-input"
        />
      </label>
      <label className="sd-label">
        RAM usage %
        <input
          type="number"
          min="0"
          max="100"
          step="0.01"
          value={form.ram_percent}
          onChange={(e) => set("ram_percent", e.target.value)}
          className="sd-input"
        />
      </label>
      <label className="sd-label">
        Storage usage %
        <input
          type="number"
          min="0"
          max="100"
          step="0.01"
          value={form.storage_percent}
          onChange={(e) => set("storage_percent", e.target.value)}
          className="sd-input"
        />
      </label>
      <div className="flex gap-3 md:col-span-2">
        <button type="submit" disabled={pending} className="sd-btn">
          {pending ? "Saving…" : editing ? "Save changes" : "Add server"}
        </button>
        <Link to="/servers" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
          Cancel
        </Link>
      </div>
    </form>
  );
}
