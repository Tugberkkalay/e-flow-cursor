"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Search, Workflow, FileText, LayoutTemplate, Clock } from "lucide-react";
import { useAppStore } from "@/store";
import { FLOW_TEMPLATES } from "@/lib/templates";
import { useRouter } from "next/navigation";
import { statusColor } from "@/lib/utils";

const DEMO_FLOWS = [
  { id: "flow_1", name: "Satın Alma Talebi (PR)", status: "published", version: 3, updated: "2024-03-12", templateId: "tpl_purchase_request" },
  { id: "flow_2", name: "Satın Alma Süreci (P2P)", status: "published", version: 2, updated: "2024-03-11", templateId: "tpl_purchase_process" },
  { id: "flow_3", name: "Sözleşme Süreci", status: "draft", version: 1, updated: "2024-03-10", templateId: "tpl_contract" },
  { id: "flow_4", name: "Sipariş/Fatura/Ödeme", status: "published", version: 1, updated: "2024-03-09", templateId: "tpl_invoice_payment" },
];

export default function DesignerPage() {
  const router = useRouter();
  const { setNodes, setEdges, setCurrentFlow } = useAppStore();
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [newFlowName, setNewFlowName] = useState("");

  const filteredFlows = DEMO_FLOWS.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase())
  );

  const openFlow = (flow: typeof DEMO_FLOWS[0]) => {
    const template = FLOW_TEMPLATES.find((t) => t.id === flow.templateId);
    if (template) {
      setNodes(template.nodes);
      setEdges(template.edges);
    }
    setCurrentFlow({
      id: flow.id,
      name: flow.name,
      status: flow.status as any,
      current_version: flow.version,
      created_at: flow.updated,
      updated_at: flow.updated,
      org_id: "org_1",
    });
    router.push(`/designer/${flow.id}`);
  };

  const createFromTemplate = (template: typeof FLOW_TEMPLATES[0]) => {
    setNodes(template.nodes);
    setEdges(template.edges);
    setCurrentFlow({
      id: `flow_new_${Date.now()}`,
      name: template.name,
      status: "draft",
      current_version: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      org_id: "org_1",
    });
    router.push(`/designer/new`);
  };

  const createBlank = () => {
    setNodes([]);
    setEdges([]);
    setCurrentFlow({
      id: `flow_new_${Date.now()}`,
      name: newFlowName || "Yeni Akış",
      status: "draft",
      current_version: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      org_id: "org_1",
    });
    setShowNew(false);
    router.push(`/designer/new`);
  };

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Tasarım Stüdyosu</h1>
            <p className="text-sm text-muted-foreground mt-1">Akış ve form tasarımları</p>
          </div>
          <div className="flex gap-2">
            <Dialog open={showNew} onOpenChange={setShowNew}>
              <DialogTrigger asChild>
                <Button size="sm" className="gap-1.5">
                  <Plus className="h-4 w-4" />
                  Yeni Akış
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Yeni Akış Oluştur</DialogTitle>
                  <DialogDescription>Boş bir akış oluşturun veya şablondan başlayın</DialogDescription>
                </DialogHeader>
                <div className="space-y-3 py-2">
                  <Input
                    placeholder="Akış adı..."
                    value={newFlowName}
                    onChange={(e) => setNewFlowName(e.target.value)}
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowNew(false)}>İptal</Button>
                  <Button onClick={createBlank}>Boş Oluştur</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Akış ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Flows Grid */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wider">Akışlar</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredFlows.map((flow) => (
              <Card
                key={flow.id}
                className="border-0 shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer group"
                onClick={() => openFlow(flow)}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/5">
                      <Workflow className="h-5 w-5 text-primary" strokeWidth={1.8} />
                    </div>
                    <Badge variant="outline" className={statusColor(flow.status)}>
                      {flow.status === "published" ? "Yayında" : "Taslak"}
                    </Badge>
                  </div>
                  <h3 className="text-sm font-semibold mb-1 group-hover:text-primary transition-colors">
                    {flow.name}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      v{flow.version}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {flow.updated}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Templates Gallery */}
        <div>
          <h2 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wider flex items-center gap-2">
            <LayoutTemplate className="h-4 w-4" />
            Şablon Galerisi
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FLOW_TEMPLATES.map((tpl) => (
              <Card
                key={tpl.id}
                className="border-0 shadow-sm hover:shadow-md transition-all duration-150 cursor-pointer group border-dashed"
                onClick={() => createFromTemplate(tpl)}
              >
                <CardContent className="p-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 mb-3">
                    <LayoutTemplate className="h-5 w-5 text-emerald-600" strokeWidth={1.8} />
                  </div>
                  <h3 className="text-sm font-semibold mb-1 group-hover:text-primary transition-colors">
                    {tpl.name}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-2">{tpl.description}</p>
                  <div className="mt-3 text-xs text-muted-foreground">
                    {tpl.nodes.length} node &middot; {tpl.edges.length} bağlantı
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
