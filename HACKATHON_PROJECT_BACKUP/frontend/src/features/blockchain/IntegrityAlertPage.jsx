import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { acknowledgeIntegrityAlert, listIntegrityAlerts, resolveIntegrityAlert } from "../../api/blockchain";
import PermissionGate from "../../components/PermissionGate";
import { VerificationBadge } from "./status";

function pageFromUrl(url) {
  if (!url) return null;
  try {
    return new URL(url, window.location.origin).searchParams.get("page") || "1";
  } catch {
    return null;
  }
}

export default function IntegrityAlertPage() {
  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("open");
  const [error, setError] = useState("");
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);

  async function load(page = "1") {
    try {
      const { data } = await listIntegrityAlerts({ status: statusFilter || undefined, page });
      setRows(data.results || []);
      setCount(data.count ?? 0);
      setNextPage(pageFromUrl(data.next));
      setPrevPage(pageFromUrl(data.previous));
    } catch {
      setError("Unable to load integrity alerts.");
    }
  }

  useEffect(() => {
    load("1");
  }, [statusFilter]);

  async function onAck(id) {
    try {
      await acknowledgeIntegrityAlert(id);
      load("1");
    } catch {
      setError("Acknowledge failed. Security Admin permission required.");
    }
  }

  async function onResolve(id) {
    try {
      await resolveIntegrityAlert(id);
      load("1");
    } catch {
      setError("Resolve failed. Security Admin permission required.");
    }
  }

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-wider text-rose-300">Integrity</p>
        <h2 className="text-xl font-semibold text-white">Security alert dashboard</h2>
        <p className="mt-1 text-sm text-slate-400">
          Raised when the current audit data hash does not match the hash stored on Hyperledger Fabric.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {["open", "acknowledged", "resolved", ""].map((value) => (
          <button
            key={value || "all"}
            type="button"
            className={`rounded-lg border px-3 py-1.5 text-sm ${
              statusFilter === value ? "border-cyan-400/50 text-cyan-300" : "border-white/10 text-slate-300"
            }`}
            onClick={() => setStatusFilter(value)}
          >
            {value || "all"}
          </button>
        ))}
      </div>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="sd-card overflow-x-auto p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-200">Integrity alerts</h3>
          <p className="text-xs text-slate-500">{count} alerts</p>
        </div>
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Reason</th>
              <th className="px-4 py-3">Local hash</th>
              <th className="px-4 py-3">Chain hash</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-white/10">
                <td className="px-4 py-3 whitespace-nowrap text-slate-300">{new Date(row.timestamp).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-cyan-300">{row.action}</td>
                <td className="px-4 py-3 text-rose-300">{row.reason}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{(row.local_hash || "").slice(0, 12)}…</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">{(row.chain_hash || "—").slice(0, 12)}</td>
                <td className="px-4 py-3">
                  <VerificationBadge status={row.status === "open" ? "alert" : "unverified"} />
                  <span className="ml-2 text-xs text-slate-500">{row.status}</span>
                </td>
                <td className="px-4 py-3 space-x-3">
                  <Link to={`/blockchain/verify/${row.log_id}`} className="text-cyan-400 hover:underline">
                    Check
                  </Link>
                  <PermissionGate permission="audit:alert">
                    {row.status === "open" ? (
                      <button type="button" className="text-amber-300 hover:underline" onClick={() => onAck(row.id)}>
                        Ack
                      </button>
                    ) : null}
                    {row.status !== "resolved" ? (
                      <button type="button" className="text-emerald-300 hover:underline" onClick={() => onResolve(row.id)}>
                        Resolve
                      </button>
                    ) : null}
                  </PermissionGate>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No integrity alerts in this view.</p> : null}
        <div className="flex gap-3 px-4 py-3">
          <button type="button" disabled={!prevPage} className="rounded-lg border border-white/10 px-3 py-1 text-sm text-slate-300 disabled:opacity-40" onClick={() => load(prevPage)}>
            Previous
          </button>
          <button type="button" disabled={!nextPage} className="rounded-lg border border-white/10 px-3 py-1 text-sm text-slate-300 disabled:opacity-40" onClick={() => load(nextPage)}>
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
