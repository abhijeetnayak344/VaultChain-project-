import { useAuth } from "../context/AuthContext";

export default function PermissionGate({ permission, children }) {
  const { hasPermission } = useAuth();
  if (permission && !hasPermission(permission)) {
    return null;
  }
  return children;
}
