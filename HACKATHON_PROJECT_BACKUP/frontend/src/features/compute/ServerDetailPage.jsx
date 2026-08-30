import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { deleteServer, getServer } from "../../api/servers";
import { useAuth } from "../../context/AuthContext";

const STATUS_TONE = {
  online: "text-emerald-300",
  offline: "text-rose-300",
  maintenance: "text-amber-300",
};

function Row({ label, value, className = "" }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className={`mt-1 text-sm text-slate-100 ${className}`}>{value ?? "—"}</dd>
    </div>
  );
}

export default function ServerDetailPage() {
  const { id } = useParams();
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [server, setServer] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getServer(id)
      .then(({ data }) => setServer(data))
      .catch(() => setError("Server not found or you do not have access."));
  }, [id]);

  async function onDelete() {
    if (!window.confirm(`Delete ${server.name}? This cannot be undone.`)) return;
    try {
      await deleteServer(server.server_id);
      navigate("/servers");
    } catch {
      setError("Delete failed.");
    }
  }

  if (error && !server) {
    return <p className="text-sm text-rose-400">{error}</p>;
  }
  if (!server) {
    return <p className="text-sm text-slate-400">Loading server…</p>;
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-cyan-400">{server.code}</p>
          <h2 className="text-xl font-semibold text-white">{server.name}</h2>
        </div>
        <div className="flex gap-3">
          <Link to="/servers" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Back to list
          </Link>
          {hasPermission("server:update") ? (
            <Link to={`/servers/${server.server_id}/edit`} className="sd-btn">
              Edit
            </Link>
          ) : null}
          {hasPermission("server:delete") ? (
            <button type="button" onClick={onDelete} className="rounded-lg border border-rose-500/40 px-4 py-2 text-sm text-rose-300">
              Delete
            </button>
          ) : null}
        </div>
      </div>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <dl className="sd-card grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Row label="Server ID" value={server.code} className="text-cyan-300" />
        <Row label="UUID" value={server.server_id} className="break-all text-slate-400" />
        <Row label="Name" value={server.name} />
        <Row label="Hostname" value={server.hostname} />
        <Row label="IP address" value={server.ip_address} />
        <Row label="Operating system" value={server.operating_system} />
        <Row label="CPU usage" value={`${server.cpu_percent}%`} />
        <Row label="RAM usage" value={`${server.ram_percent}%`} />
        <Row label="Storage usage" value={`${server.storage_percent}%`} />
        <Row label="Status" value={server.status} className={`capitalize ${STATUS_TONE[server.status] || ""}`} />
        <Row label="Location" value={server.location} />
        <Row label="Environment" value={server.environment} />
        <Row label="Last seen" value={server.last_seen_at ? new Date(server.last_seen_at).toLocaleString("en-IN") : "—"} />
        <Row label="Created" value={new Date(server.created_at).toLocaleString("en-IN")} />
        <Row label="Updated" value={new Date(server.updated_at).toLocaleString("en-IN")} />
      </dl>
    </section>
  );
}
