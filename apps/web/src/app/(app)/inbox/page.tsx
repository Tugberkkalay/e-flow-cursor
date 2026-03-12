"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatRelative, statusColor } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";
import { CheckCircle, XCircle, MessageSquare, Clock, Shield, User, ChevronRight, X } from "lucide-react";

export default function InboxPage() {
  const qc = useQueryClient();
  const [activeModal, setActiveModal] = useState<{ type: string; id: string; instanceId: string } | null>(null);
  const [comment, setComment] = useState("");

  const { data: inbox = [], isLoading } = useQuery({
    queryKey: ["inbox"],
    queryFn: () => api.get("/inbox").then(r => r.data),
    refetchInterval: 10000,
  });

  const taskMutation = useMutation({
    mutationFn: ({ taskId }: { taskId: string }) =>
      api.post(`/tasks/${taskId}/complete`, { data: {}, comment }),
    onSuccess: () => {
      toast.success("Görev tamamlandı"); qc.invalidateQueries({ queryKey: ["inbox"] }); setActiveModal(null);
    },
  });

  const approvalMutation = useMutation({
    mutationFn: ({ approvalId, decision }: { approvalId: string; decision: string }) =>
      api.post(`/approvals/${approvalId}/decide`, { decision, comment }),
    onSuccess: () => {
      toast.success("Karar verildi"); qc.invalidateQueries({ queryKey: ["inbox"] }); setActiveModal(null);
    },
  });

  const tasks = inbox.filter((i: { type: string }) => i.type === "task");
  const approvals = inbox.filter((i: { type: string }) => i.type === "approval");

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-5">
        <h2 className="text-base font-semibold text-accent">Onaylarım</h2>
        <p className="text-xs text-accent-muted mt-0.5">{inbox.length} bekleyen öğe</p>
      </div>

      {/* Approvals */}
      {approvals.length > 0 && (
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-accent-muted uppercase tracking-wide mb-3">Onay Bekleyen ({approvals.length})</h3>
          <div className="space-y-2">
            {approvals.map((item: { id: string; title: string; instance_id: string; instance_title: string; amount?: number; approver_role?: string; created_at: string }) => (
              <div key={item.id} className="card p-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-warning-soft flex items-center justify-center flex-shrink-0">
                  <Shield size={15} className="text-warning" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-accent truncate">{item.title}</div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <Link href={`/processes/${item.instance_id}`} className="text-xs text-accent-muted hover:text-accent truncate">{item.instance_title}</Link>
                    {item.amount && <span className="text-xs font-medium text-accent-muted">{item.amount.toLocaleString("tr-TR")} ₺</span>}
                    <span className="text-xs text-accent-muted">{formatRelative(item.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    className="btn btn-sm bg-success text-white hover:bg-green-600"
                    onClick={() => setActiveModal({ type: "approval", id: item.id, instanceId: item.instance_id })}
                  >
                    Karar Ver
                  </button>
                  <Link href={`/processes/${item.instance_id}`}>
                    <button className="btn-icon btn-secondary"><ChevronRight size={14} /></button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tasks */}
      {tasks.length > 0 && (
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-accent-muted uppercase tracking-wide mb-3">Görevler ({tasks.length})</h3>
          <div className="space-y-2">
            {tasks.map((item: { id: string; title: string; task_type: string; instance_id: string; instance_title: string; created_at: string }) => (
              <div key={item.id} className="card p-4 flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-info-soft flex items-center justify-center flex-shrink-0">
                  <User size={15} className="text-info" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-accent truncate">{item.title}</div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <Link href={`/processes/${item.instance_id}`} className="text-xs text-accent-muted hover:text-accent truncate">{item.instance_title}</Link>
                    <span className="text-xs text-accent-muted">{formatRelative(item.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    className="btn-primary btn-sm"
                    onClick={() => setActiveModal({ type: "task", id: item.id, instanceId: item.instance_id })}
                  >
                    <CheckCircle size={13} /> Tamamla
                  </button>
                  <Link href={`/processes/${item.instance_id}`}>
                    <button className="btn-icon btn-secondary"><ChevronRight size={14} /></button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {inbox.length === 0 && !isLoading && (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-success-soft flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={24} className="text-success" />
          </div>
          <div className="text-base font-semibold text-accent">Bekleyen öğe yok</div>
          <div className="text-sm text-accent-muted mt-1">Tüm görev ve onaylar tamamlandı.</div>
        </div>
      )}

      {/* Modal */}
      {activeModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-5 border-b border-border">
              <h3 className="text-sm font-semibold text-accent">
                {activeModal.type === "approval" ? "Onay Kararı Ver" : "Görevi Tamamla"}
              </h3>
              <button onClick={() => setActiveModal(null)} className="btn-icon text-accent-muted"><X size={16} /></button>
            </div>
            <div className="px-6 py-5">
              <label className="label mb-1.5 block">Yorum (opsiyonel)</label>
              <textarea className="input resize-none" rows={3} value={comment} onChange={e => setComment(e.target.value)} placeholder="Yorumunuzu yazın..." />
            </div>
            <div className="px-6 pb-5 flex gap-2">
              {activeModal.type === "approval" ? (
                <>
                  <button className="btn flex-1 bg-success text-white hover:bg-green-600" onClick={() => approvalMutation.mutate({ approvalId: activeModal.id, decision: "approved" })}>
                    <CheckCircle size={13} /> Onayla
                  </button>
                  <button className="btn flex-1 bg-warning text-white hover:bg-amber-600" onClick={() => approvalMutation.mutate({ approvalId: activeModal.id, decision: "revision_requested" })}>
                    Revizyon
                  </button>
                  <button className="btn-destructive flex-1" onClick={() => approvalMutation.mutate({ approvalId: activeModal.id, decision: "rejected" })}>
                    <XCircle size={13} /> Reddet
                  </button>
                </>
              ) : (
                <>
                  <button className="btn-secondary flex-1" onClick={() => setActiveModal(null)}>İptal</button>
                  <button className="btn-primary flex-1" onClick={() => taskMutation.mutate({ taskId: activeModal.id })}>
                    <CheckCircle size={13} /> Tamamla
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
