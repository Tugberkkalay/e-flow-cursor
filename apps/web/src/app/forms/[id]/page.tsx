"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft, Plus, GripVertical, Trash2, Save, Upload, Settings, Eye, EyeOff, ChevronDown, ChevronUp,
  Type, Hash, Calendar, List, ToggleLeft, FileUp, Table2, DollarSign, AlignLeft, CheckSquare,
} from "lucide-react";
import Link from "next/link";

type FieldType = "text" | "textarea" | "number" | "money" | "date" | "dropdown" | "multi_select" | "boolean" | "file_upload" | "line_items";

interface FormField {
  id: string;
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
  placeholder?: string;
  options?: { label: string; value: string }[];
  order: number;
}

const FIELD_TYPE_OPTIONS: { type: FieldType; label: string; icon: any }[] = [
  { type: "text", label: "Metin", icon: Type },
  { type: "textarea", label: "Uzun Metin", icon: AlignLeft },
  { type: "number", label: "Sayı", icon: Hash },
  { type: "money", label: "Para", icon: DollarSign },
  { type: "date", label: "Tarih", icon: Calendar },
  { type: "dropdown", label: "Açılır Liste", icon: List },
  { type: "multi_select", label: "Çoklu Seçim", icon: CheckSquare },
  { type: "boolean", label: "Evet/Hayır", icon: ToggleLeft },
  { type: "file_upload", label: "Dosya Yükleme", icon: FileUp },
  { type: "line_items", label: "Satır Tablosu", icon: Table2 },
];

const INITIAL_FIELDS: FormField[] = [
  { id: "f1", key: "title", label: "Talep Başlığı", type: "text", required: true, placeholder: "Talep başlığını girin", order: 0 },
  { id: "f2", key: "description", label: "Açıklama", type: "textarea", required: false, placeholder: "Detaylı açıklama", order: 1 },
  { id: "f3", key: "request_type", label: "Talep Türü", type: "dropdown", required: true, options: [{ label: "Mal Alımı", value: "goods" }, { label: "Hizmet Alımı", value: "service" }, { label: "Abonelik", value: "subscription" }], order: 2 },
  { id: "f4", key: "department", label: "Departman", type: "dropdown", required: true, options: [{ label: "IT", value: "it" }, { label: "İnsan Kaynakları", value: "hr" }, { label: "Operasyon", value: "ops" }, { label: "Pazarlama", value: "marketing" }], order: 3 },
  { id: "f5", key: "quantity", label: "Miktar", type: "number", required: true, order: 4 },
  { id: "f6", key: "unit_price", label: "Birim Fiyat", type: "money", required: true, order: 5 },
  { id: "f7", key: "vat_rate", label: "KDV Oranı (%)", type: "number", required: true, order: 6 },
  { id: "f8", key: "total_amount", label: "Toplam Tutar", type: "money", required: false, order: 7 },
  { id: "f9", key: "currency", label: "Para Birimi", type: "dropdown", required: true, options: [{ label: "TRY", value: "TRY" }, { label: "USD", value: "USD" }, { label: "EUR", value: "EUR" }], order: 8 },
  { id: "f10", key: "needed_by", label: "İhtiyaç Tarihi", type: "date", required: false, order: 9 },
  { id: "f11", key: "urgent", label: "Acil mi?", type: "boolean", required: false, order: 10 },
  { id: "f12", key: "attachments", label: "Ek Dosyalar", type: "file_upload", required: false, order: 11 },
];

export default function FormBuilderPage() {
  const [fields, setFields] = useState<FormField[]>(INITIAL_FIELDS);
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [showAddField, setShowAddField] = useState(false);

  const addField = (type: FieldType) => {
    const newField: FormField = {
      id: `f_${Date.now()}`,
      key: `field_${fields.length + 1}`,
      label: FIELD_TYPE_OPTIONS.find((f) => f.type === type)?.label || "Yeni Alan",
      type,
      required: false,
      order: fields.length,
    };
    setFields([...fields, newField]);
    setSelectedField(newField.id);
    setShowAddField(false);
  };

  const updateField = (id: string, updates: Partial<FormField>) => {
    setFields(fields.map((f) => (f.id === id ? { ...f, ...updates } : f)));
  };

  const removeField = (id: string) => {
    setFields(fields.filter((f) => f.id !== id));
    if (selectedField === id) setSelectedField(null);
  };

  const selected = fields.find((f) => f.id === selectedField);

  return (
    <AppShell>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/forms">
              <Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="h-4 w-4" /></Button>
            </Link>
            <div>
              <h1 className="text-lg font-semibold">Satın Alma Talep Formu</h1>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-[10px]">Yayında</Badge>
                <span className="text-xs text-muted-foreground">v2 &middot; 12 alan</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-1.5"><Save className="h-3.5 w-3.5" />Kaydet</Button>
            <Button size="sm" className="gap-1.5"><Upload className="h-3.5 w-3.5" />Yayınla</Button>
          </div>
        </div>

        {/* Builder Layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Field List */}
          <div className="col-span-7 space-y-2">
            {fields.map((field) => {
              const FieldIcon = FIELD_TYPE_OPTIONS.find((f) => f.type === field.type)?.icon || Type;
              return (
                <div
                  key={field.id}
                  onClick={() => setSelectedField(field.id)}
                  className={`flex items-center gap-3 rounded-xl border bg-white p-3 cursor-pointer transition-all duration-150 ${
                    selectedField === field.id
                      ? "border-primary/30 shadow-md ring-2 ring-primary/10"
                      : "border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300"
                  }`}
                >
                  <GripVertical className="h-4 w-4 text-gray-300 cursor-grab" />
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-50">
                    <FieldIcon className="h-4 w-4 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{field.label}</span>
                      {field.required && <span className="text-[10px] text-red-500 font-medium">Zorunlu</span>}
                    </div>
                    <span className="text-[11px] text-muted-foreground font-mono">{field.key}</span>
                  </div>
                  <Badge variant="outline" className="text-[10px]">{field.type}</Badge>
                  <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={(e) => { e.stopPropagation(); removeField(field.id); }}>
                    <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              );
            })}

            {/* Add Field */}
            {showAddField ? (
              <Card className="border-dashed border-2">
                <CardContent className="p-4">
                  <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Alan Tipi Seçin</div>
                  <div className="grid grid-cols-5 gap-2">
                    {FIELD_TYPE_OPTIONS.map((opt) => {
                      const Icon = opt.icon;
                      return (
                        <button
                          key={opt.type}
                          onClick={() => addField(opt.type)}
                          className="flex flex-col items-center gap-1.5 rounded-lg border p-3 hover:bg-gray-50 hover:border-gray-300 transition-colors"
                        >
                          <Icon className="h-4 w-4 text-gray-500" />
                          <span className="text-[10px] font-medium text-gray-600">{opt.label}</span>
                        </button>
                      );
                    })}
                  </div>
                  <Button variant="ghost" size="sm" className="mt-2 w-full text-xs" onClick={() => setShowAddField(false)}>İptal</Button>
                </CardContent>
              </Card>
            ) : (
              <button
                onClick={() => setShowAddField(true)}
                className="flex items-center justify-center gap-2 w-full rounded-xl border-2 border-dashed border-gray-200 py-3 text-sm text-muted-foreground hover:border-gray-400 hover:text-foreground transition-colors"
              >
                <Plus className="h-4 w-4" />
                Alan Ekle
              </button>
            )}
          </div>

          {/* Field Properties */}
          <div className="col-span-5">
            {selected ? (
              <Card className="sticky top-20 border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Alan Ayarları
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Etiket</label>
                    <Input value={selected.label} onChange={(e) => updateField(selected.id, { label: e.target.value })} className="h-8 text-sm" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Anahtar (snake_case)</label>
                    <Input value={selected.key} onChange={(e) => updateField(selected.id, { key: e.target.value })} className="h-8 text-sm font-mono" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Placeholder</label>
                    <Input value={selected.placeholder || ""} onChange={(e) => updateField(selected.id, { placeholder: e.target.value })} className="h-8 text-sm" />
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={selected.required} onChange={(e) => updateField(selected.id, { required: e.target.checked })} className="rounded" id="req" />
                    <label htmlFor="req" className="text-sm font-medium">Zorunlu Alan</label>
                  </div>
                  {(selected.type === "dropdown" || selected.type === "multi_select") && (
                    <div className="space-y-2">
                      <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Seçenekler</label>
                      <div className="space-y-1">
                        {(selected.options || []).map((opt, idx) => (
                          <div key={idx} className="flex gap-2">
                            <Input value={opt.label} className="h-7 text-xs" onChange={(e) => {
                              const newOpts = [...(selected.options || [])];
                              newOpts[idx] = { ...newOpts[idx], label: e.target.value, value: e.target.value.toLowerCase().replace(/\s+/g, "_") };
                              updateField(selected.id, { options: newOpts });
                            }} />
                          </div>
                        ))}
                        <Button variant="outline" size="sm" className="text-xs w-full" onClick={() => {
                          updateField(selected.id, { options: [...(selected.options || []), { label: "Yeni Seçenek", value: "new" }] });
                        }}><Plus className="h-3 w-3 mr-1" />Seçenek Ekle</Button>
                      </div>
                    </div>
                  )}
                  <Separator />
                  <div className="space-y-2">
                    <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Koşullu Kurallar</label>
                    <div className="rounded-lg bg-gray-50 p-3 text-xs text-muted-foreground text-center">
                      Koşullu görünürlük ve zorunluluk kuralları ekleyin
                    </div>
                    <Button variant="outline" size="sm" className="text-xs w-full"><Plus className="h-3 w-3 mr-1" />Kural Ekle</Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-0 shadow-sm">
                <CardContent className="p-8 text-center">
                  <Settings className="h-8 w-8 text-muted-foreground/30 mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground">Bir alan seçin veya yeni alan ekleyin</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
