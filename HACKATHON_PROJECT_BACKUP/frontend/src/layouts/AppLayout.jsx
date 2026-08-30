import { useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import PermissionGate from "../components/PermissionGate";
import { useAuth } from "../context/AuthContext";

const navLink = ({ isActive }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
    isActive ? "bg-cyan-500/15 text-cyan-300" : "text-slate-300 hover:bg-white/5 hover:text-white"
  }`;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const titles = {
    "/": "Cybersecurity dashboard",
    "/profile": "User profile",
    "/users": "User management",
    "/roles": "Role management",
    "/permissions": "Permission catalog",
    "/servers": "Servers",
    "/servers/new": "Add server",
    "/firewalls": "Firewall dashboard",
    "/firewalls/new": "Add firewall",
    "/firewall-approvals": "Firewall approvals",
    "/audit": "Security audit",
    "/blockchain": "Blockchain audit",
    "/blockchain/verify": "Integrity check",
    "/blockchain/transactions": "Chain transactions",
    "/blockchain/alerts": "Integrity alerts",
  };
  let title = titles[location.pathname] || "SecureDC";
  if (location.pathname.startsWith("/servers/") && location.pathname.endsWith("/edit")) {
    title = "Edit server";
  } else if (location.pathname.startsWith("/servers/") && location.pathname !== "/servers/new") {
    title = "Server details";
  } else if (location.pathname.startsWith("/firewalls/") && location.pathname.endsWith("/edit")) {
    title = "Edit firewall";
  } else if (location.pathname.startsWith("/firewalls/") && location.pathname !== "/firewalls/new") {
    title = "Firewall rules";
  } else if (location.pathname.startsWith("/blockchain/verify/")) {
    title = "Integrity check";
  } else if (location.pathname.startsWith("/audit/") && location.pathname !== "/audit") {
    title = "Audit event";
  }

  const nav = (
    <>
      <PermissionGate permission="dashboard:read">
        <NavLink to="/" className={navLink} end onClick={() => setOpen(false)}>
          Dashboard
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="server:read">
        <NavLink to="/servers" className={navLink} onClick={() => setOpen(false)}>
          Servers
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="firewall:read">
        <NavLink to="/firewalls" className={navLink} onClick={() => setOpen(false)}>
          Firewalls
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="firewall:read">
        <NavLink to="/firewall-approvals" className={navLink} onClick={() => setOpen(false)}>
          Approvals
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="audit:read">
        <NavLink to="/audit" className={navLink} onClick={() => setOpen(false)}>
          Audit
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="audit:read">
        <NavLink to="/blockchain" className={navLink} onClick={() => setOpen(false)}>
          Blockchain
        </NavLink>
      </PermissionGate>
      <NavLink to="/profile" className={navLink} onClick={() => setOpen(false)}>
        Profile
      </NavLink>
      <PermissionGate permission="user:read">
        <NavLink to="/users" className={navLink} onClick={() => setOpen(false)}>
          Users
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="role:read">
        <NavLink to="/roles" className={navLink} onClick={() => setOpen(false)}>
          Roles
        </NavLink>
      </PermissionGate>
      <PermissionGate permission="permission:read">
        <NavLink to="/permissions" className={navLink} onClick={() => setOpen(false)}>
          Permissions
        </NavLink>
      </PermissionGate>
    </>
  );

  return (
    <div className="flex min-h-screen bg-navy-950">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-white/10 bg-navy-900 lg:flex">
        <div className="border-b border-white/10 px-5 py-5">
          <Link to="/" className="text-lg font-semibold tracking-tight text-white">
            SecureDC
          </Link>
          <p className="mt-1 text-xs text-slate-400">AICTE cyber operations</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">{nav}</nav>
      </aside>

      {open ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          aria-label="Close menu"
          onClick={() => setOpen(false)}
        />
      ) : null}

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform border-r border-white/10 bg-navy-900 transition lg:hidden ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="border-b border-white/10 px-5 py-5">
          <p className="text-lg font-semibold text-white">SecureDC</p>
        </div>
        <nav className="flex flex-col gap-1 p-3">{nav}</nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-white/10 bg-navy-900/90 px-4 py-3 backdrop-blur md:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-lg border border-white/10 p-2 text-slate-200 lg:hidden"
              onClick={() => setOpen(true)}
              aria-label="Open menu"
            >
              Menu
            </button>
            <div>
              <p className="text-xs uppercase tracking-wider text-cyan-400">Operations center</p>
              <h1 className="text-base font-semibold text-white md:text-lg">{title}</h1>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden max-w-[220px] truncate text-slate-400 sm:inline">{user?.email}</span>
            <span className="hidden rounded-full border border-white/10 px-2 py-1 text-xs text-slate-300 md:inline">
              {user?.roles?.[0]?.name || "No role"}
            </span>
            <button type="button" onClick={logout} className="text-saffron-400 hover:text-saffron-500">
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
