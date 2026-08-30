import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getBlockchainSummary, listIntegrityAlerts, listBlockchainTransactions } from "../../api/blockchain";
import StatCard from "../monitoring/StatCard";
import { VerificationBadge } from "./status";

export default function BlockchainDashboardPage() {
  const [summary, setSummary] = useState(null);
  const [tx, setTx] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getBlockchainSummary(), listBlockchainTransactions({ page_size: 8 }), listIntegrityAlerts({ status: "open", page_size: 5 })])
      .then(([summaryRes, txRes, alertRes]) => {
        setSummary(summaryRes.data);
        setTx(txRes.data.results || []);
        setAlerts(alertRes.data.results || []);
      })
      .catch(() => setError("Unable to load blockchain verification data."));
  }, []);

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-cyan-400">Hyperledger Fabric</p>
          <h2 className="text-xl font-semibold text-white">Blockchain audit dashboard</h2>
          <p className="mt-1 text-sm text-slate-400">
            Critical audit hashes on chain. Integrity is current data hash versus blockchain hash.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/blockchain/verify" className="sd-btn">
            Integrity check
          </Link>
          <Link to="/blockchain/transactions" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Transactions
          </Link>
          <Link to="/blockchain/alerts" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Security alerts
          </Link>
        </div>
      </div>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Hashed events" value={summary.hashed} hint={`${summary.critical_events} critical actions`} tone="cyan" />
          <StatCard label="Anchored on Fabric" value={summary.anchored} hint={summary.fabric_enabled ? "Network enabled" : "Fabric disabled"} tone="violet" />
          <StatCard label="VERIFIED" value={summary.verified} hint={`${summary.pending} pending · ${summary.failed} failed`} tone="emerald" />
          <StatCard label="Open security alerts" value={summary.alerts_open} hint={`${summary.alerts_total} total integrity alerts`} tone="rose" />
        </div>
      ) : (
        <p className="text-sm text-slate-400">Loading blockchain summary…</p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="sd-card overflow-x-auto p-0">
          <div className="flex items-center justify-between px-5 py-4">
            <h3 className="text-sm font-semibold text-slate-200">Recent transactions</h3>
            <Link to="/blockchain/transactions" className="text-xs text-cyan-400 hover:underline">
              View all
            </Link>
          </div>
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/5 text-slate-400">
              <tr>
                <th className="px-5 py-2">Time</th>
                <th className="px-5 py-2">Tx ID</th>
                <th className="px-5 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {tx.map((row) => (
                <tr key={row.log_id} className="border-t border-white/10">
                  <td className="px-5 py-2 whitespace-nowrap text-slate-300">
                    {new Date(row.timestamp).toLocaleString("en-IN")}
                  </td>
                  <td className="px-5 py-2 font-mono text-xs text-slate-400">{row.chain_tx_id || "—"}</td>
                  <td className="px-5 py-2">
                    <VerificationBadge status={row.verification_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {tx.length === 0 ? <p className="px-5 py-6 text-sm text-slate-500">No hashed audit events yet.</p> : null}
        </article>

        <article className="sd-card p-0">
          <div className="flex items-center justify-between px-5 py-4">
            <h3 className="text-sm font-semibold text-slate-200">Open integrity alerts</h3>
            <Link to="/blockchain/alerts" className="text-xs text-cyan-400 hover:underline">
              Alert dashboard
            </Link>
          </div>
          <ul className="divide-y divide-white/10">
            {alerts.map((row) => (
              <li key={row.id} className="px-5 py-3">
                <p className="text-sm text-rose-300">{row.action}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">{row.reason}</p>
              </li>
            ))}
          </ul>
          {alerts.length === 0 ? (
            <p className="px-5 py-6 text-sm text-slate-500">No open SECURITY ALERT rows.</p>
          ) : null}
        </article>
      </div>
    </section>
  );
}
