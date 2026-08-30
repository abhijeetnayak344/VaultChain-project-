import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { approveChangeRequest, listChangeRequests, rejectChangeRequest } from "../../api/firewalls";
import { useAuth } from "../../context/AuthContext";

const STATUS_TONE = {
  pending: "text-amber-300",
  approved: "text-emerald-300",
  rejected: "text-rose-300",
};

export default function ApprovalRequestsPage() {
  const { hasPermission } = useAuth();
  const [requests, setRequests] = useState([]);
  const [status, setStatus] = useState("pending");
  const [error, setError] = useState("");
  const [comments, setComments] = useState({});
  const canApprove = hasPermission("firewall:approve");
  const canReject = hasPermission("firewall:reject");

  async function load(nextStatus = status) {
    try {
      const { data } = await listChangeRequests({ status: nextStatus || undefined });
      setRequests(data.results || data);
    } catch {
      setError("Unable to load approval requests.");
    }
  }

  useEffect(() => {
    load("pending");
  }, []);

  async function decide(row, approved) {
    setError("");
    const review_comment = comments[row.request_id] || "";
    try {
      if (approved) {
        await approveChangeRequest(row.request_id, { review_comment });
      } else {
        await rejectChangeRequest(row.request_id, { review_comment });
      }
      await load(status);
    } catch (err) {
      setError(err.response?.data?.error?.message || "Review failed.");
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-400">
          Network Admin submits rule changes. Security Admin approves or rejects. History is retained on each request.
        </p>
        <Link to="/firewalls" className="text-sm text-cyan-400 hover:underline">
          Firewall dashboard
        </Link>
      </div>

      <form
        className="sd-card flex flex-wrap gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          load(status);
        }}
      >
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="sd-input max-w-xs">
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="">All</option>
        </select>
        <button type="submit" className="sd-btn">
          Filter
        </button>
      </form>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="space-y-4">
        {requests.map((row) => (
          <article key={row.request_id} className="sd-card space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wider text-cyan-400">{row.firewall_name}</p>
                <h2 className="text-base font-semibold capitalize text-white">{row.change_type} rule</h2>
                <p className={`text-sm capitalize ${STATUS_TONE[row.status] || ""}`}>{row.status}</p>
              </div>
              <p className="text-xs text-slate-500">{new Date(row.requested_at).toLocaleString("en-IN")}</p>
            </div>
            <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 text-sm">
              <div>
                <dt className="text-slate-500">Source IP</dt>
                <dd>{row.source_ip || "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Destination IP</dt>
                <dd>{row.destination_ip || "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Port / protocol</dt>
                <dd>
                  {row.port ?? "—"} / {(row.protocol || "—").toUpperCase()}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Action</dt>
                <dd className="capitalize">{row.action || "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Requested by</dt>
                <dd>{row.requested_by_email || "seeded request"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Reviewed by</dt>
                <dd>{row.reviewed_by_email || "—"}</dd>
              </div>
            </dl>
            {row.request_comment ? <p className="text-sm text-slate-300">Request: {row.request_comment}</p> : null}
            {row.review_comment ? <p className="text-sm text-slate-300">Review: {row.review_comment}</p> : null}

            {row.status === "pending" && (canApprove || canReject) ? (
              <div className="flex flex-wrap items-end gap-3">
                <label className="sd-label flex-1 min-w-[220px]">
                  Review comment
                  <input
                    value={comments[row.request_id] || ""}
                    onChange={(e) => setComments((current) => ({ ...current, [row.request_id]: e.target.value }))}
                    placeholder={canReject ? "Required to reject" : "Optional"}
                    className="sd-input"
                  />
                </label>
                {canApprove ? (
                  <button type="button" className="sd-btn" onClick={() => decide(row, true)}>
                    Approve
                  </button>
                ) : null}
                {canReject ? (
                  <button
                    type="button"
                    className="rounded-lg border border-rose-500/40 px-4 py-2 text-sm text-rose-300"
                    onClick={() => decide(row, false)}
                  >
                    Reject
                  </button>
                ) : null}
              </div>
            ) : null}

            {row.history?.length ? (
              <ol className="border-t border-white/10 pt-3 text-xs text-slate-400 space-y-1">
                {row.history.map((event) => (
                  <li key={event.id}>
                    <span className="capitalize text-slate-200">{event.event_type}</span>
                    {" · "}
                    {event.actor_email || "system"}
                    {" · "}
                    {new Date(event.created_at).toLocaleString("en-IN")}
                    {event.comment ? ` · ${event.comment}` : ""}
                  </li>
                ))}
              </ol>
            ) : null}
          </article>
        ))}
        {requests.length === 0 ? <p className="text-sm text-slate-500">No requests in this filter.</p> : null}
      </div>
    </section>
  );
}
