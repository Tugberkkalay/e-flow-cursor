"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft, Clock, User, CheckCircle, XCircle, AlertTriangle, FileText, MessageSquare,
  RotateCcw, SkipForward, UserX, Trash2, Play, ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { formatDate, statusColor, formatCurrency } from "@/lib/utils";

const INSTANCE = {
  id: "inst_1",
  title: "PR-2024-0847",
  flow_name: "Satın Alma Talebi",
  status: "running",
  requester: "Ahmet Yılmaz",
  department: "IT",
  started_at: "2024-03-12T09:30:00Z",
  variables: {
    "form.title": "Dizüstü Bilgisayar Alımı",
    "form.request_type": "Mal Alımı",
    "form.quantity": 10,
    "form.unit_price": 35000,
    "form.vat_rate": 20,
    "form.currency": "TRY",
    "calc.total_amount": 420000,
    "docs.offers_count": 3,
  },
};

const TIMELINE_EVENTS = [
  { id: "ev1", type: "instance_started", message: "Süreç başlatıldı", user: "Ahmet Yılmaz", timestamp: "2024-03-12T09:30:00Z", icon: Play, color: "text-blue-500" },
  { id: "ev2", type: "node_started", message: "Form Gönderim tetiklendi", user: "Sistem", timestamp: "2024-03-12T09:30:01Z", icon: ChevronRight, color: "text-gray-400" },
  { id: "ev3", type: "node_completed", message: "PR Formu dolduruldu", user: "Ahmet Yılmaz", timestamp: "2024-03-12T09:45:00Z", icon: CheckCircle, color: "text-emerald-500" },
  { id: "ev4", type: "node_completed", message: "Toplam hesaplandı: ₺420.000", user: "Sistem", timestamp: "2024-03-12T09:45:01Z", icon: CheckCircle, color: "text-emerald-500" },
  { id: "ev5", type: "gateway_evaluated", message: "Koşul: Tutar >= 50K → Evet", user: "Sistem", timestamp: "2024-03-12T09:45:02Z", icon: ChevronRight, color: "text-amber-500" },
  { id: "ev6", type: "task_created", message: "Teklif Yükle görevi oluşturuldu", user: "Sistem", timestamp: "2024-03-12T09:45:03Z", icon: FileText, color: "text-blue-500" },
  { id: "ev7", type: "document_uploaded", message: "3 teklif dokümanı yüklendi", user: "Ahmet Yılmaz", timestamp: "2024-03-12T10:30:00Z", icon: FileText, color: "text-violet-500" },
  { id: "ev8", type: "node_completed", message: "AI Teklif Çıkarımı tamamlandı", user: "Sistem", timestamp: "2024-03-12T10:30:05Z", icon: CheckCircle, color: "text-emerald-500" },
  { id: "ev9", type: "node_completed", message: "Para normalize edildi (TRY)", user: "Sistem", timestamp: "2024-03-12T10:30:06Z", icon: CheckCircle, color: "text-emerald-500" },
  { id: "ev10", type: "node_completed", message: "Politika kontrolü: Geçti", user: "Sistem", timestamp: "2024-03-12T10:30:07Z", icon: CheckCircle, color: "text-emerald-500" },
  { id: "ev11", type: "approval_pending", message: "Onay bekleniyor: Limit Matrisi (Finans Direktörü)", user: "Sistem", timestamp: "2024-03-12T10:30:08Z", icon: Clock, color: "text-amber-500" },
];

const TASKS = [
  { id: "t1", title: "PR Formu Doldur", assignee: "Ahmet Yılmaz", status: "completed", completed_at: "2024-03-12T09:45:00Z" },
  { id: "t2", title: "Teklif Yükle (min 2)", assignee: "Ahmet Yılmaz", status: "completed", completed_at: "2024-03-12T10:30:00Z" },
];

const APPROVALS = [
  { id: "a1", title: "Limit Matrisli Onay", approver: "Finans Direktörü", status: "pending", amount: 420000 },
];

const DOCUMENTS = [
  { id: "d1", name: "Teklif_CompanyA.pdf", type: "offer", version: 1, uploaded_at: "2024-03-12T10:25:00Z" },
  { id: "d2", name: "Teklif_CompanyB.pdf", type: "offer", version: 1, uploaded_at: "2024-03-12T10:26:00Z" },
  { id: "d3", name: "Teklif_CompanyC.pdf", type: "offer", version: 1, uploaded_at: "2024-03-12T10:27:00Z" },
];

export default function InstanceDetailPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/processes">
              <Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="h-4 w-4" /></Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold">{INSTANCE.title}</h1>
                <Badge variant="outline" className={statusColor(INSTANCE.status)}>İşlemde</Badge>
              </div>
              <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground">
                <span>{INSTANCE.flow_name}</span>
                <span>&middot;</span>
                <span className="flex items-center gap-1"><User className="h-3 w-3" />{INSTANCE.requester}</span>
                <span>&middot;</span>
                <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{formatDate(INSTANCE.started_at)}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs"><UserX className="h-3.5 w-3.5" />Yeniden Ata</Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs"><SkipForward className="h-3.5 w-3.5" />Adım Atla</Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs text-red-600 hover:text-red-700"><Trash2 className="h-3.5 w-3.5" />İptal Et</Button>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs"><RotateCcw className="h-3.5 w-3.5" />Yeniden Dene</Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="timeline">
          <TabsList>
            <TabsTrigger value="timeline">Zaman Çizelgesi</TabsTrigger>
            <TabsTrigger value="tasks">Görevler</TabsTrigger>
            <TabsTrigger value="approvals">Onaylar</TabsTrigger>
            <TabsTrigger value="form">Form Verileri</TabsTrigger>
            <TabsTrigger value="documents">Dokümanlar</TabsTrigger>
            <TabsTrigger value="controls">Kontroller</TabsTrigger>
          </TabsList>

          <TabsContent value="timeline">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="space-y-0">
                  {TIMELINE_EVENTS.map((event, idx) => {
                    const Icon = event.icon;
                    return (
                      <div key={event.id} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className={`flex h-8 w-8 items-center justify-center rounded-full bg-white border-2 ${
                            event.type === "approval_pending" ? "border-amber-300" :
                            event.type.includes("completed") ? "border-emerald-300" : "border-gray-200"
                          }`}>
                            <Icon className={`h-4 w-4 ${event.color}`} strokeWidth={1.8} />
                          </div>
                          {idx < TIMELINE_EVENTS.length - 1 && (
                            <div className="w-0.5 flex-1 bg-gray-100 my-1 min-h-[24px]" />
                          )}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="text-sm font-medium">{event.message}</span>
                              <div className="text-xs text-muted-foreground mt-0.5">{event.user}</div>
                            </div>
                            <span className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tasks">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Görev</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Atanan</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Durum</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Tamamlanma</th>
                  </tr></thead>
                  <tbody>
                    {TASKS.map((task) => (
                      <tr key={task.id} className="border-b last:border-0">
                        <td className="px-4 py-3 text-sm font-medium">{task.title}</td>
                        <td className="px-4 py-3 text-sm">{task.assignee}</td>
                        <td className="px-4 py-3"><Badge variant="outline" className={statusColor(task.status)}>{task.status === "completed" ? "Tamamlandı" : "Beklemede"}</Badge></td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">{task.completed_at ? formatDate(task.completed_at) : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="approvals">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Onay</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Onaylayan</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Tutar</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Durum</th>
                  </tr></thead>
                  <tbody>
                    {APPROVALS.map((appr) => (
                      <tr key={appr.id} className="border-b last:border-0">
                        <td className="px-4 py-3 text-sm font-medium">{appr.title}</td>
                        <td className="px-4 py-3 text-sm">{appr.approver}</td>
                        <td className="px-4 py-3 text-sm font-medium">{formatCurrency(appr.amount)}</td>
                        <td className="px-4 py-3"><Badge variant="outline" className={statusColor(appr.status)}>Beklemede</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="form">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(INSTANCE.variables).map(([key, value]) => (
                    <div key={key} className="rounded-lg bg-gray-50 px-4 py-3">
                      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-1">{key}</div>
                      <div className="text-sm font-medium">
                        {typeof value === "number" && key.includes("amount") ? formatCurrency(value) : String(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Dosya</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Tip</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Versiyon</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase">Yükleme</th>
                  </tr></thead>
                  <tbody>
                    {DOCUMENTS.map((doc) => (
                      <tr key={doc.id} className="border-b last:border-0">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" /><span className="text-sm font-medium">{doc.name}</span></div>
                        </td>
                        <td className="px-4 py-3"><Badge variant="outline">{doc.type}</Badge></td>
                        <td className="px-4 py-3 text-sm">v{doc.version}</td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">{formatDate(doc.uploaded_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="controls">
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                      <span className="text-sm font-semibold text-amber-800">Bayraklar & Kontroller</span>
                    </div>
                    <div className="text-sm text-amber-700">Bu süreç için henüz bayrak veya uyumsuzluk bulunmuyor.</div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-lg bg-gray-50 p-4">
                      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-2">Politika Kontrolü</div>
                      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">Geçti</Badge>
                    </div>
                    <div className="rounded-lg bg-gray-50 p-4">
                      <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-2">3-Way Match</div>
                      <span className="text-sm text-muted-foreground">Henüz uygulanmadı</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}
