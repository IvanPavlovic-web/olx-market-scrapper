import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold">
        OLX Monitor <span className="text-accent">BiH</span>
      </h1>
      <p className="text-gray-400 max-w-lg text-center">
        Real-time praćenje cijena, novih oglasa i pada cijena na OLX.ba i portalima u BiH.
      </p>
      <div className="flex gap-3">
        <Link href="/login" className="btn-ghost">Prijava</Link>
        <Link href="/dashboard" className="btn">Dashboard</Link>
      </div>
    </main>
  );
}
