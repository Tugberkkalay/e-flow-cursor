import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("tr-TR", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function formatRelative(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  if (diff < 60000) return "az önce";
  if (diff < 3600000) return `${Math.floor(diff / 60000)} dk önce`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} sa önce`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} gün önce`;
  return new Date(dateStr).toLocaleDateString("tr-TR");
}

export function formatMoney(amount: number | null | undefined, currency = "TRY"): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("tr-TR", {
    style: "currency", currency, minimumFractionDigits: 0, maximumFractionDigits: 2,
  }).format(amount);
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    running: "badge-info",
    completed: "badge-success",
    rejected: "badge-error",
    cancelled: "badge-neutral",
    failed: "badge-error",
    waiting: "badge-warning",
    pending: "badge-warning",
    approved: "badge-success",
    draft: "badge-neutral",
    published: "badge-success",
    archived: "badge-neutral",
    decided: "badge-info",
  };
  return map[status] || "badge-neutral";
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    running: "Çalışıyor",
    completed: "Tamamlandı",
    rejected: "Reddedildi",
    cancelled: "İptal",
    failed: "Başarısız",
    waiting: "Bekliyor",
    pending: "Bekliyor",
    approved: "Onaylandı",
    draft: "Taslak",
    published: "Yayında",
    archived: "Arşiv",
    decided: "Karar Verildi",
    skipped: "Atlandı",
    revision_requested: "Revizyon",
  };
  return map[status] || status;
}

export function nodeTypeColor(engineType: string): { bg: string; border: string; text: string } {
  if (["ManualStart", "FormSubmitTrigger", "APITrigger", "ScheduledTrigger", "MessageTrigger"].includes(engineType)) {
    return { bg: "bg-node-trigger", border: "border-node-trigger-border", text: "text-indigo-700" };
  }
  if (["HumanTask", "FormFill", "DataEntry", "DocumentUpload", "ReviewComment", "VendorSelection", "DeliveryAcceptance", "ReworkTask", "ManualCompensation"].includes(engineType)) {
    return { bg: "bg-node-human", border: "border-node-human-border", text: "text-green-700" };
  }
  if (["ApprovalTask", "Approval", "MultiApproval", "ApprovalByLimitMatrix"].includes(engineType)) {
    return { bg: "bg-node-approval", border: "border-node-approval-border", text: "text-yellow-700" };
  }
  if (["Gateway", "IF", "Switch", "ParallelSplit", "ParallelJoin"].includes(engineType)) {
    return { bg: "bg-node-logic", border: "border-node-logic-border", text: "text-purple-700" };
  }
  if (["ServiceTask", "HTTPRequest", "EmailSend", "ERPAdapter", "SubprocessCall"].includes(engineType)) {
    return { bg: "bg-node-integration", border: "border-node-integration-border", text: "text-red-700" };
  }
  if (["ScriptTask", "Calculate", "SetFields", "Transform", "ThreeWayMatch", "NormalizeMoney", "PolicyCheck", "ScriptTask"].includes(engineType)) {
    return { bg: "bg-node-data", border: "border-node-data-border", text: "text-sky-700" };
  }
  if (["AuditEmit", "StopError", "PolicyCheck"].includes(engineType)) {
    return { bg: "bg-node-compliance", border: "border-node-compliance-border", text: "text-orange-700" };
  }
  return { bg: "bg-node-event", border: "border-node-event-border", text: "text-slate-600" };
}
