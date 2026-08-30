import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAuditChainHistory, getAuditLog, verifyAuditLog } from "../../api/audit";
import { VerificationBadge } from "../blockchain/status";
import { actionLabel, resourceLabel } from "./labels";

function Row({ label, value, className = "" }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className={`mt-1 text-sm text-slate-100 ${className}`}>{value ?? "—"}</dd>
    </div>
  );
}

export default function AuditDetailPage() {
  const { id } = useParams();
  const [log, setLog] = useState(null);
  const [error, setError] = useState("");
  const [verify, setVerify] = useState(null);
  const [history, setHistory] = useState(null);
  const [busy, setBusy] = useState("");

  useEffect(() => {
    getAuditLog(id)
      .then(({ data }) => setLog(data))
      .catch(() => setError("Audit event not found or you do not have access."));
  }, [id]);

  if (error && !log) return <p className="text-sm text-rose-400">{error}</p>;
  if (!log) return <p className="text-sm text-slate-400">Loading audit event…</p>;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-cyan-400">{actionLabel(log.action)}</p>
          <h2 className="text-xl font-semibold text-white">Audit event</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={`/blockchain/verify/${log.log_id}`} className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Integrity check
          </Link>
          <Link to="/audit" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Back to audit log
          </Link>
        </div>
      </div>

      <dl className="sd-card grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Row label="User" value={log.user_email || "—"} />
        <Row label="User ID" value={log.user || "—"} className="break-all text-slate-400" />
        <Row label="Action" value={actionLabel(log.action)} className="text-cyan-300" />
        <Row label="Timestamp" value={new Date(log.timestamp).toLocaleString("en-IN")} />
        <Row label="IP address" value={log.ip_address || "—"} />
        <Row label="Resource type" value={resourceLabel(log.resource_type)} />
        <Row label="Resource ID" value={log.resource_id || "—"} className="break-all font-mono text-xs" />
        <Row label="Integrity hash" value={log.integrity_hash || "—"} className="break-all font-mono text-xs" />
        <Row label="Chain status" value={log.chain_status || "skipped"} />
        <Row label="Chain Tx ID" value={log.chain_tx_id || "—"} className="break-all font-mono text-xs" />
        <div>
          <dt className="text-xs uppercase tracking-wider text-slate-500">Verification</dt>
          <dd className="mt-1">
            <VerificationBadge status={verify?.status || log.verification_status} />
          </dd>
        </div>
      </dl>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="sd-btn"
          disabled={busy === "verify"}
          onClick={async () => {
            setBusy("verify");
            try {
              const { data } = await verifyAuditLog(id);
              setVerify(data);
            } catch {
              setError("Integrity verification failed.");
            } finally {
              setBusy("");
            }
          }}
        >
          {busy === "verify" ? "Verifying…" : "Verify integrity"}
        </button>
        <button
          type="button"
          className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300"
          disabled={busy === "history"}
          onClick={async () => {
            setBusy("history");
            try {
              const { data } = await getAuditChainHistory(id);
              setHistory(data);
            } catch {
              setError("Unable to load chain history.");
            } finally {
              setBusy("");
            }
          }}
        >
          {busy === "history" ? "Loading…" : "On-chain history"}
        </button>
      </div>

      {verify ? (
        <article className="sd-card">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Integrity check</h3>
          <p className={`text-sm ${verify.matches ? "text-emerald-300" : verify.status === "alert" ? "text-rose-300" : "text-amber-300"}`}>
            {verify.label || (verify.matches ? "VERIFIED" : verify.reason || "Hash does not match or is not anchored.")}
          </p>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-navy-950/80 p-4 text-xs text-slate-300">
            {JSON.stringify(verify, null, 2)}
          </pre>
        </article>
      ) : null}

      {history ? (
        <article className="sd-card">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Ledger history</h3>
          <pre className="overflow-x-auto rounded-lg bg-navy-950/80 p-4 text-xs text-slate-300">
            {JSON.stringify(history, null, 2)}
          </pre>
        </article>
      ) : null}

      <article className="sd-card">
        <h3 className="mb-3 text-sm font-semibold text-slate-200">Event details</h3>
        <pre className="overflow-x-auto rounded-lg bg-navy-950/80 p-4 text-xs text-slate-300">
          {JSON.stringify(log.details || {}, null, 2)}
        </pre>
      </article>
    </section>
  );
}
