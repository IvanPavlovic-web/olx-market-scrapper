"use client";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { useWS } from "@/hooks/useWS";
import { Activity, TrendingDown } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Listing, ListingStats } from "@/types";

export default function DashboardPage() {
  const { data: stats } = useSWR<ListingStats>(
    "/listings/stats/summary",
    fetcher,
    { refreshInterval: 15000 },
  );
  const { data: listings } = useSWR<Listing[]>("/listings?limit=20", fetcher, {
    refreshInterval: 10000,
  });
  const { messages, connected } = useWS();
  const chartData = messages
    .filter((message) => message.type === "alert")
    .slice(0, 20)
    .reverse()
    .map((alert, i) => ({ i, price: Number(alert.listing.price) || 0 }));

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pregled</h1>
        <span className={`tag ${connected ? "text-accent" : "text-danger"}`}>
          <Activity size={12} className="inline mr-1" />
          {connected ? "Live" : "Offline"}
        </span>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-gray-400 text-sm">Ukupno oglasa</div>
          <div className="text-3xl font-bold">{stats?.total ?? "—"}</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm">Aktivnih</div>
          <div className="text-3xl font-bold text-accent">
            {stats?.active ?? "—"}
          </div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm">Prosj. cijena</div>
          <div className="text-3xl font-bold">
            {stats?.avg_price ? `${Math.round(stats.avg_price)} KM` : "—"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card lg:col-span-2">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown size={18} className="text-accent" />
            <h2 className="font-semibold">Live feed alerta</h2>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData}>
                <XAxis dataKey="i" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid #1f2937",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#00d9a3"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 text-sm py-12 text-center">
              Čekam nove alerte...
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Zadnji alerti</h2>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {messages
              .filter((m) => m.type === "alert")
              .slice(0, 8)
              .map((m, idx) => (
                <a
                  key={idx}
                  href={m.listing.url}
                  target="_blank"
                  className="block p-2 rounded-lg border border-border hover:border-accent"
                >
                  <div className="text-sm font-medium line-clamp-1">
                    {m.listing.title}
                  </div>
                  <div className="text-xs text-accent">
                    {m.listing.price
                      ? `${m.listing.price} ${m.listing.currency}`
                      : "—"}{" "}
                    · {m.rule_name}
                  </div>
                </a>
              ))}
            {messages.filter((m) => m.type === "alert").length === 0 && (
              <div className="text-gray-500 text-sm">Nema novih alerta.</div>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">Najnoviji oglasi</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(listings || []).map((l) => (
            <a
              key={l.id}
              href={l.url}
              target="_blank"
              className="p-3 rounded-lg border border-border hover:border-accent transition"
            >
              <div className="font-medium line-clamp-2 text-sm">{l.title}</div>
              <div className="text-accent text-lg font-bold mt-2">
                {l.price ? `${l.price} ${l.currency}` : "—"}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {l.location || "—"}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
