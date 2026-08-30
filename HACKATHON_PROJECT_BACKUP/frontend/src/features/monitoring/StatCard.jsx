function toneClass(tone) {
  const map = {
    cyan: "text-cyan-300",
    emerald: "text-emerald-300",
    rose: "text-rose-300",
    amber: "text-amber-300",
    violet: "text-violet-300",
    orange: "text-saffron-400",
  };
  return map[tone] || "text-slate-100";
}

export default function StatCard({ label, value, hint, tone = "cyan" }) {
  return (
    <article className="sd-card">
      <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${toneClass(tone)}`}>{value}</p>
      {hint ? <p className="mt-2 text-xs text-slate-500">{hint}</p> : null}
    </article>
  );
}
