"use client";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { useState } from "react";
import type { Listing } from "@/types";

export default function ListingsPage() {
  const [q, setQ] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const query = new URLSearchParams();
  if (q) query.set("q", q);
  if (maxPrice) query.set("max_price", maxPrice);

  const { data } = useSWR<Listing[]>(
    `/listings?${query.toString()}&limit=100`,
    fetcher,
    { refreshInterval: 10000 },
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Oglasi</h1>
      <div className="flex gap-3">
        <input
          className="input"
          placeholder="Pretraga..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <input
          className="input max-w-[140px]"
          placeholder="Max cijena"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {(data || []).map((l) => (
          <a
            key={l.id}
            href={l.url}
            target="_blank"
            className="card hover:border-accent transition"
          >
            <div className="font-medium line-clamp-2">{l.title}</div>
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
  );
}
