import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listFirewalls } from "../../api/firewalls";
import { useAuth } from "../../context/AuthContext";

const STATUS_TONE = {
  active: "text-emerald-300",
  inactive: "text-slate-400",
};

export default function FirewallDashboardPage() {
  const { hasPermission } = useAuth();
  const [firewalls, setFirewalls] = useState([]);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [vendor, setVendor] = useState("");
  const [vendors, setVendors] = useState([]);
  const [error, setError] = useState("");

  async function load(params = {}) {
    try {
      const { data } = await listFirewalls(params);
      const rows = data.results || data;
      setFirewalls(rows);
      if (!params.search && !params.status && !params.vendor) {
        setVendors([...new Set(rows.map((row) => row.vendor).filter(Boolean))].sort());
      }
    } catch {
      setError("Unable to load firewalls.");
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
      vendor: vendor || undefined,
    });
  }

  const pendingTotal = firewalls.reduce((sum, row) => sum + (row.pending_request_count || 0), 0);
  const activeCount = firewalls.filter((row) => row.status === "active").length;

  return (
    <section className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <article className="sd-card">
          <p className="text-xs uppercase tracking-wider text-slate-500">Firewalls</p>
          <p className="mt-2 text-2xl font-semibold text-white">{firewalls.length}</p>
        </article>
        <article className="sd-card">
          <p className="text-xs uppercase tracking-wider text-slate-500">Active</p>
          <p className="mt-2 text-2xl font-semibold text-emerald-300">{activeCount}</p>
        </article>
        <article className="sd-card">
          <p className="text-xs uppercase tracking-wider text-slate-500">Pending rule changes</p>
          <p className="mt-2 text-2xl font-semibold text-amber-300">{pendingTotal}</p>
        </article>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        {hasPermission("firewall:approve") || hasPermission("firewall:request") ? (
          <Link to="/firewall-approvals" className="text-sm text-cyan-400 hover:underline">
            Open approval requests
          </Link>
        ) : (
          <span />
        )}
        {hasPermission("firewall:create") ? (
          <Link to="/firewalls/new" className="sd-btn">
            Add firewall
          </Link>
        ) : null}
      </div>

      <form onSubmit={onFilter} className="sd-card grid gap-3 md:grid-cols-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search name or vendor"
          className="sd-input md:col-span-2"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="sd-input">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <select value={vendor} onChange={(e) => setVendor(e.target.value)} className="sd-input">
          <option value="">All vendors</option>
          {vendors.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <button type="submit" className="sd-btn md:col-span-2">
          Filter
        </button>
        <button
          type="button"
          className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300 md:col-span-2"
          onClick={() => {
            setSearch("");
            setStatus("");
            setVendor("");
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
              <th className="px-4 py-3">Firewall name</th>
              <th className="px-4 py-3">Vendor</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Rules</th>
              <th className="px-4 py-3">Pending changes</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {firewalls.map((fw) => (
              <tr key={fw.firewall_id} className="border-t border-white/10">
                <td className="px-4 py-3 font-medium text-cyan-300">{fw.name}</td>
                <td className="px-4 py-3">{fw.vendor}</td>
                <td className={`px-4 py-3 capitalize ${STATUS_TONE[fw.status] || ""}`}>{fw.status}</td>
                <td className="px-4 py-3">{fw.rule_count}</td>
                <td className="px-4 py-3">{fw.pending_request_count}</td>
                <td className="space-x-3 px-4 py-3 whitespace-nowrap">
                  <Link to={`/firewalls/${fw.firewall_id}`} className="text-cyan-400 hover:underline">
                    Rules
                  </Link>
                  {hasPermission("firewall:update") ? (
                    <Link to={`/firewalls/${fw.firewall_id}/edit`} className="text-slate-300 hover:underline">
                      Edit
                    </Link>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {firewalls.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No firewalls match the current filters.</p> : null}
      </div>
    </section>
  );
}
