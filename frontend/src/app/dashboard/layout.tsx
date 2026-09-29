"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bell, ListChecks, Settings, LogOut } from "lucide-react";
import { logout } from "@/lib/auth";
import clsx from "clsx";

const nav = [
  { href: "/dashboard", label: "Pregled", icon: LayoutDashboard },
  { href: "/dashboard/listings", label: "Oglasi", icon: ListChecks },
  { href: "/dashboard/alerts", label: "Alerti", icon: Bell },
  { href: "/dashboard/settings", label: "Postavke", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 border-r border-border p-4 flex flex-col gap-2">
        <div className="text-xl font-bold mb-4">
          OLX <span className="text-accent">Monitor</span>
        </div>
        {nav.map((n) => {
          const Icon = n.icon;
          const active = path === n.href;
          return (
            <Link key={n.href} href={n.href} className={clsx(
              "flex items-center gap-2 px-3 py-2 rounded-lg transition",
              active ? "bg-accent text-black font-semibold" : "hover:bg-border"
            )}>
              <Icon size={18} /> {n.label}
            </Link>
          );
        })}
        <button onClick={logout} className="mt-auto flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-border text-gray-400">
          <LogOut size={18} /> Odjava
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">{children}</main>
    </div>
  );
}
