"use client";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import Link from "next/link";
import { Plus, Workflow, Clock, CheckCircle, Archive } from "lucide-react";
import { useState } from "react";
import { formatRelative, statusColor, statusLabel } from "@/lib/utils";
import { CreateFlowModal } from "@/components/flow/CreateFlowModal";

export default function DesignPage() {
  const [showCreate, setShowCreate] = useState(false);

  const { data: flows = [], refetch } = useQuery({
    queryKey: ["flows"],
    queryFn: () => api.get("/flows").then(r => r.data),
  });

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-base font-semibold text-accent">Akış Tasarımları</h2>
          <p className="text-xs text-accent-muted mt-0.5">{flows.length} akış tanımlı</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={14} />
          Yeni Akış
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {flows.map((flow: { id: string; name: string; description: string; is_template: boolean; latest_version?: { status: string; version_number: number }; updated_at: string }) => (
          <Link key={flow.id} href={`/design/${flow.id}`}>
            <div className="card-hover p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-accent-soft flex items-center justify-center">
                  <Workflow size={16} className="text-accent" />
                </div>
                <div className="flex items-center gap-2">
                  {flow.is_template && (
                    <span className="badge badge-info text-[10px]">Şablon</span>
                  )}
                  <span className={`badge text-[10px] ${statusColor(flow.latest_version?.status || "draft")}`}>
                    {statusLabel(flow.latest_version?.status || "draft")}
                  </span>
                </div>
              </div>
              <h3 className="text-sm font-semibold text-accent mb-1">{flow.name}</h3>
              <p className="text-xs text-accent-muted line-clamp-2 leading-relaxed mb-4">{flow.description || "Açıklama yok"}</p>
              <div className="flex items-center gap-3 text-xs text-accent-muted">
                <span className="flex items-center gap-1">
                  <Clock size={11} />
                  {formatRelative(flow.updated_at)}
                </span>
                {flow.latest_version && (
                  <span>v{flow.latest_version.version_number}</span>
                )}
              </div>
            </div>
          </Link>
        ))}

        {/* New Flow Card */}
        <button onClick={() => setShowCreate(true)}>
          <div className="rounded-xl border-2 border-dashed border-border hover:border-accent/30 hover:bg-accent-soft/30 transition-all duration-200 p-5 flex flex-col items-center justify-center min-h-[160px] cursor-pointer group">
            <div className="w-10 h-10 rounded-xl bg-secondary group-hover:bg-accent-soft transition-colors flex items-center justify-center mb-2">
              <Plus size={16} className="text-accent-muted group-hover:text-accent" />
            </div>
            <span className="text-sm font-medium text-accent-muted group-hover:text-accent transition-colors">Yeni Akış Oluştur</span>
          </div>
        </button>
      </div>

      {showCreate && (
        <CreateFlowModal
          onClose={() => setShowCreate(false)}
          onCreated={() => { refetch(); setShowCreate(false); }}
        />
      )}
    </div>
  );
}
