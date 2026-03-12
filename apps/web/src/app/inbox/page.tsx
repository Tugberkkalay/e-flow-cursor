"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  ThumbsUp, ThumbsDown, MessageSquare, RotateCcw, Clock, User, FileText, AlertCircle,
  CheckCircle, XCircle, ChevronRight,
} from "lucide-react";
import { formatDate, formatCurrency, statusColor } from "@/lib/utils";

const INBOX_ITEMS = [
  {
    id: "inb_1", type: "approval", title: "Satın Alma Onayı", instance_title: "PR-2024-0847",
    flow_name: "Satın Alma Talebi", requester: "Ahmet Yılmaz", amount: 420000, currency: "TRY",
    description: "10 adet Dizüstü Bilgisayar - IT Departmanı", created_at: "2024-03-12T10:30:00Z",
    due_date: "2024-03-14T10:30:00Z",
  },
  {
    id: "inb_2", type: "approval", title: "Sözleşme Onayı", instance_title: "CNT-2024-0091",
    flow_name: "Sözleşme Süreci", requester: "Ayşe Kara", amount: 1200000, currency: "TRY",
    description: "Yazılım lisans sözleşmesi yenileme", created_at: "2024-03-11T14:00:00Z",
    due_date: "2024-03-15T14:00:00Z",
  },
  {
    id: "inb_3", type: "task", title: "Tedarikçi Seçimi", instance_title: "PO-2024-0235",
    flow_name: "Satın Alma Süreci", requester: "Zeynep Demir", amount: 85000, currency: "TRY",
    description: "3 teklif arasından tedarikçi seçimi yapılmalı", created_at: "2024-03-12T08:00:00Z",
    due_date: "2024-03-13T17:00:00Z",
  },
  {
    id: "inb_4", type: "task", title: "Fatura İnceleme", instance_title: "INV-2024-0563",
    flow_name: "Fatura/Ödeme", requester: "Can Bey", amount: 52000, currency: "TRY",
    description: "Fatura tutarı sipariş ile uyuşmuyor - inceleme gerekli", created_at: "2024-03-11T16:00:00Z",
    due_date: "2024-03-13T16:00:00Z",
  },
];

export default function InboxPage() {
  const [filter, setFilter] = useState("all");
  const [selectedItem, setSelectedItem] = useState<typeof INBOX_ITEMS[0] | null>(null);
  const [comment, setComment] = useState("");

  const filtered = filter === "all" ? INBOX_ITEMS : INBOX_ITEMS.filter((i) => i.type === filter);

  const handleAction = (action: string) => {
    setSelectedItem(null);
    setComment("");
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Onaylarım</h1>
          <p className="text-sm text-muted-foreground mt-1">Bekleyen onay ve görevler</p>
        </div>

        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList>
            <TabsTrigger value="all" className="text-xs">Tümü ({INBOX_ITEMS.length})</TabsTrigger>
            <TabsTrigger value="approval" className="text-xs">Onaylar ({INBOX_ITEMS.filter((i) => i.type === "approval").length})</TabsTrigger>
            <TabsTrigger value="task" className="text-xs">Görevler ({INBOX_ITEMS.filter((i) => i.type === "task").length})</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="space-y-3">
          {filtered.map((item) => (
            <Card
              key={item.id}
              className="border-0 shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer"
              onClick={() => setSelectedItem(item)}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                      item.type === "approval" ? "bg-emerald-50" : "bg-blue-50"
                    }`}>
                      {item.type === "approval" ? (
                        <ThumbsUp className="h-5 w-5 text-emerald-600" strokeWidth={1.8} />
                      ) : (
                        <FileText className="h-5 w-5 text-blue-600" strokeWidth={1.8} />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold">{item.title}</span>
                        <Badge variant="outline" className={item.type === "approval" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-blue-50 text-blue-700 border-blue-200"}>
                          {item.type === "approval" ? "Onay" : "Görev"}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mb-1">{item.description}</div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><User className="h-3 w-3" />{item.requester}</span>
                        <span>{item.instance_title}</span>
                        <span>{item.flow_name}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <div className="text-lg font-semibold">{formatCurrency(item.amount, item.currency)}</div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(item.created_at)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Action Dialog */}
        <Dialog open={!!selectedItem} onOpenChange={(open) => !open && setSelectedItem(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>{selectedItem?.title}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="rounded-lg bg-gray-50 p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Talep Eden</span>
                  <span className="font-medium">{selectedItem?.requester}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Süreç</span>
                  <span className="font-medium">{selectedItem?.instance_title}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Tutar</span>
                  <span className="font-semibold">{selectedItem && formatCurrency(selectedItem.amount, selectedItem.currency)}</span>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Yorum</label>
                <Input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Yorum ekleyin..." />
              </div>
            </div>
            <DialogFooter className="gap-2">
              {selectedItem?.type === "approval" ? (
                <>
                  <Button variant="outline" className="gap-1.5 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => handleAction("reject")}>
                    <XCircle className="h-4 w-4" />Reddet
                  </Button>
                  <Button variant="outline" className="gap-1.5 text-amber-600" onClick={() => handleAction("revision")}>
                    <RotateCcw className="h-4 w-4" />Revizyon
                  </Button>
                  <Button className="gap-1.5" onClick={() => handleAction("approve")}>
                    <CheckCircle className="h-4 w-4" />Onayla
                  </Button>
                </>
              ) : (
                <Button className="gap-1.5" onClick={() => handleAction("complete")}>
                  <CheckCircle className="h-4 w-4" />Tamamla
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
