import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="sd-card">
      <h1 className="text-2xl font-semibold text-white">Page not found</h1>
      <Link to="/" className="mt-4 inline-block text-cyan-400 hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}
