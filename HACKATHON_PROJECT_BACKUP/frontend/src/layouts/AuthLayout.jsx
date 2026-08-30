import { Link, Outlet } from "react-router-dom";

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-navy-950">
      <header className="border-b border-white/10 px-6 py-4">
        <Link to="/login" className="text-lg font-semibold tracking-tight text-white">
          AICTE SecureDC
        </Link>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 items-center px-6 py-12">
        <div className="w-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
