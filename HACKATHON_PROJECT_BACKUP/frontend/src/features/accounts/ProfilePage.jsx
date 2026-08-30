import { useState } from "react";
import { changePassword, updateMe } from "../../api/auth";
import { useAuth } from "../../context/AuthContext";

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  async function saveProfile(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await updateMe({ full_name: fullName });
      await refreshUser();
      setMessage("Profile updated.");
    } catch {
      setError("Could not update profile.");
    }
  }

  async function savePassword(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await changePassword({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      await logout();
    } catch (err) {
      setError(err.response?.data?.error?.message || "Could not change password.");
    }
  }

  if (!user) return null;

  return (
    <section className="space-y-6">
      <div className="sd-card">
        <h2 className="text-sm font-semibold text-slate-200">Roles</h2>
        <p className="mt-2 text-sm text-slate-300">
          {user.roles?.length ? user.roles.map((role) => role.name).join(", ") : "No role assigned"}
        </p>
        <p className="mt-2 text-xs text-slate-500">{user.email}</p>
      </div>

      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <form onSubmit={saveProfile} className="sd-card max-w-lg space-y-4">
        <h2 className="text-sm font-semibold text-slate-200">Display name</h2>
        <input required value={fullName} onChange={(e) => setFullName(e.target.value)} className="sd-input" />
        <button type="submit" className="sd-btn">
          Save profile
        </button>
      </form>

      <form onSubmit={savePassword} className="sd-card max-w-lg space-y-4">
        <h2 className="text-sm font-semibold text-slate-200">Change password</h2>
        <p className="text-xs text-slate-500">You will be signed out after a successful change.</p>
        <input
          type="password"
          required
          placeholder="Current password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="sd-input"
        />
        <input
          type="password"
          required
          minLength={12}
          placeholder="New password (min 12 characters)"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="sd-input"
        />
        <button type="submit" className="sd-btn">
          Update password
        </button>
      </form>
    </section>
  );
}
