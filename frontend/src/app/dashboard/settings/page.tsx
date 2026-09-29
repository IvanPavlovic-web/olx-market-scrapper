"use client";
import { currentUser, logout } from "@/lib/auth";

export default function SettingsPage() {
  const user = currentUser();
  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold">Postavke</h1>
      <div className="card">
        <div className="text-sm text-gray-400">Prijavljen kao</div>
        <div className="text-lg font-semibold">{user?.username} ({user?.email})</div>
      </div>
      <button className="btn-ghost" onClick={logout}>Odjavi se</button>
    </div>
  );
}
