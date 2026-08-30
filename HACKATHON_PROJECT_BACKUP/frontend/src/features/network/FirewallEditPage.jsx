import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getFirewall } from "../../api/firewalls";
import FirewallForm from "./FirewallForm";

export default function FirewallEditPage() {
  const { id } = useParams();
  const [firewall, setFirewall] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getFirewall(id)
      .then(({ data }) => setFirewall(data))
      .catch(() => setError("Unable to load firewall."));
  }, [id]);

  if (error) return <p className="text-sm text-rose-400">{error}</p>;
  if (!firewall) return <p className="text-sm text-slate-400">Loading firewall…</p>;

  return (
    <FirewallForm
      firewallId={firewall.firewall_id}
      initial={{ name: firewall.name, vendor: firewall.vendor, status: firewall.status }}
    />
  );
}
