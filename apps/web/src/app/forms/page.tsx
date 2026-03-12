"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Search, FileText, Clock, Settings } from "lucide-react";
import { statusColor } from "@/lib/utils";
import { useRouter } from "next/navigation";

const DEMO_FORMS = [
  { id: "form_1", name: "Satın Alma Talep Formu", status: "published", version: 2, fields: 12, updated: "2024-03-12" },
  { id: "form_2", name: "Tedarikçi Bilgi Formu", status: "published", version: 1, fields: 8, updated: "2024-03-11" },
  { id: "form_3", name: "Sözleşme Detay Formu", status: "draft", version: 1, fields: 15, updated: "2024-03-10" },
  { id: "form_4", name: "Fatura Giriş Formu", status: "published", version: 3, fields: 10, updated: "2024-03-09" },
];

export default function FormsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");

  const filteredForms = DEMO_FORMS.filter((f) => f.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Form Oluşturucu</h1>
            <p className="text-sm text-muted-foreground mt-1">Dinamik formlar tasarlayın ve yönetin</p>
          </div>
          <Dialog open={showNew} onOpenChange={setShowNew}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1.5"><Plus className="h-4 w-4" />Yeni Form</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Yeni Form Oluştur</DialogTitle>
                <DialogDescription>Form alanlarını daha sonra ekleyebilirsiniz</DialogDescription>
              </DialogHeader>
              <Input placeholder="Form adı..." value={newName} onChange={(e) => setNewName(e.target.value)} />
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNew(false)}>İptal</Button>
                <Button onClick={() => { setShowNew(false); router.push("/forms/new"); }}>Oluştur</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Form ara..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredForms.map((form) => (
            <Card key={form.id} className="border-0 shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer group" onClick={() => router.push(`/forms/${form.id}`)}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50">
                    <FileText className="h-5 w-5 text-violet-600" strokeWidth={1.8} />
                  </div>
                  <Badge variant="outline" className={statusColor(form.status)}>{form.status === "published" ? "Yayında" : "Taslak"}</Badge>
                </div>
                <h3 className="text-sm font-semibold mb-1 group-hover:text-primary transition-colors">{form.name}</h3>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Settings className="h-3 w-3" />{form.fields} alan</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />v{form.version}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
