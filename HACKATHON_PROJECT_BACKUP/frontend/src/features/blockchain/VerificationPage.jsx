import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAuditLog } from "../../api/audit";
import { runIntegrityCheck } from "../../api/blockchain";
import { VerificationBadge } from "./status";

function HashRow({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-1 break-all font-mono text-xs text-slate-200">{value || "—"}</dd>
    </div>
  );
}

export default function VerificationPage() {
  const { id: routeId } = useParams();
  const [logId, setLogId] = useState(routeId || "");
  const [log, setLog] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    if (!routeId) return;
    getAuditLog(routeId)
      .then(({ data }) => {
        setLog(data);
        setLogId(data.log_id);
      })
      .catch(() => setError("Audit event not found."));
  }, [routeId]);

  async function loadLog(event) {
    event.preventDefault();
    setError("");
    setResult(null);
    try {
      const { data } = await getAuditLog(logId.trim());
      setLog(data);
    } catch {
      setError("Audit event not found or you do not have access.");
      setLog(null);
    }
  }

  async function verifyOne() {
    if (!log?.log_id) return;
    setBusy("one");
    setError("");
    try {
      const { data } = await runIntegrityCheck({ log_id: log.log_id });
      setResult(data);
    } catch {
      setError("Integrity check failed. You may need the audit:verify permission.");
    } finally {
      setBusy("");
    }
  }

  async function scanRecent() {
    setBusy("scan");
    setError("");
    try {
      const { data } = await runIntegrityCheck({ limit: 25 });
      setResult({ scan: true, results: data.results || [] });
    } catch {
      setError("Scan failed. You may need the audit:verify permission.");
    } finally {
      setBusy("");
    }
  }

  const status = result?.status || log?.verification_status;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-wider text-cyan-400">Integrity check</p>
        <h2 className="text-xl font-semibold text-white">Current data hash vs blockchain hash</h2>
      </div>

      <form onSubmit={loadLog} className="sd-card flex flex-wrap gap-3">
        <input
          value={logId}
          onChange={(e) => setLogId(e.target.value)}
          placeholder="Audit event UUID"
          className="sd-input max-w-xl flex-1"
        />
        <button type="submit" className="sd-btn">
          Load event
        </button>
        <button type="button" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300" onClick={scanRecent} disabled={busy === "scan"}>
          {busy === "scan" ? "Scanning…" : "Scan last 25"}
        </button>
      </form>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      {log ? (
        <article className="sd-card space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-slate-300">{log.action}</p>
              <p className="text-xs text-slate-500">{log.user_email}</p>
            </div>
            <VerificationBadge status={status} />
          </div>
          <dl className="grid gap-4 sm:grid-cols-2">
            <HashRow label="Current data hash" value={result?.current_hash || log.integrity_hash} />
            <HashRow label="Blockchain hash" value={result?.blockchain_hash} />
            <HashRow label="Stored hash" value={result?.stored_hash || log.integrity_hash} />
            <HashRow label="Chain Tx ID" value={result?.chain_tx_id || log.chain_tx_id} />
          </dl>
          <div className="flex flex-wrap gap-3">
            <button type="button" className="sd-btn" onClick={verifyOne} disabled={busy === "one"}>
              {busy === "one" ? "Checking…" : "Run integrity check"}
            </button>
            <Link to={`/audit/${log.log_id}`} className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
              Open audit event
            </Link>
          </div>
        </article>
      ) : null}

      {result?.label ? (
        <article className={`sd-card ${result.matches ? "border-emerald-400/30" : result.status === "alert" ? "border-rose-400/40" : ""}`}>
          <p className={`text-lg font-semibold ${result.matches ? "text-emerald-300" : result.status === "alert" ? "text-rose-300" : "text-slate-200"}`}>
            {result.label}
          </p>
          <p className="mt-2 text-sm text-slate-400">{result.reason}</p>
        </article>
      ) : null}

      {result?.scan ? (
        <article className="sd-card overflow-x-auto p-0">
          <h3 className="px-5 py-4 text-sm font-semibold text-slate-200">Scan results</h3>
          <table className="min-w-full text-left text-sm">
            <thead className="bg-white/5 text-slate-400">
              <tr>
                <th className="px-5 py-2">Event</th>
                <th className="px-5 py-2">Result</th>
                <th className="px-5 py-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {(result.results || []).map((row) => (
                <tr key={row.log_id} className="border-t border-white/10">
                  <td className="px-5 py-2 font-mono text-xs">
                    <Link to={`/blockchain/verify/${row.log_id}`} className="text-cyan-400 hover:underline">
                      {row.log_id}
                    </Link>
                  </td>
                  <td className="px-5 py-2">
                    <VerificationBadge status={row.status} />
                  </td>
                  <td className="px-5 py-2 text-slate-400">{row.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      ) : null}
    </section>
  );
}
