"use client";

import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ListChecks,
  CheckCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  Users,
  FileText,
  Workflow,
} from "lucide-react";

const stats = [
  { label: "Aktif Süreçler", value: "24", icon: ListChecks, trend: "+3", color: "text-blue-600", bg: "bg-blue-50" },
  { label: "Bekleyen Onaylar", value: "8", icon: Clock, trend: "+2", color: "text-amber-600", bg: "bg-amber-50" },
  { label: "Tamamlanan (Bu Ay)", value: "156", icon: CheckCircle, trend: "+12%", color: "text-emerald-600", bg: "bg-emerald-50" },
  { label: "SLA İhlali", value: "2", icon: AlertTriangle, trend: "-1", color: "text-red-600", bg: "bg-red-50" },
];

const recentProcesses = [
  { id: "1", title: "PR-2024-0847", flow: "Satın Alma Talebi", status: "running", step: "Onay Bekleniyor", requester: "Ahmet Yılmaz", date: "2024-03-12" },
  { id: "2", title: "PO-2024-0234", flow: "Satın Alma Süreci", status: "completed", step: "Tamamlandı", requester: "Mehmet Demir", date: "2024-03-11" },
  { id: "3", title: "CNT-2024-0091", flow: "Sözleşme Süreci", status: "running", step: "Hukuk İnceleme", requester: "Ayşe Kara", date: "2024-03-10" },
  { id: "4", title: "INV-2024-0562", flow: "Fatura/Ödeme", status: "pending", step: "Fatura Eşleşme", requester: "Fatma Ak", date: "2024-03-10" },
  { id: "5", title: "PR-2024-0846", flow: "Satın Alma Talebi", status: "rejected", step: "Reddedildi", requester: "Ali Veli", date: "2024-03-09" },
];

const statusMap: Record<string, { label: string; class: string }> = {
  running: { label: "İşlemde", class: "bg-blue-50 text-blue-700 border-blue-200" },
  completed: { label: "Tamamlandı", class: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  pending: { label: "Beklemede", class: "bg-amber-50 text-amber-700 border-amber-200" },
  rejected: { label: "Reddedildi", class: "bg-red-50 text-red-700 border-red-200" },
};

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">İzleme Paneli</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Süreç durumları ve iş akışı özeti
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label} className="border-0 shadow-sm hover:shadow-md transition-shadow duration-150">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                      <p className="mt-1 text-2xl font-semibold tracking-tight">{stat.value}</p>
                    </div>
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${stat.bg}`}>
                      <Icon className={`h-5 w-5 ${stat.color}`} strokeWidth={1.8} />
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-emerald-500" />
                    <span className="text-xs font-medium text-emerald-600">{stat.trend}</span>
                    <span className="text-xs text-muted-foreground">son 7 gün</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Quick Actions & Recent */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Quick Actions */}
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Hızlı Erişim</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                { label: "Yeni Akış Tasarla", icon: Workflow, href: "/designer" },
                { label: "Süreç Başlat", icon: FileText, href: "/processes" },
                { label: "Onaylarım", icon: Clock, href: "/inbox" },
                { label: "Kullanıcı Yönetimi", icon: Users, href: "/users" },
              ].map((action) => {
                const Icon = action.icon;
                return (
                  <a
                    key={action.label}
                    href={action.href}
                    className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                  >
                    <Icon className="h-4 w-4" strokeWidth={1.8} />
                    {action.label}
                  </a>
                );
              })}
            </CardContent>
          </Card>

          {/* Recent Processes */}
          <Card className="lg:col-span-2 border-0 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Son Süreçler</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {recentProcesses.map((proc) => (
                  <a
                    key={proc.id}
                    href={`/processes/${proc.id}`}
                    className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-medium">{proc.title}</span>
                        <span className="text-xs text-muted-foreground">{proc.flow} &middot; {proc.requester}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground hidden sm:block">{proc.step}</span>
                      <Badge variant="outline" className={statusMap[proc.status]?.class}>
                        {statusMap[proc.status]?.label}
                      </Badge>
                    </div>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
