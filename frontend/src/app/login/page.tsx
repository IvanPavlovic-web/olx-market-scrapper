"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/auth";
import { getApiErrorMessage } from "@/lib/api";
import { toast } from "sonner";

export default function LoginPage() {
  const r = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, username, password);
      toast.success("Uspješno");
      r.push("/dashboard");
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={submit} className="card w-full max-w-md space-y-4">
        <h1 className="text-2xl font-bold">
          {mode === "login" ? "Prijava" : "Registracija"}
        </h1>
        <input className="input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        {mode === "register" && (
          <input className="input" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        )}
        <input className="input" type="password" placeholder="Lozinka" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className="btn w-full justify-center" disabled={loading}>
          {loading ? "..." : mode === "login" ? "Prijavi se" : "Registruj se"}
        </button>
        <button type="button" className="text-sm text-gray-400 hover:text-accent" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Nemaš račun? Registruj se" : "Već imaš račun? Prijavi se"}
        </button>
      </form>
    </main>
  );
}
