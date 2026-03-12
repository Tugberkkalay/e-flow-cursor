"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Search, Clock, User, ArrowRight, Play } from "lucide-react";
import { formatDate, statusColor } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { FLOW_TEMPLATES } from "@/lib/templates";

const DEMO_INSTANCES = [
  { id: "inst_1", title: "PR-2024-0847", flow_name: "Satın Alma Talebi", status: "running", current_step: "Limit Matrisli Onay", requester: "Ahmet Yılmaz", sla: "4s 12dk", started_at: "2024-03-12T09:30:00Z" },
  { id: "inst_2", title: "PO-2024-0234", flow_name: "Satın Alma Süreci", status: "completed", current_step: "Tamamlandı", requester: "Mehmet Demir", sla: "—", started_at: "2024-03-11T14:00:00Z" },
  { id: "inst_3", title: "CNT-2024-0091", flow_name: "Sözleşme Süreci", status: "running", current_step: "Hukuk İnceleme", requester: "Ayşe Kara", sla: "2g 3s", started_at: "2024-03-10T08:00:00Z" },
  { id: "inst_4", title: "INV-2024-0562", flow_name: "Fatura/Ödeme", status: "pending", current_step: "Fatura Eşleşme", requester: "Fatma Ak", sla: "6s", started_at: "2024-03-10T16:00:00Z" },
  { id: "inst_5", title: "PR-2024-0846", flow_name: "Satın Alma Talebi", status: "rejected", current_step: "Reddedildi", requester: "Ali Veli", sla: "—", started_at: "2024-03-09T11:00:00Z" },
  { id: "inst_6", title: "PR-2024-0845", flow_name: "Satın Alma Talebi", status: "completed", current_step: "Tamamlandı", requester: "Zeynep Demir", sla: "—", started_at: "2024-03-08T09:00:00Z" },
  { id: "inst_7", title: "CNT-2024-0090", flow_name: "Sözleşme Süreci", status: "cancelled", current_step: "İptal Edildi", requester: "Can Bey", sla: "—", started_at: "2024-03-07T10:00:00Z" },
  { id: "inst_8", title: "PO-2024-0233", flow_name: "Satın Alma Süreci", status: "failed", current_step: "ERP Entegrasyon Hatası", requester: "Duygu Han", sla: "—", started_at: "2024-03-06T15:00:00Z" },
];

const STATUS_LABELS: Record<string, string> = {
  all: "Tümü",
  running: "İşlemde",
  completed: "Tamamlandı",
  pending: "Beklemede",
  rejected: "Reddedildi",
  cancelled: "İptal",
  failed: "Hata",
};

export default function ProcessesPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showStart, setShowStart] = useState(false);

  const filtered = DEMO_INSTANCES.filter((inst) => {
    const matchSearch = inst.title.toLowerCase().includes(search.toLowerCase()) || inst.flow_name.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || inst.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Süreçler</h1>
            <p className="text-sm text-muted-foreground mt-1">Tüm süreç örnekleri</p>
          </div>
          <Dialog open={showStart} onOpenChange={setShowStart}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1.5"><Play className="h-4 w-4" />Süreç Başlat</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Süreç Başlat</DialogTitle>
                <DialogDescription>Yayındaki bir akışı seçerek yeni süreç başlatın</DialogDescription>
              </DialogHeader>
              <div className="space-y-2 py-2">
                {FLOW_TEMPLATES.map((tpl) => (
                  <button
                    key={tpl.id}
                    className="flex items-center justify-between w-full rounded-lg border p-3 hover:bg-gray-50 transition-colors text-left"
                    onClick={() => { setShowStart(false); router.push(`/processes/new?template=${tpl.id}`); }}
                  >
                    <div>
                      <div className="text-sm font-medium">{tpl.name}</div>
                      <div className="text-xs text-muted-foreground">{tpl.description}</div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Süreç ara..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <Tabs value={statusFilter} onValueChange={setStatusFilter}>
            <TabsList>
              {Object.entries(STATUS_LABELS).map(([key, label]) => (
                <TabsTrigger key={key} value={key} className="text-xs">{label}</TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* Table */}
        <Card className="border-0 shadow-sm">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Başlık</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Akış</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Talep Eden</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Durum</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Aktif Adım</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">SLA</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Tarih</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((inst) => (
                    <tr
                      key={inst.id}
                      className="border-b last:border-0 hover:bg-gray-50/50 cursor-pointer transition-colors"
                      onClick={() => router.push(`/processes/${inst.id}`)}
                    >
                      <td className="px-4 py-3 text-sm font-medium">{inst.title}</td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">{inst.flow_name}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100">
                            <User className="h-3 w-3 text-gray-500" />
                          </div>
                          <span className="text-sm">{inst.requester}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className={statusColor(inst.status)}>
                          {STATUS_LABELS[inst.status] || inst.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">{inst.current_step}</td>
                      <td className="px-4 py-3">
                        <span className={`text-sm ${inst.sla !== "—" ? "font-medium" : "text-muted-foreground"}`}>{inst.sla}</span>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(inst.started_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
