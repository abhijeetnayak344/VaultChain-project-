import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteServer, listServers } from "../../api/servers";
import { useAuth } from "../../context/AuthContext";

const STATUS_TONE = {
  online: "text-emerald-300",
  offline: "text-rose-300",
  maintenance: "text-amber-300",
};

export default function ServerListPage() {
  const { hasPermission } = useAuth();
  const [servers, setServers] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [location, setLocation] = useState("");
  const [operatingSystem, setOperatingSystem] = useState("");
  const [error, setError] = useState("");
  const [locations, setLocations] = useState([]);
  const [operatingSystems, setOperatingSystems] = useState([]);

  async function load(params = {}) {
    try {
      const { data } = await listServers(params);
      const rows = data.results || data;
      setServers(rows);
      const uniqueLocations = [...new Set(rows.map((row) => row.location).filter(Boolean))].sort();
      const uniqueOs = [...new Set(rows.map((row) => row.operating_system).filter(Boolean))].sort();
      if (!params.search && !params.status && !params.location && !params.operating_system) {
        setLocations(uniqueLocations);
        setOperatingSystems(uniqueOs);
      }
    } catch {
      setError("Unable to load servers.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  function onFilter(event) {
    event.preventDefault();
    load({
      search: search || undefined,
      status: status || undefined,
      location: location || undefined,
      operating_system: operatingSystem || undefined,
    });
  }

  async function onDelete(server) {
    if (!window.confirm(`Delete ${server.name} (${server.hostname})? This cannot be undone.`)) {
      return;
    }
    try {
      await deleteServer(server.server_id);
      await load({
        search: search || undefined,
        status: status || undefined,
        location: location || undefined,
        operating_system: operatingSystem || undefined,
      });
    } catch {
      setError("Delete failed. You may not have permission.");
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-400">{servers.length} servers</p>
        {hasPermission("server:create") ? (
          <Link to="/servers/new" className="sd-btn">
            Add server
          </Link>
        ) : null}
      </div>

      <form onSubmit={onFilter} className="sd-card grid gap-3 md:grid-cols-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search ID, name, hostname, IP, location"
          className="sd-input md:col-span-2"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="sd-input">
          <option value="">All statuses</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="maintenance">Maintenance</option>
        </select>
        <select value={location} onChange={(e) => setLocation(e.target.value)} className="sd-input">
          <option value="">All locations</option>
          {locations.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select
          value={operatingSystem}
          onChange={(e) => setOperatingSystem(e.target.value)}
          className="sd-input md:col-span-2"
        >
          <option value="">All operating systems</option>
          {operatingSystems.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <button type="submit" className="sd-btn">
          Search / filter
        </button>
        <button
          type="button"
          className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300"
          onClick={() => {
            setSearch("");
            setStatus("");
            setLocation("");
            setOperatingSystem("");
            load();
          }}
        >
          Clear
        </button>
      </form>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="sd-card overflow-x-auto p-0">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Server ID</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Hostname</th>
              <th className="px-4 py-3">IP</th>
              <th className="px-4 py-3">OS</th>
              <th className="px-4 py-3">CPU</th>
              <th className="px-4 py-3">RAM</th>
              <th className="px-4 py-3">Storage</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {servers.map((server) => (
              <tr key={server.server_id} className="border-t border-white/10">
                <td className="px-4 py-3 font-medium text-cyan-300">{server.code}</td>
                <td className="px-4 py-3">{server.name}</td>
                <td className="px-4 py-3">{server.hostname}</td>
                <td className="px-4 py-3">{server.ip_address}</td>
                <td className="px-4 py-3">{server.operating_system}</td>
                <td className="px-4 py-3">{server.cpu_percent}%</td>
                <td className="px-4 py-3">{server.ram_percent}%</td>
                <td className="px-4 py-3">{server.storage_percent}%</td>
                <td className={`px-4 py-3 capitalize ${STATUS_TONE[server.status] || ""}`}>{server.status}</td>
                <td className="px-4 py-3">{server.location}</td>
                <td className="space-x-3 px-4 py-3 whitespace-nowrap">
                  <Link to={`/servers/${server.server_id}`} className="text-cyan-400 hover:underline">
                    View
                  </Link>
                  {hasPermission("server:update") ? (
                    <Link to={`/servers/${server.server_id}/edit`} className="text-slate-300 hover:underline">
                      Edit
                    </Link>
                  ) : null}
                  {hasPermission("server:delete") ? (
                    <button type="button" onClick={() => onDelete(server)} className="text-rose-400">
                      Delete
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {servers.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No servers match the current filters.</p> : null}
      </div>
    </section>
  );
}
