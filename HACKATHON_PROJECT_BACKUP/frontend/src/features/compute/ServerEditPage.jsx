import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getServer } from "../../api/servers";
import ServerForm from "./ServerForm";

export default function ServerEditPage() {
  const { id } = useParams();
  const [server, setServer] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getServer(id)
      .then(({ data }) => setServer(data))
      .catch(() => setError("Unable to load server for editing."));
  }, [id]);

  if (error) return <p className="text-sm text-rose-400">{error}</p>;
  if (!server) return <p className="text-sm text-slate-400">Loading server…</p>;

  return (
    <ServerForm
      serverId={server.server_id}
      initial={{
        code: server.code,
        name: server.name,
        hostname: server.hostname,
        ip_address: server.ip_address,
        operating_system: server.operating_system,
        location: server.location,
        environment: server.environment,
        status: server.status,
        cpu_percent: server.cpu_percent,
        ram_percent: server.ram_percent,
        storage_percent: server.storage_percent,
      }}
    />
  );
}
