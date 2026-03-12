"use client";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatRelative, statusColor, statusLabel } from "@/lib/utils";
import { ClipboardList, CheckSquare, Play, AlertCircle, TrendingUp, Clock } from "lucide-react";
import Link from "next/link";

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: React.FC<{size: number; className?: string}>; color: string }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={16} className="text-current" />
        </div>
      </div>
      <div className="text-2xl font-bold text-accent">{value}</div>
      <div className="text-xs text-accent-muted mt-0.5 font-medium">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: instances = [] } = useQuery({
    queryKey: ["instances-all"],
    queryFn: () => api.get("/instances").then(r => r.data),
  });

  const { data: inbox = [] } = useQuery({
    queryKey: ["inbox"],
    queryFn: () => api.get("/inbox").then(r => r.data),
  });

  const { data: flows = [] } = useQuery({
    queryKey: ["flows"],
    queryFn: () => api.get("/flows").then(r => r.data),
  });

  const running = instances.filter((i: { status: string }) => i.status === "running").length;
  const completed = instances.filter((i: { status: string }) => i.status === "completed").length;
  const failed = instances.filter((i: { status: string }) => ["failed", "rejected"].includes(i.status)).length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Aktif Süreç" value={running} icon={Play} color="bg-info-soft text-info" />
        <StatCard label="Bekleyen Görev" value={inbox.length} icon={CheckSquare} color="bg-warning-soft text-warning" />
        <StatCard label="Tamamlanan" value={completed} icon={TrendingUp} color="bg-success-soft text-success" />
        <StatCard label="Başarısız / Reddedildi" value={failed} icon={AlertCircle} color="bg-destructive-soft text-destructive" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Instances */}
        <div className="lg:col-span-2 card">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-accent">Son Süreçler</h3>
              <p className="text-xs text-accent-muted">Tüm aktif ve tamamlanan akışlar</p>
            </div>
            <Link href="/processes" className="text-xs font-medium text-accent-muted hover:text-accent">Tümünü gör →</Link>
          </div>
          <div className="divide-y divide-border">
            {instances.slice(0, 8).map((inst: { id: string; title: string; status: string; definition_name: string; started_at: string }) => (
              <Link key={inst.id} href={`/processes/${inst.id}`}>
                <div className="px-5 py-3.5 hover:bg-surface-hover transition-colors cursor-pointer flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-accent truncate">{inst.title}</div>
                    <div className="text-xs text-accent-muted mt-0.5">{inst.definition_name} · {formatRelative(inst.started_at)}</div>
                  </div>
                  <span className={statusColor(inst.status) + " badge text-xs"}>
                    {statusLabel(inst.status)}
                  </span>
                </div>
              </Link>
            ))}
            {instances.length === 0 && (
              <div className="px-5 py-8 text-center text-sm text-accent-muted">
                Henüz süreç başlatılmadı.
                <br />
                <Link href="/processes" className="text-accent font-medium mt-1 inline-block">Süreç Başlat →</Link>
              </div>
            )}
          </div>
        </div>

        {/* Inbox */}
        <div className="card">
          <div className="px-5 py-4 border-b border-border flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-accent">Onaylarım</h3>
              <p className="text-xs text-accent-muted">Bekleyen görevler</p>
            </div>
            <Link href="/inbox" className="text-xs font-medium text-accent-muted hover:text-accent">Tümü →</Link>
          </div>
          <div className="divide-y divide-border">
            {inbox.slice(0, 6).map((item: { id: string; title: string; type: string; instance_title: string; created_at: string; instance_id?: string }) => (
              <Link key={item.id} href={`/processes/${item.instance_id || ""}`}>
                <div className="px-5 py-3.5 hover:bg-surface-hover transition-colors cursor-pointer">
                  <div className="flex items-start gap-2">
                    <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${item.type === "approval" ? "bg-warning" : "bg-info"}`} />
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-accent truncate">{item.title}</div>
                      <div className="text-xs text-accent-muted mt-0.5 flex items-center gap-1">
                        <Clock size={10} />
                        {formatRelative(item.created_at)}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
            {inbox.length === 0 && (
              <div className="px-5 py-8 text-center text-sm text-accent-muted">
                Bekleyen görev yok.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Templates */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-accent">Akış Şablonları</h3>
          <Link href="/design" className="text-xs font-medium text-accent-muted hover:text-accent">Designer →</Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {flows.filter((f: { is_template: boolean }) => f.is_template).map((flow: { id: string; name: string; description: string; category: string; latest_version?: { status: string } }) => (
            <Link key={flow.id} href={`/design/${flow.id}`}>
              <div className="card-hover p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="w-8 h-8 rounded-lg bg-accent-soft flex items-center justify-center">
                    <ClipboardList size={14} className="text-accent" />
                  </div>
                  <span className={`badge text-[10px] ${flow.latest_version?.status === "published" ? "badge-success" : "badge-neutral"}`}>
                    {flow.latest_version?.status === "published" ? "Yayında" : "Taslak"}
                  </span>
                </div>
                <div className="text-sm font-semibold text-accent mb-1 leading-snug">{flow.name}</div>
                <div className="text-xs text-accent-muted leading-relaxed line-clamp-2">{flow.description}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
