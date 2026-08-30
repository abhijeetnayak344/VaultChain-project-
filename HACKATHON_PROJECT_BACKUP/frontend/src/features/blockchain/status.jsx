export function verificationLabel(status) {
  if (status === "verified") return "VERIFIED";
  if (status === "alert") return "SECURITY ALERT";
  if (status === "not_anchored") return "NOT ANCHORED";
  if (status === "unavailable") return "UNAVAILABLE";
  return "UNVERIFIED";
}

export function VerificationBadge({ status }) {
  const tone =
    status === "verified"
      ? "border-emerald-400/40 bg-emerald-500/10 text-emerald-300"
      : status === "alert"
        ? "border-rose-400/40 bg-rose-500/10 text-rose-300"
        : "border-white/10 bg-white/5 text-slate-300";
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold tracking-wide ${tone}`}>
      {verificationLabel(status)}
    </span>
  );
}
