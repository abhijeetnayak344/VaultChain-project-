import { useEffect, useState } from "react";
import {
  getAlertTrends,
  getCpuChart,
  getDashboardSummary,
  getRamChart,
  getSecurityEventsChart,
} from "../../api/dashboard";
import { AlertTrendsChart, CpuChart, RamChart, SecurityEventsChart } from "./charts";
import StatCard from "./StatCard";

function hourLabel(iso) {
  const date = new Date(iso);
  return date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [cpu, setCpu] = useState([]);
  const [ram, setRam] = useState([]);
  const [security, setSecurity] = useState({ timeline: [], by_type: [] });
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getDashboardSummary(),
      getCpuChart(24),
      getRamChart(24),
      getSecurityEventsChart(7),
      getAlertTrends(14),
    ])
      .then(([summaryRes, cpuRes, ramRes, securityRes, alertRes]) => {
        if (cancelled) return;
        setSummary(summaryRes.data);
        setCpu((cpuRes.data.series || []).map((row) => ({ ...row, label: hourLabel(row.timestamp) })));
        setRam((ramRes.data.series || []).map((row) => ({ ...row, label: hourLabel(row.timestamp) })));
        setSecurity(securityRes.data);
        setAlerts(alertRes.data.series || []);
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load dashboard statistics.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className="text-sm text-slate-400">Loading operations data…</p>;
  }
  if (error) {
    return <p className="text-sm text-rose-400">{error}</p>;
  }

  return (
    <section className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total servers" value={summary.total_servers} tone="cyan" />
        <StatCard label="Online servers" value={summary.online_servers} tone="emerald" />
        <StatCard label="Offline servers" value={summary.offline_servers} tone="rose" />
        <StatCard label="Total firewalls" value={summary.total_firewalls} tone="violet" />
        <StatCard label="Pending approvals" value={summary.pending_approvals} tone="orange" />
        <StatCard
          label="Active users"
          value={summary.active_users}
          hint="Signed in within 24 hours"
          tone="cyan"
        />
        <StatCard label="Critical alerts" value={summary.critical_alerts} hint="Open critical only" tone="rose" />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <article className="sd-card h-80">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">CPU usage (24h fleet average)</h2>
          <div className="h-64">
            <CpuChart data={cpu} />
          </div>
        </article>
        <article className="sd-card h-80">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">RAM usage (24h fleet average)</h2>
          <div className="h-64">
            <RamChart data={ram} />
          </div>
        </article>
        <article className="sd-card h-[28rem]">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Security events (7 days)</h2>
          <div className="h-[24rem]">
            <SecurityEventsChart timeline={security.timeline} byType={security.by_type} />
          </div>
        </article>
        <article className="sd-card h-[28rem]">
          <h2 className="mb-3 text-sm font-semibold text-slate-200">Alert trends (14 days)</h2>
          <div className="h-[24rem]">
            <AlertTrendsChart data={alerts} />
          </div>
        </article>
      </div>
    </section>
  );
}
