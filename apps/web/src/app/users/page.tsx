"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Search, User, Shield, Calendar, DollarSign, ArrowRightLeft } from "lucide-react";
import { formatCurrency, formatDateShort } from "@/lib/utils";

const USERS = [
  { id: "u1", name: "Admin Kullanıcı", email: "admin@eflow.io", role: "admin", department: "IT", cost_center: "CC001", manager: "—" },
  { id: "u2", name: "Ahmet Yılmaz", email: "ahmet@eflow.io", role: "approver", department: "IT", cost_center: "CC001", manager: "Admin Kullanıcı" },
  { id: "u3", name: "Mehmet Demir", email: "mehmet@eflow.io", role: "approver", department: "Finans", cost_center: "CC002", manager: "Admin Kullanıcı" },
  { id: "u4", name: "Ayşe Kara", email: "ayse@eflow.io", role: "viewer", department: "Hukuk", cost_center: "CC003", manager: "Admin Kullanıcı" },
];

const DELEGATIONS = [
  { id: "del_1", from: "Mehmet Demir", to: "Ahmet Yılmaz", start: "2024-03-15", end: "2024-03-22", scope: "Onay", active: true },
];

const APPROVAL_LIMITS = [
  { id: "lim_1", department: "Tümü", budget_type: "Tümü", currency: "TRY", min: 0, max: 50000, approver: "Departman Yöneticisi" },
  { id: "lim_2", department: "Tümü", budget_type: "Tümü", currency: "TRY", min: 50000, max: 250000, approver: "Direktör" },
  { id: "lim_3", department: "Tümü", budget_type: "Tümü", currency: "TRY", min: 250000, max: 999999999, approver: "CFO" },
];

const roleColors: Record<string, string> = {
  admin: "bg-red-50 text-red-700 border-red-200",
  approver: "bg-emerald-50 text-emerald-700 border-emerald-200",
  viewer: "bg-gray-50 text-gray-600 border-gray-200",
};

export default function UsersPage() {
  const [search, setSearch] = useState("");
  const filtered = USERS.filter((u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()));

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Kullanıcılar</h1>
            <p className="text-sm text-muted-foreground mt-1">Kullanıcı, vekalet ve onay limiti yönetimi</p>
          </div>
          <Button size="sm" className="gap-1.5"><Plus className="h-4 w-4" />Kullanıcı Ekle</Button>
        </div>

        <Tabs defaultValue="users">
          <TabsList>
            <TabsTrigger value="users" className="gap-1.5"><User className="h-3.5 w-3.5" />Kullanıcılar</TabsTrigger>
            <TabsTrigger value="delegations" className="gap-1.5"><ArrowRightLeft className="h-3.5 w-3.5" />Vekaletler</TabsTrigger>
            <TabsTrigger value="limits" className="gap-1.5"><DollarSign className="h-3.5 w-3.5" />Onay Limitleri</TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Kullanıcı ara..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Kullanıcı</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Rol</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Departman</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Maliyet Merkezi</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Yönetici</th>
                  </tr></thead>
                  <tbody>
                    {filtered.map((user) => (
                      <tr key={user.id} className="border-b last:border-0 hover:bg-gray-50/50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-[11px] font-semibold text-white">
                              {user.name.split(" ").map((n) => n[0]).join("")}
                            </div>
                            <div>
                              <div className="text-sm font-medium">{user.name}</div>
                              <div className="text-xs text-muted-foreground">{user.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3"><Badge variant="outline" className={roleColors[user.role]}>{user.role}</Badge></td>
                        <td className="px-4 py-3 text-sm">{user.department}</td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">{user.cost_center}</td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">{user.manager}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="delegations" className="space-y-4">
            <div className="flex justify-end">
              <Button size="sm" className="gap-1.5"><Plus className="h-4 w-4" />Vekalet Ekle</Button>
            </div>
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Vekalet Veren</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Vekil</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Başlangıç</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Bitiş</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Kapsam</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Durum</th>
                  </tr></thead>
                  <tbody>
                    {DELEGATIONS.map((del) => (
                      <tr key={del.id} className="border-b last:border-0">
                        <td className="px-4 py-3 text-sm font-medium">{del.from}</td>
                        <td className="px-4 py-3 text-sm">{del.to}</td>
                        <td className="px-4 py-3 text-sm">{del.start}</td>
                        <td className="px-4 py-3 text-sm">{del.end}</td>
                        <td className="px-4 py-3 text-sm">{del.scope}</td>
                        <td className="px-4 py-3"><Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">Aktif</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="limits" className="space-y-4">
            <div className="flex justify-end">
              <Button size="sm" className="gap-1.5"><Plus className="h-4 w-4" />Limit Ekle</Button>
            </div>
            <Card className="border-0 shadow-sm">
              <CardContent className="p-0">
                <table className="w-full">
                  <thead><tr className="border-b bg-gray-50/50">
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Departman</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Bütçe Türü</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Para Birimi</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Min Tutar</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Max Tutar</th>
                    <th className="px-4 py-3 text-left text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Onaylayan</th>
                  </tr></thead>
                  <tbody>
                    {APPROVAL_LIMITS.map((lim) => (
                      <tr key={lim.id} className="border-b last:border-0">
                        <td className="px-4 py-3 text-sm">{lim.department}</td>
                        <td className="px-4 py-3 text-sm">{lim.budget_type}</td>
                        <td className="px-4 py-3 text-sm">{lim.currency}</td>
                        <td className="px-4 py-3 text-sm font-medium">{formatCurrency(lim.min)}</td>
                        <td className="px-4 py-3 text-sm font-medium">{lim.max >= 999999999 ? "∞" : formatCurrency(lim.max)}</td>
                        <td className="px-4 py-3 text-sm font-medium">{lim.approver}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}
