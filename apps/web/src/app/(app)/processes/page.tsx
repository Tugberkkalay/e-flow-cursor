"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import Link from "next/link";
import { Plus, Search, Filter } from "lucide-react";
import { formatRelative, statusColor, statusLabel } from "@/lib/utils";
import { StartProcessModal } from "@/components/instances/StartProcessModal";

const STATUS_TABS = [
  { id: "all", label: "Tümü" },
  { id: "running", label: "İşlemde" },
  { id: "completed", label: "Tamamlandı" },
  { id: "rejected", label: "Reddedildi" },
  { id: "failed", label: "Başarısız" },
  { id: "cancelled", label: "İptal" },
];

export default function ProcessesPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [showStart, setShowStart] = useState(false);

  const { data: instances = [], isLoading, refetch } = useQuery({
    queryKey: ["instances", activeTab],
    queryFn: () => api.get(`/instances${activeTab !== "all" ? `?status=${activeTab}` : ""}`).then(r => r.data),
  });

  const filtered = instances.filter((inst: { title: string; definition_name: string }) =>
    !search || inst.title.toLowerCase().includes(search.toLowerCase()) || inst.definition_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-base font-semibold text-accent">Süreçler</h2>
          <p className="text-xs text-accent-muted mt-0.5">{instances.length} süreç</p>
        </div>
        <button className="btn-primary" onClick={() => setShowStart(true)}>
          <Plus size={14} />
          Süreç Başlat
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-1 border border-border rounded-lg p-0.5 bg-surface">
          {STATUS_TABS.map(tab => (
            <button
              key={tab.id}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === tab.id ? "bg-accent text-white shadow-xs" : "text-accent-muted hover:text-accent hover:bg-surface-hover"
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative flex-1 max-w-xs">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-accent-muted" />
          <input
            type="text"
            className="input pl-8 text-sm"
            placeholder="Süreç ara..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted">
              <th className="text-left px-5 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">Başlık</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide hidden md:table-cell">Akış</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide hidden lg:table-cell">Talep Eden</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">Durum</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide hidden lg:table-cell">Aktif Adım</th>
              <th className="text-right px-5 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">Tarih</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i}>
                  {[...Array(6)].map((_, j) => (
                    <td key={j} className="px-5 py-4">
                      <div className="h-4 bg-border rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-sm text-accent-muted">
                  Süreç bulunamadı.
                  <br />
                  <button className="text-accent font-medium mt-1" onClick={() => setShowStart(true)}>Yeni Süreç Başlat →</button>
                </td>
              </tr>
            ) : (
              filtered.map((inst: {
                id: string;
                title: string;
                definition_name: string;
                started_by_name: string;
                status: string;
                current_node_id: string | null;
                started_at: string;
              }) => (
                <tr key={inst.id} className="hover:bg-muted/50 transition-colors cursor-pointer group">
                  <td className="px-5 py-3.5">
                    <Link href={`/processes/${inst.id}`} className="block">
                      <div className="font-medium text-accent group-hover:text-primary transition-colors">{inst.title}</div>
                    </Link>
                  </td>
                  <td className="px-4 py-3.5 hidden md:table-cell">
                    <span className="text-xs text-accent-muted">{inst.definition_name}</span>
                  </td>
                  <td className="px-4 py-3.5 hidden lg:table-cell">
                    <span className="text-xs text-accent-muted">{inst.started_by_name || "—"}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`badge text-xs ${statusColor(inst.status)}`}>
                      {statusLabel(inst.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 hidden lg:table-cell">
                    <span className="text-xs text-accent-muted font-mono">{inst.current_node_id || "—"}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <span className="text-xs text-accent-muted">{formatRelative(inst.started_at)}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showStart && (
        <StartProcessModal
          onClose={() => setShowStart(false)}
          onStarted={() => { refetch(); setShowStart(false); }}
        />
      )}
    </div>
  );
}
