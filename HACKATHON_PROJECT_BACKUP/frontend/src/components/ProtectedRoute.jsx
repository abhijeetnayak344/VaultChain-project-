import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, permission }) {
  const { ready, isAuthenticated, hasPermission } = useAuth();
  const location = useLocation();

  if (!ready) {
    return <p className="p-6 text-sm text-slate-400">Loading session…</p>;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (permission && !hasPermission(permission)) {
    if (location.pathname === "/") {
      return <Navigate to="/profile" replace />;
    }
    return (
      <div className="sd-card">
        <h1 className="text-lg font-semibold text-white">Access denied</h1>
        <p className="mt-2 text-sm text-slate-400">
          Your role does not include <code className="text-cyan-300">{permission}</code>.
        </p>
      </div>
    );
  }
  return children;
}
