import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listBlockchainTransactions } from "../../api/blockchain";
import { VerificationBadge } from "./status";

function pageFromUrl(url) {
  if (!url) return null;
  try {
    return new URL(url, window.location.origin).searchParams.get("page") || "1";
  } catch {
    return null;
  }
}

export default function TransactionHistoryPage() {
  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);
  const [search, setSearch] = useState("");
  const [chainStatus, setChainStatus] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("");
  const [error, setError] = useState("");

  async function load(page = "1") {
    try {
      const { data } = await listBlockchainTransactions({
        search: search || undefined,
        chain_status: chainStatus || undefined,
        verification_status: verificationStatus || undefined,
        page,
      });
      setRows(data.results || []);
      setCount(data.count ?? 0);
      setNextPage(pageFromUrl(data.next));
      setPrevPage(pageFromUrl(data.previous));
    } catch {
      setError("Unable to load transaction history.");
    }
  }

  useEffect(() => {
    load("1");
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs uppercase tracking-wider text-cyan-400">Fabric</p>
        <h2 className="text-xl font-semibold text-white">Transaction history</h2>
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          load("1");
        }}
        className="sd-card grid gap-3 md:grid-cols-4"
      >
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search tx id, user, action" className="sd-input md:col-span-2" />
        <select value={chainStatus} onChange={(e) => setChainStatus(e.target.value)} className="sd-input">
          <option value="">All chain statuses</option>
          <option value="anchored">Anchored</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </select>
        <select value={verificationStatus} onChange={(e) => setVerificationStatus(e.target.value)} className="sd-input">
          <option value="">All verification</option>
          <option value="verified">VERIFIED</option>
          <option value="alert">SECURITY ALERT</option>
          <option value="unverified">UNVERIFIED</option>
        </select>
        <button type="submit" className="sd-btn">
          Filter
        </button>
      </form>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="sd-card overflow-x-auto p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-200">Anchored hashes</h3>
          <p className="text-xs text-slate-500">{count} records</p>
        </div>
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">User</th>
              <th className="px-4 py-3">Tx ID</th>
              <th className="px-4 py-3">Chain</th>
              <th className="px-4 py-3">Integrity</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.log_id} className="border-t border-white/10">
                <td className="px-4 py-3 whitespace-nowrap text-slate-300">{new Date(row.timestamp).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-cyan-300">{row.action}</td>
                <td className="px-4 py-3">{row.user_email || "—"}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{row.chain_tx_id || "—"}</td>
                <td className="px-4 py-3 text-slate-400">{row.chain_status}</td>
                <td className="px-4 py-3">
                  <VerificationBadge status={row.verification_status} />
                </td>
                <td className="px-4 py-3">
                  <Link to={`/blockchain/verify/${row.log_id}`} className="text-cyan-400 hover:underline">
                    Verify
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No blockchain transactions match the filters.</p> : null}
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
