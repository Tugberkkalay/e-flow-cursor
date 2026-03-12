"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Download, Search, Shield } from "lucide-react";

export default function AuditPage() {
  const [search, setSearch] = useState("");

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["audit", search],
    queryFn: () => api.get(`/audit?limit=200`).then(r => r.data),
  });

  const filtered = events.filter((e: { event_type: string; actor_email?: string }) =>
    !search || e.event_type.toLowerCase().includes(search.toLowerCase()) || (e.actor_email || "").toLowerCase().includes(search.toLowerCase())
  );

  function exportCsv() {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/audit/export`, "_blank");
  }

  const EVENT_TYPES_COLOR: Record<string, string> = {
    "instance.started": "bg-info-soft text-info-foreground",
    "instance.completed": "bg-success-soft text-success-foreground",
    "instance.failed": "bg-destructive-soft text-destructive",
    "instance.cancelled": "bg-secondary text-accent-muted",
    "approval.approved": "bg-success-soft text-success-foreground",
    "approval.rejected": "bg-destructive-soft text-destructive",
    "task.completed": "bg-success-soft text-success-foreground",
    "node.started": "bg-info-soft text-info-foreground",
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-base font-semibold text-accent">Denetim Günlüğü</h2>
          <p className="text-xs text-accent-muted mt-0.5">Değiştirilemez olay akışı · {events.length} olay</p>
        </div>
        <button className="btn-secondary btn-sm" onClick={exportCsv}>
          <Download size={13} /> CSV İndir
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-4 max-w-sm">
        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-accent-muted" />
        <input
          className="input pl-8 text-sm"
          placeholder="Olay tipi veya kullanıcı ara..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted">
              {["Olay Tipi", "Aktör", "Süreç", "Zaman"].map(h => (
                <th key={h} className="text-left px-5 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              [...Array(8)].map((_, i) => (
                <tr key={i}>
                  {[...Array(4)].map((_, j) => (
                    <td key={j} className="px-5 py-3.5"><div className="h-4 bg-border rounded animate-pulse" /></td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-12 text-center text-sm text-accent-muted">
                  <Shield size={20} className="mx-auto mb-2 text-accent-muted/50" />
                  Kayıt bulunamadı
                </td>
              </tr>
            ) : (
              filtered.map((event: {
                id: string;
                event_type: string;
                actor_email?: string;
                instance_id?: string;
                payload: Record<string, unknown>;
                created_at: string;
              }) => (
                <tr key={event.id} className="hover:bg-muted/50 transition-colors">
                  <td className="px-5 py-3">
                    <span className={`badge text-[10px] ${EVENT_TYPES_COLOR[event.event_type] || "badge-neutral"}`}>
                      {event.event_type}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs text-accent-muted">{event.actor_email || "—"}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-mono text-accent-muted">
                      {event.instance_id ? event.instance_id.slice(0, 8) + "..." : "—"}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs text-accent-muted">{formatDate(event.created_at)}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
