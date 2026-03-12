"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Download, Search, Shield, Filter } from "lucide-react";
import { formatDate } from "@/lib/utils";

const AUDIT_EVENTS = [
  { id: "ae1", type: "instance_started", instance: "PR-2024-0847", user: "Ahmet Yılmaz", detail: "Süreç başlatıldı", timestamp: "2024-03-12T09:30:00Z" },
  { id: "ae2", type: "task_completed", instance: "PR-2024-0847", user: "Ahmet Yılmaz", detail: "Form dolduruldu", timestamp: "2024-03-12T09:45:00Z" },
  { id: "ae3", type: "document_uploaded", instance: "PR-2024-0847", user: "Ahmet Yılmaz", detail: "3 doküman yüklendi", timestamp: "2024-03-12T10:30:00Z" },
  { id: "ae4", type: "approval_requested", instance: "PR-2024-0847", user: "Sistem", detail: "Onay talebi: Finans Direktörü", timestamp: "2024-03-12T10:30:08Z" },
  { id: "ae5", type: "approval_decided", instance: "PO-2024-0234", user: "Mehmet Demir", detail: "Onaylandı: ₺156.000", timestamp: "2024-03-11T16:00:00Z" },
  { id: "ae6", type: "instance_completed", instance: "PO-2024-0234", user: "Sistem", detail: "Süreç tamamlandı", timestamp: "2024-03-11T16:30:00Z" },
  { id: "ae7", type: "flow_published", instance: "—", user: "Admin", detail: "Sözleşme Süreci v2 yayınlandı", timestamp: "2024-03-10T08:00:00Z" },
  { id: "ae8", type: "user_created", instance: "—", user: "Admin", detail: "Kullanıcı eklendi: Fatma Ak", timestamp: "2024-03-09T10:00:00Z" },
  { id: "ae9", type: "delegation_created", instance: "—", user: "Mehmet Demir", detail: "Vekalet: Ahmet Yılmaz (15-22 Mart)", timestamp: "2024-03-08T09:00:00Z" },
  { id: "ae10", type: "instance_cancelled", instance: "CNT-2024-0090", user: "Admin", detail: "Süreç iptal edildi", timestamp: "2024-03-07T11:00:00Z" },
];

const TYPE_LABELS: Record<string, string> = {
  instance_started: "Süreç Başlatıldı",
  task_completed: "Görev Tamamlandı",
  document_uploaded: "Doküman Yüklendi",
  approval_requested: "Onay Talep Edildi",
  approval_decided: "Onay Kararı",
  instance_completed: "Süreç Tamamlandı",
  flow_published: "Akış Yayınlandı",
  user_created: "Kullanıcı Eklendi",
  delegation_created: "Vekalet Oluşturuldu",
  instance_cancelled: "Süreç İptal Edildi",
};

const TYPE_COLORS: Record<string, string> = {
  instance_started: "bg-blue-50 text-blue-700 border-blue-200",
  task_completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  document_uploaded: "bg-violet-50 text-violet-700 border-violet-200",
  approval_requested: "bg-amber-50 text-amber-700 border-amber-200",
  approval_decided: "bg-emerald-50 text-emerald-700 border-emerald-200",
  instance_completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  flow_published: "bg-blue-50 text-blue-700 border-blue-200",
  user_created: "bg-gray-50 text-gray-600 border-gray-200",
  delegation_created: "bg-orange-50 text-orange-700 border-orange-200",
  instance_cancelled: "bg-red-50 text-red-700 border-red-200",
};

export default function AuditPage() {
  const [search, setSearch] = useState("");
  const filtered = AUDIT_EVENTS.filter((e) =>
    e.detail.toLowerCase().includes(search.toLowerCase()) ||
    e.user.toLowerCase().includes(search.toLowerCase()) ||
    e.instance.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Denetim Günlüğü</h1>
            <p className="text-sm text-muted-foreground mt-1">Tüm sistem olayları (silinemez)</p>
          </div>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Download className="h-4 w-4" />CSV İndir
          </Button>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Olay, kullanıcı veya süreç ara..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <Button variant="outline" size="sm" className="gap-1.5"><Filter className="h-3.5 w-3.5" />Filtre</Button>
        </div>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            <table className="w-full">
              <thead><tr className="border-b bg-gray-50/50">
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Zaman</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Tip</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Süreç</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Kullanıcı</th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Detay</th>
              </tr></thead>
              <tbody>
                {filtered.map((event) => (
                  <tr key={event.id} className="border-b last:border-0 hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">{formatDate(event.timestamp)}</td>
                    <td className="px-4 py-3"><Badge variant="outline" className={TYPE_COLORS[event.type]}>{TYPE_LABELS[event.type]}</Badge></td>
                    <td className="px-4 py-3 text-sm font-medium">{event.instance}</td>
                    <td className="px-4 py-3 text-sm">{event.user}</td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">{event.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Shield className="h-3.5 w-3.5" />
          <span>Denetim kayıtları değiştirilemez ve silinemez (immutable audit log)</span>
        </div>
      </div>
    </AppShell>
  );
}
