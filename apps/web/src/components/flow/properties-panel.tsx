"use client";

import React from "react";
import { X, Trash2, Copy } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAppStore } from "@/store";
import { getNodeDef } from "@/lib/node-registry";

function getIcon(iconName: string) {
  const icons = LucideIcons as any;
  return icons[iconName] || icons.Circle;
}

interface PropertiesPanelProps {
  onClose: () => void;
  onDelete: (id: string) => void;
}

export function PropertiesPanel({ onClose, onDelete }: PropertiesPanelProps) {
  const { selectedNodeId, nodes, updateNode } = useAppStore();
  const node = nodes.find((n) => n.id === selectedNodeId);

  if (!node) return null;

  const def = getNodeDef(node.data.nodeType);
  const Icon = getIcon(def?.icon || "Circle");
  const color = def?.color || "#64748b";
  const bgColor = def?.bgColor || "#f8fafc";

  const updateConfig = (key: string, value: any) => {
    updateNode(node.id, {
      data: {
        ...node.data,
        config: { ...node.data.config, [key]: value },
      },
    });
  };

  const updateLabel = (label: string) => {
    updateNode(node.id, {
      data: { ...node.data, label },
    });
  };

  return (
    <div className="flex h-full w-[320px] flex-col border-l bg-white panel-transition">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-lg"
            style={{ backgroundColor: bgColor }}
          >
            <Icon className="h-3.5 w-3.5" style={{ color }} strokeWidth={1.8} />
          </div>
          <div>
            <div className="text-sm font-semibold">{node.data.label}</div>
            <div className="text-[10px] text-muted-foreground">{def?.engineType}</div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => onDelete(node.id)}>
            <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <Tabs defaultValue="general" className="w-full">
          <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-4 h-9">
            <TabsTrigger value="general" className="text-xs">Genel</TabsTrigger>
            <TabsTrigger value="config" className="text-xs">Yapılandırma</TabsTrigger>
            <TabsTrigger value="advanced" className="text-xs">Gelişmiş</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="px-4 py-3 space-y-4">
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Node Adı
              </label>
              <Input
                value={node.data.label}
                onChange={(e) => updateLabel(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Açıklama
              </label>
              <Input
                value={node.data.description || ""}
                onChange={(e) => updateNode(node.id, { data: { ...node.data, description: e.target.value } })}
                className="h-8 text-sm"
                placeholder="Bu adımın amacı..."
              />
            </div>
            <Separator />
            <div className="space-y-1">
              <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Bilgi
              </div>
              <div className="rounded-lg bg-gray-50 p-3 space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Tip</span>
                  <span className="font-medium">{def?.label}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Motor Tipi</span>
                  <span className="font-medium">{def?.engineType}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Kategori</span>
                  <span className="font-medium">{def?.category}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Çıktılar</span>
                  <span className="font-medium">{def?.outputs.join(", ") || "—"}</span>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="config" className="px-4 py-3 space-y-4">
            {node.data.nodeType === "if_condition" && (
              <>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Koşul İfadesi
                  </label>
                  <Input
                    value={node.data.config?.condition || ""}
                    onChange={(e) => updateConfig("condition", e.target.value)}
                    className="h-8 text-sm font-mono"
                    placeholder='{{ form.total_amount >= 50000 }}'
                  />
                  <p className="text-[10px] text-muted-foreground">
                    {"{{ }}"} ile context değişkenlerine erişin
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] font-medium text-muted-foreground">Doğru Etiketi</label>
                    <Input
                      value={node.data.config?.true_label || "Evet"}
                      onChange={(e) => updateConfig("true_label", e.target.value)}
                      className="h-7 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-medium text-muted-foreground">Yanlış Etiketi</label>
                    <Input
                      value={node.data.config?.false_label || "Hayır"}
                      onChange={(e) => updateConfig("false_label", e.target.value)}
                      className="h-7 text-xs"
                    />
                  </div>
                </div>
              </>
            )}

            {node.data.nodeType === "approval_single" && (
              <>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Onaylayan Tipi
                  </label>
                  <select
                    value={node.data.config?.approver_type || "manager"}
                    onChange={(e) => updateConfig("approver_type", e.target.value)}
                    className="w-full h-8 rounded-lg border bg-background px-3 text-sm"
                  >
                    <option value="manager">Yönetici</option>
                    <option value="role">Rol Bazlı</option>
                    <option value="specific">Belirli Kullanıcı</option>
                    <option value="limit_matrix">Limit Matrisi</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Yorum Zorunlu
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={node.data.config?.comment_required || false}
                      onChange={(e) => updateConfig("comment_required", e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-xs text-muted-foreground">Onay/red için yorum zorunlu</span>
                  </div>
                </div>
              </>
            )}

            {node.data.nodeType === "http_request" && (
              <>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">URL</label>
                  <Input
                    value={node.data.config?.url || ""}
                    onChange={(e) => updateConfig("url", e.target.value)}
                    className="h-8 text-sm font-mono"
                    placeholder="https://api.example.com/..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Metod</label>
                  <select
                    value={node.data.config?.method || "POST"}
                    onChange={(e) => updateConfig("method", e.target.value)}
                    className="w-full h-8 rounded-lg border bg-background px-3 text-sm"
                  >
                    <option>GET</option>
                    <option>POST</option>
                    <option>PUT</option>
                    <option>PATCH</option>
                    <option>DELETE</option>
                  </select>
                </div>
              </>
            )}

            {node.data.nodeType === "document_upload" && (
              <>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Doküman Tipi
                  </label>
                  <Input
                    value={node.data.config?.doc_type || ""}
                    onChange={(e) => updateConfig("doc_type", e.target.value)}
                    className="h-8 text-sm"
                    placeholder="offer, invoice, contract..."
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Minimum Doküman Sayısı
                  </label>
                  <Input
                    type="number"
                    value={node.data.config?.min_count || 1}
                    onChange={(e) => updateConfig("min_count", parseInt(e.target.value))}
                    className="h-8 text-sm"
                    min={1}
                  />
                </div>
              </>
            )}

            {node.data.nodeType === "calculate" && (
              <div className="space-y-2">
                <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  Hesaplama İfadesi
                </label>
                <Input
                  value={node.data.config?.expression || ""}
                  onChange={(e) => updateConfig("expression", e.target.value)}
                  className="h-8 text-sm font-mono"
                  placeholder='{{ form.quantity * form.unit_price }}'
                />
              </div>
            )}

            {node.data.nodeType === "email_send" && (
              <>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Alıcı</label>
                  <Input
                    value={node.data.config?.to || ""}
                    onChange={(e) => updateConfig("to", e.target.value)}
                    className="h-8 text-sm"
                    placeholder="{{ system.requester_email }}"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Konu</label>
                  <Input
                    value={node.data.config?.subject || ""}
                    onChange={(e) => updateConfig("subject", e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
              </>
            )}

            {node.data.nodeType === "subprocess_call" && (
              <div className="space-y-2">
                <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  Hedef Akış
                </label>
                <Input
                  value={node.data.config?.target_flow_id || ""}
                  onChange={(e) => updateConfig("target_flow_id", e.target.value)}
                  className="h-8 text-sm"
                  placeholder="Akış ID seçin..."
                />
                <div className="space-y-2 mt-3">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Giriş Eşleme (JSON)
                  </label>
                  <textarea
                    value={JSON.stringify(node.data.config?.input_mapping || {}, null, 2)}
                    onChange={(e) => {
                      try { updateConfig("input_mapping", JSON.parse(e.target.value)); } catch {}
                    }}
                    className="w-full h-20 rounded-lg border bg-background px-3 py-2 text-xs font-mono resize-none"
                  />
                </div>
                <div className="space-y-2 mt-2">
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    Çıkış Eşleme (JSON)
                  </label>
                  <textarea
                    value={JSON.stringify(node.data.config?.output_mapping || {}, null, 2)}
                    onChange={(e) => {
                      try { updateConfig("output_mapping", JSON.parse(e.target.value)); } catch {}
                    }}
                    className="w-full h-20 rounded-lg border bg-background px-3 py-2 text-xs font-mono resize-none"
                  />
                </div>
              </div>
            )}

            {/* Generic config for other node types */}
            {!["if_condition", "approval_single", "http_request", "document_upload", "calculate", "email_send", "subprocess_call"].includes(node.data.nodeType) && (
              <div className="space-y-2">
                <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  Yapılandırma (JSON)
                </label>
                <textarea
                  value={JSON.stringify(node.data.config || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const config = JSON.parse(e.target.value);
                      updateNode(node.id, { data: { ...node.data, config } });
                    } catch {}
                  }}
                  className="w-full h-32 rounded-lg border bg-background px-3 py-2 text-xs font-mono resize-none"
                />
              </div>
            )}
          </TabsContent>

          <TabsContent value="advanced" className="px-4 py-3 space-y-4">
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Tekrar Deneme
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-muted-foreground">Deneme Sayısı</label>
                  <Input
                    type="number"
                    value={node.data.config?.retries || 0}
                    onChange={(e) => updateConfig("retries", parseInt(e.target.value))}
                    className="h-7 text-xs"
                    min={0}
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground">Zaman Aşımı (sn)</label>
                  <Input
                    type="number"
                    value={node.data.config?.timeout || 300}
                    onChange={(e) => updateConfig("timeout", parseInt(e.target.value))}
                    className="h-7 text-xs"
                    min={0}
                  />
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Hata Davranışı
              </label>
              <select
                value={node.data.config?.error_behavior || "stop"}
                onChange={(e) => updateConfig("error_behavior", e.target.value)}
                className="w-full h-8 rounded-lg border bg-background px-3 text-sm"
              >
                <option value="stop">Süreci Durdur</option>
                <option value="skip">Adımı Atla</option>
                <option value="retry">Yeniden Dene</option>
                <option value="route_error">Hata Akışına Yönlendir</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Idempotency Anahtarı
              </label>
              <Input
                value={node.data.config?.idempotency_key || ""}
                onChange={(e) => updateConfig("idempotency_key", e.target.value)}
                className="h-8 text-sm font-mono"
                placeholder="{{ system.instance_id }}_{{ system.node_id }}"
              />
            </div>
          </TabsContent>
        </Tabs>
      </ScrollArea>
    </div>
  );
}
