"use client";

import React from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Building2, Globe, Shield, Mail, Database, Key, Bell, Palette,
} from "lucide-react";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Ayarlar</h1>
          <p className="text-sm text-muted-foreground mt-1">Platform yapılandırması</p>
        </div>

        <Tabs defaultValue="general">
          <TabsList>
            <TabsTrigger value="general" className="gap-1.5"><Building2 className="h-3.5 w-3.5" />Genel</TabsTrigger>
            <TabsTrigger value="auth" className="gap-1.5"><Key className="h-3.5 w-3.5" />Kimlik Doğrulama</TabsTrigger>
            <TabsTrigger value="integrations" className="gap-1.5"><Globe className="h-3.5 w-3.5" />Entegrasyonlar</TabsTrigger>
            <TabsTrigger value="notifications" className="gap-1.5"><Bell className="h-3.5 w-3.5" />Bildirimler</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-6">
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Organizasyon</CardTitle>
                <CardDescription>Kuruluş bilgileri ve varsayılan ayarlar</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Kuruluş Adı</label>
                    <Input defaultValue="e-Flow Demo Corp" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Org ID</label>
                    <Input defaultValue="org_1" disabled className="bg-gray-50" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Varsayılan Para Birimi</label>
                    <Input defaultValue="TRY" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Zaman Dilimi</label>
                    <Input defaultValue="Europe/Istanbul" />
                  </div>
                </div>
                <Button size="sm">Kaydet</Button>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Motor Ayarları</CardTitle>
                <CardDescription>BPM motoru yapılandırması</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Varsayılan SLA (saat)</label>
                    <Input type="number" defaultValue="24" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Varsayılan Retry Sayısı</label>
                    <Input type="number" defaultValue="3" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Hata Akışı</label>
                    <Input placeholder="Hata akışı ID..." />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Backoff (saniye)</label>
                    <Input type="number" defaultValue="30" />
                  </div>
                </div>
                <Button size="sm">Kaydet</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="auth" className="space-y-6">
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">JWT Yapılandırması</CardTitle>
                <CardDescription>Kimlik doğrulama token ayarları</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Secret Key</label>
                  <Input type="password" defaultValue="••••••••••••" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Token Süresi (dakika)</label>
                    <Input type="number" defaultValue="60" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Algoritma</label>
                    <Input defaultValue="HS256" disabled className="bg-gray-50" />
                  </div>
                </div>
                <Button size="sm">Kaydet</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="integrations" className="space-y-6">
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Depolama (S3/MinIO)</CardTitle>
                <CardDescription>Doküman depolama yapılandırması</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Endpoint URL</label>
                    <Input placeholder="http://minio:9000" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Bucket</label>
                    <Input defaultValue="eflow-documents" />
                  </div>
                </div>
                <Button size="sm">Bağlantıyı Test Et</Button>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">E-posta (SMTP)</CardTitle>
                <CardDescription>E-posta bildirim yapılandırması</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">SMTP Sunucu</label>
                    <Input placeholder="smtp.gmail.com" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Port</label>
                    <Input type="number" defaultValue="587" />
                  </div>
                </div>
                <Button size="sm">Bağlantıyı Test Et</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Bildirim Ayarları</CardTitle>
                <CardDescription>Hangi olaylarda bildirim gönderilsin</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {["Onay talebi", "Görev ataması", "SLA ihlali", "Süreç tamamlanma", "Hata bildirimi"].map((item) => (
                  <div key={item} className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3">
                    <span className="text-sm font-medium">{item}</span>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                ))}
                <Button size="sm">Kaydet</Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}
