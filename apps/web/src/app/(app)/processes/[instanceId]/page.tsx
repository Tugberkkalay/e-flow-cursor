"use client";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { formatDate, formatRelative, statusColor, statusLabel } from "@/lib/utils";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle, XCircle, RefreshCw, SkipForward, X, AlertTriangle, Clock, User, FileText, Shield } from "lucide-react";
import Link from "next/link";

const TABS = [
  { id: "timeline", label: "Zaman Çizelgesi" },
  { id: "tasks", label: "Görevler" },
  { id: "approvals", label: "Onaylar" },
  { id: "form", label: "Form Verisi" },
  { id: "documents", label: "Belgeler" },
];

export default function InstanceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const qc = useQueryClient();
  const instanceId = params.instanceId as string;
  const [activeTab, setActiveTab] = useState("timeline");
  const [showApproveModal, setShowApproveModal] = useState<{ type: string; taskId?: string; approvalId?: string } | null>(null);
  const [comment, setComment] = useState("");

  const { data: instance, isLoading } = useQuery({
    queryKey: ["instance", instanceId],
    queryFn: () => api.get(`/instances/${instanceId}`).then(r => r.data),
    refetchInterval: 5000,
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ["timeline", instanceId],
    queryFn: () => api.get(`/instances/${instanceId}/timeline`).then(r => r.data),
    refetchInterval: 5000,
  });

  const actionMutation = useMutation({
    mutationFn: ({ action, payload }: { action: string; payload?: object }) =>
      api.post(`/instances/${instanceId}/actions`, { action, payload: payload || {}, comment }),
    onSuccess: () => {
      toast.success("İşlem gerçekleştirildi");
      qc.invalidateQueries({ queryKey: ["instance", instanceId] });
      qc.invalidateQueries({ queryKey: ["timeline", instanceId] });
      setShowApproveModal(null);
      setComment("");
    },
    onError: () => toast.error("İşlem başarısız"),
  });

  const taskMutation = useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: object }) =>
      api.post(`/tasks/${taskId}/complete`, { data, comment }),
    onSuccess: () => {
      toast.success("Görev tamamlandı");
      qc.invalidateQueries({ queryKey: ["instance", instanceId] });
      qc.invalidateQueries({ queryKey: ["timeline", instanceId] });
      setShowApproveModal(null);
    },
    onError: () => toast.error("Görev tamamlanamadı"),
  });

  const approvalMutation = useMutation({
    mutationFn: ({ approvalId, decision }: { approvalId: string; decision: string }) =>
      api.post(`/approvals/${approvalId}/decide`, { decision, comment }),
    onSuccess: () => {
      toast.success("Onay kararı verildi");
      qc.invalidateQueries({ queryKey: ["instance", instanceId] });
      qc.invalidateQueries({ queryKey: ["timeline", instanceId] });
      qc.invalidateQueries({ queryKey: ["inbox"] });
      setShowApproveModal(null);
    },
    onError: () => toast.error("Karar verilemedi"),
  });

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!instance) {
    return <div className="p-6 text-sm text-accent-muted">Süreç bulunamadı.</div>;
  }

  const pendingTasks = instance.tasks?.filter((t: { status: string }) => t.status === "pending") || [];
  const pendingApprovals = instance.approvals?.filter((a: { status: string }) => a.status === "pending") || [];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-3">
          <Link href="/processes">
            <button className="btn-icon btn-secondary mt-0.5"><ArrowLeft size={15} /></button>
          </Link>
          <div>
            <h2 className="text-base font-semibold text-accent">{instance.title}</h2>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-accent-muted">{instance.definition_name}</span>
              <span className={`badge ${statusColor(instance.status)}`}>{statusLabel(instance.status)}</span>
              <span className="text-xs text-accent-muted">{formatRelative(instance.started_at)}</span>
            </div>
          </div>
        </div>

        {/* Admin actions */}
        {instance.status === "running" && (
          <div className="flex items-center gap-2">
            <button className="btn-secondary btn-sm" onClick={() => actionMutation.mutate({ action: "retry" })}>
              <RefreshCw size={12} /> Tekrar Dene
            </button>
            <button className="btn-secondary btn-sm" onClick={() => actionMutation.mutate({ action: "skip" })}>
              <SkipForward size={12} /> Adım Atla
            </button>
            <button className="btn-destructive btn-sm" onClick={() => { if (confirm("İptal edilsin mi?")) actionMutation.mutate({ action: "cancel" }); }}>
              <X size={12} /> İptal
            </button>
          </div>
        )}
      </div>

      {/* Action banners */}
      {pendingTasks.length > 0 && (
        <div className="mb-4 border border-info/30 bg-info-soft rounded-xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-info" />
            <span className="text-sm font-medium text-accent">{pendingTasks.length} bekleyen görev</span>
            <span className="text-xs text-accent-muted">— Aktif adım: <strong>{instance.current_node_id}</strong></span>
          </div>
          <button
            className="btn-primary btn-sm"
            onClick={() => setShowApproveModal({ type: "task", taskId: pendingTasks[0].id })}
          >
            Görevi Tamamla
          </button>
        </div>
      )}

      {pendingApprovals.length > 0 && (
        <div className="mb-4 border border-warning/30 bg-warning-soft rounded-xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="text-warning" />
            <span className="text-sm font-medium text-accent">{pendingApprovals.length} bekleyen onay</span>
            <span className="text-xs text-accent-muted">— {pendingApprovals[0].approver_role}</span>
          </div>
          <button
            className="btn-primary btn-sm"
            onClick={() => setShowApproveModal({ type: "approval", approvalId: pendingApprovals[0].id })}
          >
            Karar Ver
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-border mb-4">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id
                ? "border-accent text-accent"
                : "border-transparent text-accent-muted hover:text-accent"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "timeline" && (
        <TimelineTab timeline={timeline} />
      )}

      {activeTab === "tasks" && (
        <TasksTab tasks={instance.tasks || []} nodeInstances={instance.node_instances || []} />
      )}

      {activeTab === "approvals" && (
        <ApprovalsTab approvals={instance.approvals || []} />
      )}

      {activeTab === "form" && (
        <FormTab variables={instance.variables || {}} exports={instance.exports || {}} />
      )}

      {activeTab === "documents" && (
        <DocumentsTab documents={instance.documents || []} />
      )}

      {/* Action Modal */}
      {showApproveModal && (
        <ActionModal
          type={showApproveModal.type}
          comment={comment}
          onCommentChange={setComment}
          onClose={() => setShowApproveModal(null)}
          onApprove={() => {
            if (showApproveModal.type === "approval" && showApproveModal.approvalId) {
              approvalMutation.mutate({ approvalId: showApproveModal.approvalId, decision: "approved" });
            } else if (showApproveModal.type === "task" && showApproveModal.taskId) {
              taskMutation.mutate({ taskId: showApproveModal.taskId, data: {} });
            }
          }}
          onReject={() => {
            if (showApproveModal.type === "approval" && showApproveModal.approvalId) {
              approvalMutation.mutate({ approvalId: showApproveModal.approvalId, decision: "rejected" });
            }
          }}
          onRevision={() => {
            if (showApproveModal.type === "approval" && showApproveModal.approvalId) {
              approvalMutation.mutate({ approvalId: showApproveModal.approvalId, decision: "revision_requested" });
            }
          }}
          loading={approvalMutation.isPending || taskMutation.isPending}
        />
      )}
    </div>
  );
}

function TimelineTab({ timeline }: { timeline: { id: string; event_type: string; actor_name?: string; payload: Record<string, unknown>; created_at: string }[] }) {
  const EVENT_ICONS: Record<string, React.ReactNode> = {
    "instance.started": <div className="w-7 h-7 rounded-full bg-info-soft flex items-center justify-center"><Clock size={13} className="text-info" /></div>,
    "instance.completed": <div className="w-7 h-7 rounded-full bg-success-soft flex items-center justify-center"><CheckCircle size={13} className="text-success" /></div>,
    "instance.failed": <div className="w-7 h-7 rounded-full bg-destructive-soft flex items-center justify-center"><XCircle size={13} className="text-destructive" /></div>,
    "instance.cancelled": <div className="w-7 h-7 rounded-full bg-secondary flex items-center justify-center"><X size={13} className="text-accent-muted" /></div>,
    "task.created": <div className="w-7 h-7 rounded-full bg-warning-soft flex items-center justify-center"><User size={13} className="text-warning" /></div>,
    "task.completed": <div className="w-7 h-7 rounded-full bg-success-soft flex items-center justify-center"><CheckCircle size={13} className="text-success" /></div>,
    "approval.requested": <div className="w-7 h-7 rounded-full bg-warning-soft flex items-center justify-center"><Shield size={13} className="text-warning" /></div>,
    "approval.approved": <div className="w-7 h-7 rounded-full bg-success-soft flex items-center justify-center"><CheckCircle size={13} className="text-success" /></div>,
    "approval.rejected": <div className="w-7 h-7 rounded-full bg-destructive-soft flex items-center justify-center"><XCircle size={13} className="text-destructive" /></div>,
  };

  const EVENT_LABELS: Record<string, string> = {
    "instance.started": "Süreç başlatıldı",
    "instance.completed": "Süreç tamamlandı",
    "instance.failed": "Süreç başarısız",
    "instance.cancelled": "Süreç iptal edildi",
    "node.started": "Adım başladı",
    "node.completed": "Adım tamamlandı",
    "node.skipped": "Adım atlandı",
    "node.retry": "Adım tekrar denendi",
    "task.created": "Görev oluşturuldu",
    "task.completed": "Görev tamamlandı",
    "task.reassigned": "Görev yeniden atandı",
    "approval.requested": "Onay istendi",
    "approval.approved": "Onaylandı",
    "approval.rejected": "Reddedildi",
    "approval.revision_requested": "Revizyon istendi",
    "subprocess.called": "Alt süreç çağrıldı",
  };

  return (
    <div className="space-y-0">
      {timeline.length === 0 ? (
        <div className="text-center py-12 text-sm text-accent-muted">Henüz olay kaydı yok.</div>
      ) : (
        <div className="relative">
          <div className="absolute left-3.5 top-0 bottom-0 w-px bg-border" />
          <div className="space-y-0">
            {timeline.map((event, i) => (
              <div key={event.id} className="flex gap-3 relative pl-0 pb-4">
                <div className="flex-shrink-0 relative z-10">
                  {EVENT_ICONS[event.event_type] || (
                    <div className="w-7 h-7 rounded-full bg-secondary border border-border flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-accent-muted" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0 pt-0.5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-sm font-medium text-accent">
                        {EVENT_LABELS[event.event_type] || event.event_type}
                      </span>
                      {event.actor_name && (
                        <span className="text-xs text-accent-muted ml-2">· {event.actor_name}</span>
                      )}
                    </div>
                    <span className="text-xs text-accent-muted whitespace-nowrap flex-shrink-0">{formatRelative(event.created_at)}</span>
                  </div>
                  {Object.keys(event.payload || {}).length > 0 && (
                    <details className="mt-1">
                      <summary className="text-xs text-accent-muted cursor-pointer select-none hover:text-accent">Detaylar</summary>
                      <pre className="mt-1 text-[10px] font-mono text-accent-muted bg-muted rounded p-2 overflow-auto max-h-32">
                        {JSON.stringify(event.payload, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TasksTab({ tasks, nodeInstances }: { tasks: { id: string; title: string; task_type: string; status: string; assigned_to_name?: string; assigned_role?: string; comment?: string; created_at: string; completed_at?: string }[]; nodeInstances: { id: string; node_id: string; status: string; node_label?: string; duration_ms?: number }[] }) {
  return (
    <div className="space-y-2">
      {nodeInstances.map(ni => (
        <div key={ni.id} className="card p-4 flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
            ni.status === "completed" ? "bg-success" : ni.status === "running" ? "bg-info" : ni.status === "skipped" ? "bg-accent-muted" : "bg-border"
          }`} />
          <div className="flex-1">
            <span className="text-sm font-medium text-accent">{ni.node_label || ni.node_id}</span>
            <span className={`ml-2 badge text-[10px] ${statusColor(ni.status)}`}>{statusLabel(ni.status)}</span>
          </div>
          {ni.duration_ms && (
            <span className="text-xs text-accent-muted">{ni.duration_ms}ms</span>
          )}
        </div>
      ))}
      {tasks.map(task => (
        <div key={task.id} className="card p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className={`badge text-[10px] ${statusColor(task.status)}`}>{statusLabel(task.status)}</span>
                <span className="text-sm font-medium text-accent">{task.title}</span>
              </div>
              <div className="text-xs text-accent-muted mt-1">
                {task.assigned_to_name || task.assigned_role || "Atanmamış"} · {formatRelative(task.created_at)}
              </div>
              {task.comment && <div className="text-xs text-accent-muted italic mt-1">"{task.comment}"</div>}
            </div>
          </div>
        </div>
      ))}
      {tasks.length === 0 && nodeInstances.length === 0 && (
        <div className="text-center py-12 text-sm text-accent-muted">Görev bulunamadı.</div>
      )}
    </div>
  );
}

function ApprovalsTab({ approvals }: { approvals: { id: string; node_id: string; status: string; decision?: string; approver_name?: string; approver_role?: string; amount?: number; comment?: string; created_at: string; decided_at?: string }[] }) {
  return (
    <div className="space-y-3">
      {approvals.length === 0 ? (
        <div className="text-center py-12 text-sm text-accent-muted">Onay bulunamadı.</div>
      ) : (
        approvals.map(a => (
          <div key={a.id} className="card p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`badge text-[10px] ${statusColor(a.decision || a.status)}`}>
                    {statusLabel(a.decision || a.status)}
                  </span>
                  <span className="text-sm font-medium text-accent">{a.approver_name || a.approver_role || "Onaylayıcı"}</span>
                </div>
                {a.amount && <div className="text-xs text-accent-muted">Tutar: <strong>{a.amount.toLocaleString("tr-TR")} ₺</strong></div>}
                {a.comment && <div className="text-xs text-accent-muted italic mt-1">"{a.comment}"</div>}
                <div className="text-xs text-accent-muted mt-1">
                  {formatRelative(a.decided_at || a.created_at)}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function FormTab({ variables, exports: exps }: { variables: Record<string, unknown>; exports: Record<string, unknown> }) {
  return (
    <div className="space-y-4">
      {Object.keys(exps).length > 0 && (
        <div className="card p-4">
          <h4 className="text-xs font-semibold text-accent-muted uppercase tracking-wide mb-3">Çıktılar (Exports)</h4>
          <div className="space-y-2">
            {Object.entries(exps).map(([k, v]) => (
              <div key={k} className="flex items-start gap-3">
                <span className="text-xs font-mono text-accent-muted w-32 flex-shrink-0">{k}</span>
                <span className="text-xs text-accent font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="card p-4">
        <h4 className="text-xs font-semibold text-accent-muted uppercase tracking-wide mb-3">Süreç Değişkenleri</h4>
        <pre className="text-[11px] font-mono text-accent overflow-auto max-h-96 bg-muted rounded-lg p-3">
          {JSON.stringify(variables, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function DocumentsTab({ documents }: { documents: { id: string; doc_type?: string; original_filename: string; version_number: number; extraction_status: string; created_at: string }[] }) {
  return (
    <div className="space-y-2">
      {documents.length === 0 ? (
        <div className="text-center py-12 text-sm text-accent-muted">Belge bulunamadı.</div>
      ) : (
        documents.map(doc => (
          <div key={doc.id} className="card p-4 flex items-center gap-3">
            <FileText size={16} className="text-accent-muted flex-shrink-0" />
            <div className="flex-1">
              <div className="text-sm font-medium text-accent">{doc.original_filename}</div>
              <div className="text-xs text-accent-muted">{doc.doc_type || "Genel"} · v{doc.version_number} · {formatRelative(doc.created_at)}</div>
            </div>
            <span className={`badge text-[10px] ${doc.extraction_status === "completed" ? "badge-success" : "badge-warning"}`}>
              {doc.extraction_status}
            </span>
          </div>
        ))
      )}
    </div>
  );
}

function ActionModal({ type, comment, onCommentChange, onClose, onApprove, onReject, onRevision, loading }: {
  type: string;
  comment: string;
  onCommentChange: (v: string) => void;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
  onRevision: () => void;
  loading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md animate-scale-in">
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h3 className="text-sm font-semibold text-accent">
            {type === "approval" ? "Onay Kararı" : "Görevi Tamamla"}
          </h3>
          <button onClick={onClose} className="btn-icon text-accent-muted"><X size={16} /></button>
        </div>
        <div className="px-6 py-5">
          <label className="label mb-1.5 block">Yorum (opsiyonel)</label>
          <textarea
            className="input resize-none"
            rows={3}
            placeholder="Kararınızla ilgili bir yorum ekleyin..."
            value={comment}
            onChange={e => onCommentChange(e.target.value)}
          />
        </div>
        <div className="px-6 pb-5 flex items-center gap-2">
          {type === "approval" ? (
            <>
              <button className="btn flex-1 bg-success text-white hover:bg-green-600" onClick={onApprove} disabled={loading}>
                <CheckCircle size={13} /> Onayla
              </button>
              <button className="btn flex-1 bg-warning text-white hover:bg-amber-600" onClick={onRevision} disabled={loading}>
                Revizyon
              </button>
              <button className="btn-destructive flex-1" onClick={onReject} disabled={loading}>
                <XCircle size={13} /> Reddet
              </button>
            </>
          ) : (
            <>
              <button className="btn-secondary flex-1" onClick={onClose}>İptal</button>
              <button className="btn-primary flex-1" onClick={onApprove} disabled={loading}>
                <CheckCircle size={13} /> Tamamla
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
