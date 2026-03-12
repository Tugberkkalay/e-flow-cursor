"use client";

import { useMemo, useState } from "react";
import { Plus, Sigma } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

type FieldType =
  | "text"
  | "textarea"
  | "number"
  | "money"
  | "date"
  | "dropdown"
  | "multi-select"
  | "boolean"
  | "file-upload"
  | "line-items";

type Field = {
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
};

export function FormBuilder() {
  const [version, setVersion] = useState(2);
  const [fields, setFields] = useState<Field[]>([
    { key: "request_type", label: "Talep Tipi", type: "dropdown", required: true },
    { key: "total_amount", label: "Toplam Tutar", type: "money", required: true },
    { key: "line_items", label: "Satır Kalemleri", type: "line-items", required: true },
  ]);

  const [newFieldLabel, setNewFieldLabel] = useState("");
  const [rules, setRules] = useState(
    "if request_type == 'Abonelik' => field('contract_start_date').required = true",
  );
  const [calc, setCalc] = useState(
    "calc.total_with_vat = form.total_amount * 1.20\ncalc.fx_total = calc.total_with_vat * form.fx_rate",
  );

  const schemaJson = useMemo(
    () => ({
      version,
      fields,
      rules,
      calculations: calc,
    }),
    [calc, fields, rules, version],
  );

  const addField = () => {
    if (!newFieldLabel.trim()) return;
    const key = newFieldLabel
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
    setFields((curr) => [
      ...curr,
      { key, label: newFieldLabel, type: "text", required: false },
    ]);
    setNewFieldLabel("");
  };

  return (
    <div className="grid grid-cols-12 gap-4">
      <Card className="col-span-7 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Dynamic Form Builder</h3>
            <p className="text-sm text-[#637186]">
              Draft/Publish · stable snake_case keys · line-items destekli
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => setVersion((v) => v + 1)}>
              Version +1
            </Button>
            <Button>Publish</Button>
          </div>
        </div>

        <div className="mb-3 flex gap-2">
          <Input
            placeholder="Yeni alan etiketi (örn. Vendor Name)"
            value={newFieldLabel}
            onChange={(e) => setNewFieldLabel(e.target.value)}
          />
          <Button variant="secondary" onClick={addField}>
            <Plus className="mr-1 h-4 w-4" />
            Alan Ekle
          </Button>
        </div>

        <div className="space-y-2">
          {fields.map((field, index) => (
            <div
              key={`${field.key}-${index}`}
              className="grid grid-cols-12 items-center gap-2 rounded-xl border border-[#E7EBF0] bg-white px-3 py-2"
            >
              <span className="col-span-4 text-sm font-medium">{field.label}</span>
              <span className="col-span-3 text-xs text-[#6A788A]">{field.key}</span>
              <span className="col-span-3 rounded-lg bg-[#F4F6FA] px-2 py-1 text-xs">
                {field.type}
              </span>
              <label className="col-span-2 flex items-center gap-1 text-xs text-[#6A788A]">
                <input
                  type="checkbox"
                  checked={field.required}
                  onChange={(e) =>
                    setFields((curr) =>
                      curr.map((f, idx) =>
                        idx === index ? { ...f, required: e.target.checked } : f,
                      ),
                    )
                  }
                />
                Zorunlu
              </label>
            </div>
          ))}
        </div>
      </Card>

      <Card className="col-span-5 p-4">
        <Tabs defaultValue="rules">
          <TabsList>
            <TabsTrigger value="rules">Rules Builder</TabsTrigger>
            <TabsTrigger value="calc">Calculations</TabsTrigger>
            <TabsTrigger value="schema">Schema Preview</TabsTrigger>
          </TabsList>
          <TabsContent value="rules">
            <p className="mb-2 text-xs text-[#6A788A]">
              Koşullu görünürlük/zorunluluk kuralları
            </p>
            <Textarea
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              className="h-[280px] font-mono text-xs"
            />
          </TabsContent>
          <TabsContent value="calc">
            <p className="mb-2 flex items-center gap-1 text-xs text-[#6A788A]">
              <Sigma className="h-4 w-4" /> KDV/toplam/kur hesapları
            </p>
            <Textarea
              value={calc}
              onChange={(e) => setCalc(e.target.value)}
              className="h-[280px] font-mono text-xs"
            />
          </TabsContent>
          <TabsContent value="schema">
            <pre className="h-[280px] overflow-auto rounded-xl border border-[#E7EBF0] bg-[#FAFBFD] p-3 text-xs">
              {JSON.stringify(schemaJson, null, 2)}
            </pre>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
