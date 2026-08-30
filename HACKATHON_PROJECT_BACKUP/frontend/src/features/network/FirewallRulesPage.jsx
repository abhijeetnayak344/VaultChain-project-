import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { createChangeRequest, getFirewall, listChangeRequests, listFirewallRules } from "../../api/firewalls";
import { useAuth } from "../../context/AuthContext";

const emptyRule = {
  source_ip: "",
  destination_ip: "",
  port: "",
  protocol: "tcp",
  action: "allow",
  request_comment: "",
};

const ACTION_TONE = {
  allow: "text-emerald-300",
  deny: "text-rose-300",
};

export default function FirewallRulesPage() {
  const { id } = useParams();
  const { hasPermission } = useAuth();
  const [firewall, setFirewall] = useState(null);
  const [rules, setRules] = useState([]);
  const [pending, setPending] = useState([]);
  const [form, setForm] = useState(emptyRule);
  const [editingRule, setEditingRule] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const canRequest = hasPermission("firewall:request");

  async function load() {
    try {
      const [fw, rulePage, requestPage] = await Promise.all([
        getFirewall(id),
        listFirewallRules({ firewall: id }),
        listChangeRequests({ firewall: id, status: "pending" }),
      ]);
      setFirewall(fw.data);
      setRules(rulePage.data.results || rulePage.data);
      setPending(requestPage.data.results || requestPage.data);
    } catch {
      setError("Unable to load firewall rules.");
    }
  }

  useEffect(() => {
    load();
  }, [id]);

  function set(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function startEdit(rule) {
    setEditingRule(rule);
    setForm({
      source_ip: rule.source_ip,
      destination_ip: rule.destination_ip,
      port: rule.port ?? "",
      protocol: rule.protocol,
      action: rule.action,
      request_comment: "",
    });
    setNotice("");
    setError("");
  }

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    setSaving(true);
    const payload = {
      firewall: id,
      change_type: editingRule ? "update" : "create",
      rule: editingRule?.rule_id,
      source_ip: form.source_ip,
      destination_ip: form.destination_ip,
      protocol: form.protocol,
      action: form.action,
      request_comment: form.request_comment,
      port: form.protocol === "icmp" || form.protocol === "any" || form.port === "" ? null : Number(form.port),
    };
    try {
      await createChangeRequest(payload);
      setForm(emptyRule);
      setEditingRule(null);
      setNotice("Change submitted. A Security Admin must approve it before the live rule set updates.");
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Could not submit the rule change.");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(rule) {
    if (!window.confirm(`Request deletion of ${rule.action} ${rule.protocol} ${rule.source_ip} → ${rule.destination_ip}?`)) {
      return;
    }
    setError("");
    try {
      await createChangeRequest({
        firewall: id,
        change_type: "delete",
        rule: rule.rule_id,
        request_comment: `Delete rule ${rule.rule_id}`,
      });
      setNotice("Delete request submitted for Security Admin approval.");
      await load();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Could not submit the delete request.");
    }
  }

  if (!firewall && error) return <p className="text-sm text-rose-400">{error}</p>;
  if (!firewall) return <p className="text-sm text-slate-400">Loading rules…</p>;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-cyan-400">{firewall.vendor}</p>
          <h2 className="text-xl font-semibold text-white">{firewall.name}</h2>
          <p className="text-sm capitalize text-slate-400">{firewall.status}</p>
        </div>
        <div className="flex gap-3">
          <Link to="/firewalls" className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300">
            Back to firewalls
          </Link>
          <Link to="/firewall-approvals" className="text-sm text-cyan-400 hover:underline self-center">
            Approval queue
          </Link>
        </div>
      </div>

      {error ? <p className="text-sm text-rose-400">{error}</p> : null}
      {notice ? <p className="text-sm text-emerald-300">{notice}</p> : null}

      {canRequest ? (
        <form onSubmit={onSubmit} className="sd-card grid gap-4 md:grid-cols-2">
          <p className="md:col-span-2 text-sm text-slate-300">
            {editingRule ? "Request an edit to an existing rule" : "Request a new firewall rule"}
          </p>
          <label className="sd-label">
            Source IP
            <input
              required
              value={form.source_ip}
              onChange={(e) => set("source_ip", e.target.value)}
              placeholder="IP, CIDR, or any"
              className="sd-input"
            />
          </label>
          <label className="sd-label">
            Destination IP
            <input
              required
              value={form.destination_ip}
              onChange={(e) => set("destination_ip", e.target.value)}
              placeholder="IP, CIDR, or any"
              className="sd-input"
            />
          </label>
          <label className="sd-label">
            Protocol
            <select value={form.protocol} onChange={(e) => set("protocol", e.target.value)} className="sd-input">
              <option value="tcp">TCP</option>
              <option value="udp">UDP</option>
              <option value="icmp">ICMP</option>
              <option value="any">Any</option>
            </select>
          </label>
          <label className="sd-label">
            Port
            <input
              type="number"
              min="1"
              max="65535"
              value={form.port}
              onChange={(e) => set("port", e.target.value)}
              disabled={form.protocol === "icmp"}
              className="sd-input"
            />
          </label>
          <label className="sd-label">
            Action
            <select value={form.action} onChange={(e) => set("action", e.target.value)} className="sd-input">
              <option value="allow">Allow</option>
              <option value="deny">Deny</option>
            </select>
          </label>
          <label className="sd-label">
            Request comment
            <input
              value={form.request_comment}
              onChange={(e) => set("request_comment", e.target.value)}
              className="sd-input"
            />
          </label>
          <div className="flex gap-3 md:col-span-2">
            <button type="submit" disabled={saving} className="sd-btn">
              {saving ? "Submitting…" : editingRule ? "Request edit" : "Request add"}
            </button>
            {editingRule ? (
              <button
                type="button"
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300"
                onClick={() => {
                  setEditingRule(null);
                  setForm(emptyRule);
                }}
              >
                Cancel edit
              </button>
            ) : null}
          </div>
        </form>
      ) : (
        <p className="text-sm text-slate-400">Live rules are shown below. Only Network Admin can request changes.</p>
      )}

      <div className="sd-card overflow-x-auto p-0">
        <h3 className="px-4 py-3 text-sm font-semibold text-slate-200">Live rules</h3>
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Source IP</th>
              <th className="px-4 py-3">Destination IP</th>
              <th className="px-4 py-3">Port</th>
              <th className="px-4 py-3">Protocol</th>
              <th className="px-4 py-3">Action</th>
              {canRequest ? <th className="px-4 py-3">Actions</th> : null}
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.rule_id} className="border-t border-white/10">
                <td className="px-4 py-3">{rule.source_ip}</td>
                <td className="px-4 py-3">{rule.destination_ip}</td>
                <td className="px-4 py-3">{rule.port ?? "—"}</td>
                <td className="px-4 py-3 uppercase">{rule.protocol}</td>
                <td className={`px-4 py-3 capitalize ${ACTION_TONE[rule.action] || ""}`}>{rule.action}</td>
                {canRequest ? (
                  <td className="space-x-3 px-4 py-3 whitespace-nowrap">
                    <button type="button" className="text-slate-300 hover:underline" onClick={() => startEdit(rule)}>
                      Edit
                    </button>
                    <button type="button" className="text-rose-400" onClick={() => onDelete(rule)}>
                      Delete
                    </button>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
        {rules.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No live rules on this firewall.</p> : null}
      </div>

      <div className="sd-card overflow-x-auto p-0">
        <h3 className="px-4 py-3 text-sm font-semibold text-slate-200">Pending changes</h3>
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-slate-400">
            <tr>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Destination</th>
              <th className="px-4 py-3">Port / Proto</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Requested by</th>
            </tr>
          </thead>
          <tbody>
            {pending.map((row) => (
              <tr key={row.request_id} className="border-t border-white/10">
                <td className="px-4 py-3 capitalize">{row.change_type}</td>
                <td className="px-4 py-3">{row.source_ip || "—"}</td>
                <td className="px-4 py-3">{row.destination_ip || "—"}</td>
                <td className="px-4 py-3">
                  {row.port ?? "—"} / {(row.protocol || "—").toUpperCase()}
                </td>
                <td className="px-4 py-3 capitalize">{row.action || "—"}</td>
                <td className="px-4 py-3">{row.requested_by_email || "seeded"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {pending.length === 0 ? <p className="px-4 py-6 text-sm text-slate-500">No pending requests for this firewall.</p> : null}
      </div>
    </section>
  );
}
