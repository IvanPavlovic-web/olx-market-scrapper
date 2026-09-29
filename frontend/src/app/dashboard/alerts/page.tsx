"use client";
import useSWR, { mutate } from "swr";
import { fetcher, api, getApiErrorMessage } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import { Trash2, Plus, Bell } from "lucide-react";
import type { AlertRule } from "@/types";

export default function AlertsPage() {
  const { data: rules } = useSWR<AlertRule[]>("/alerts", fetcher);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: "",
    keywords: "",
    exclude_keywords: "",
    source: "",
    min_price: "",
    max_price: "",
    location: "",
    cooldown_seconds: 300,
  });

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/alerts", {
        ...form,
        min_price: form.min_price ? Number(form.min_price) : null,
        max_price: form.max_price ? Number(form.max_price) : null,
        source: form.source || null,
      });
      toast.success("Alert kreiran");
      setCreating(false);
      setForm({
        name: "",
        keywords: "",
        exclude_keywords: "",
        source: "",
        min_price: "",
        max_price: "",
        location: "",
        cooldown_seconds: 300,
      });
      mutate("/alerts");
    } catch (e: unknown) {
      toast.error(getApiErrorMessage(e));
    }
  }

  async function remove(id: string) {
    if (!confirm("Obriši alert?")) return;
    await api.delete(`/alerts/${id}`);
    mutate("/alerts");
    toast.success("Obrisano");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alert pravila</h1>
        <button className="btn" onClick={() => setCreating(!creating)}>
          <Plus size={16} /> Novi alert
        </button>
      </div>

      {creating && (
        <form
          onSubmit={create}
          className="card grid grid-cols-1 md:grid-cols-3 gap-3"
        >
          <input
            className="input md:col-span-3"
            placeholder="Naziv alerta"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            className="input"
            placeholder="Keywords (npr. passat, b8)"
            value={form.keywords}
            onChange={(e) => setForm({ ...form, keywords: e.target.value })}
          />
          <input
            className="input"
            placeholder="Isključi (npr. havarisan)"
            value={form.exclude_keywords}
            onChange={(e) =>
              setForm({ ...form, exclude_keywords: e.target.value })
            }
          />
          <input
            className="input"
            placeholder="Lokacija"
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
          />
          <input
            className="input"
            placeholder="Min cijena"
            value={form.min_price}
            onChange={(e) => setForm({ ...form, min_price: e.target.value })}
          />
          <input
            className="input"
            placeholder="Max cijena"
            value={form.max_price}
            onChange={(e) => setForm({ ...form, max_price: e.target.value })}
          />
          <select
            className="input"
            value={form.source}
            onChange={(e) => setForm({ ...form, source: e.target.value })}
          >
            <option value="">Svi izvori</option>
            <option value="olx">OLX.ba</option>
          </select>
          <button type="submit" className="btn md:col-span-3 justify-center">
            Kreiraj
          </button>
        </form>
      )}

      <div className="space-y-2">
        {(rules || []).map((r) => (
          <div key={r.id} className="card flex items-center justify-between">
            <div className="flex items-start gap-3">
              <Bell
                size={18}
                className={r.is_active ? "text-accent" : "text-gray-500"}
              />
              <div>
                <div className="font-semibold">{r.name}</div>
                <div className="text-xs text-gray-400">
                  {r.keywords && `kw: ${r.keywords}`}{" "}
                  {r.max_price && `· max: ${r.max_price} KM`}{" "}
                  {r.location && `· ${r.location}`}
                </div>
              </div>
            </div>
            <button
              className="text-danger hover:opacity-80"
              onClick={() => remove(r.id)}
            >
              <Trash2 size={18} />
            </button>
          </div>
        ))}
        {rules && rules.length === 0 && (
          <div className="text-gray-500">Nemaš još alerta.</div>
        )}
      </div>
    </div>
  );
}
