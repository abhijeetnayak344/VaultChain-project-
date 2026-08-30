import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAuditSummary, listAuditLogs } from "../../api/audit";
import { VerificationBadge } from "../blockchain/status";
import { AUDIT_ACTIONS, RESOURCE_TYPES, actionLabel, resourceLabel } from "./labels";

function pageFromUrl(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url, window.location.origin);
    return parsed.searchParams.get("page") || "1";
  } catch {
    return null;
  }
}

export default function AuditDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [page, setPage] = useState("1");
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  async function load(nextPage = "1", cleared = false) {
    const params = cleared
      ? { page: nextPage }
      : {
          search: search || undefined,
          action: action || undefined,
          resource_type: resourceType || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          page: nextPage || undefined,
        };
    try {
      const [{ data: summaryData }, { data: logPage }] = await Promise.all([
        getAuditSummary(),
        listAuditLogs(params),
      ]);
      setSummary(summaryData);
      setLogs(logPage.results || logPage);
      setCount(logPage.count ?? (logPage.results || logPage).length);
      setNextPage(pageFromUrl(logPage.next));
      setPrevPage(pageFromUrl(logPage.previous));
      setPage(nextPage);
    } catch {
      setError("Unable to load audit logs.");
    }
  }

  useEffect(() => {
    load("1");
  }, []);

  function onFilter(event) {
    event.preventDefault();
    load("1");
  }

  return (
    <section className="space-y-6">
      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article className="sd-card">
            <p className="text-xs uppercase tracking-wider text-slate-500">Total events</p>
            <p className="mt-2 text-2xl font-semibold text-white">{summary.total}</p>
          </article>
          <article className="sd-card">
            <p className="text-xs uppercase tracking-wider text-slate-500">Last 24 hours</p>
            <p className="mt-2 text-2xl font-semibold text-cyan-300">{summary.last_24h}</p>
          </article>
          <article className="sd-card">
            <p className="text-xs uppercase tracking-wider text-slate-500">Logins (24h)</p>
            <p className="mt-2 text-2xl font-semibold text-emerald-300">{summary.logins_24h}</p>
          </article>
          <article className="sd-card">
            <p className="text-xs uppercase tracking-wider text-slate-500">Approvals (24h)</p>
            <p className="mt-2 text-2xl font-semibold text-amber-300">{summary.approvals_24h}</p>
          </article>
        </div>
      ) : null}

      <form onSubmit={onFilter} className="sd-card grid gap-3 md:grid-cols-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search user, action, resource ID, IP"
          className="sd-input md:col-span-2"
        />
        <select value={action} onChange={(e) => setAction(e.target.value)} className="sd-input">
          <option value="">All actions</option>
          {AUDIT_ACTIONS.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <select value={resourceType} onChange={(e) => setResourceType(e.target.value)} className="sd-input">
          <option value="">All resources</option>
          {RESOURCE_TYPES.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="sd-input" />
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="sd-input" />
        <button type="submit" className="sd-btn">
          Search / filter
        </button>
        <button
          type="button"
          className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300"
          onClick={() => {
            setSearch("");
            setAction("");
            setResourceType("");
            setDateFrom("");
            setDateTo("");
            load("1", true);
          }}
        >
          Clear
        </button>
      </form>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="sd-card overflow-x-auto p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-200">Audit log</h2>
          <p className="text-xs text-slate-500">{count} events</p>
        </div>
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Resource</th>
              <th className="px-4 py-3">Resource ID</th>
              <th className="px-4 py-3">IP address</th>
              <th className="px-4 py-3">Integrity</th>
              <th className="px-4 py-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((row) => (
              <tr key={row.log_id} className="border-t border-white/10">
                <td className="px-4 py-3 whitespace-nowrap text-slate-300">
                  {new Date(row.timestamp).toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-3">{row.user_email || "—"}</td>
                <td className="px-4 py-3 text-cyan-300">{actionLabel(row.action)}</td>
                <td className="px-4 py-3">{resourceLabel(row.resource_type)}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{row.resource_id || "—"}</td>
                <td className="px-4 py-3">{row.ip_address || "—"}</td>
                <td className="px-4 py-3">
                  <VerificationBadge status={row.verification_status} />
                </td>
                <td className="px-4 py-3">
                  <Link to={`/audit/${row.log_id}`} className="text-cyan-400 hover:underline">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No audit events match the current filters.</p> : null}
        <div className="flex gap-3 px-4 py-3">
          <button
            type="button"
            disabled={!prevPage}
            className="rounded-lg border border-white/10 px-3 py-1 text-sm text-slate-300 disabled:opacity-40"
            onClick={() => load(prevPage)}
          >
            Previous
          </button>
          <button
            type="button"
            disabled={!nextPage}
            className="rounded-lg border border-white/10 px-3 py-1 text-sm text-slate-300 disabled:opacity-40"
            onClick={() => load(nextPage)}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
