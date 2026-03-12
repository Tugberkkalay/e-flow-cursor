"use client";
import { useState, useEffect } from "react";
import { Node } from "reactflow";
import { X, ChevronDown, ChevronRight } from "lucide-react";
import { NODE_REGISTRY } from "@/lib/nodeRegistry";

interface Props {
  node: Node | null;
  onUpdate: (nodeId: string, data: Record<string, unknown>) => void;
  onClose: () => void;
}

export function PropertiesPanel({ node, onUpdate, onClose }: Props) {
  const [label, setLabel] = useState("");
  const [config, setConfig] = useState<Record<string, unknown>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (node) {
      setLabel(node.data.label || "");
      setConfig(node.data.config || {});
    }
  }, [node?.id]);

  if (!node) return null;

  const def = NODE_REGISTRY.find(n => n.engineType === node.data.engineType);

  function save() {
    if (!node) return;
    onUpdate(node.id, { label, config });
  }

  function updateConfig(key: string, value: unknown) {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    onUpdate(node!.id, { label, config: newConfig });
  }

  return (
    <div className="w-[280px] flex-shrink-0 bg-surface border-l border-border flex flex-col h-full animate-slide-in-right">
      {/* Header */}
      <div className="px-4 py-3.5 border-b border-border flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold text-accent">Node Özellikleri</div>
          <div className="text-[10px] text-accent-muted font-mono mt-0.5">{node.data.engineType}</div>
        </div>
        <button onClick={onClose} className="btn-icon text-accent-muted">
          <X size={14} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {/* Label */}
        <div>
          <label className="label mb-1.5 block">Başlık</label>
          <input
            className="input text-sm"
            value={label}
            onChange={e => { setLabel(e.target.value); onUpdate(node.id, { label: e.target.value, config }); }}
          />
        </div>

        {/* Description */}
        {def?.description && (
          <div className="text-xs text-accent-muted bg-muted rounded-lg px-3 py-2">
            {def.description}
          </div>
        )}

        {/* Config fields by type */}
        <ConfigEditor engineType={node.data.engineType} config={config} onChange={updateConfig} />

        {/* Advanced */}
        <div>
          <button
            className="flex items-center gap-1 text-xs text-accent-muted font-medium"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            Gelişmiş Ayarlar
          </button>
          {showAdvanced && (
            <div className="mt-2 space-y-3">
              <div>
                <label className="label mb-1.5 block">Node ID</label>
                <input className="input text-xs font-mono text-accent-muted" value={node.id} readOnly />
              </div>
              <div>
                <label className="label mb-1.5 block">Retry Sayısı</label>
                <input
                  type="number"
                  className="input"
                  value={(config.retries as number) || 0}
                  onChange={e => updateConfig("retries", parseInt(e.target.value))}
                />
              </div>
              <div>
                <label className="label mb-1.5 block">Timeout (sn)</label>
                <input
                  type="number"
                  className="input"
                  value={(config.timeout_seconds as number) || 0}
                  onChange={e => updateConfig("timeout_seconds", parseInt(e.target.value))}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ConfigEditor({ engineType, config, onChange }: {
  engineType: string;
  config: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  if (["ManualStart", "FormSubmitTrigger"].includes(engineType)) {
    return null;
  }

  if (["FormFill", "DataEntry", "DocumentUpload", "ReviewComment", "VendorSelection", "DeliveryAcceptance", "ReworkTask", "ManualCompensation"].includes(engineType)) {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">Görev Başlığı</label>
          <input className="input" value={(config.title as string) || ""} onChange={e => onChange("title", e.target.value)} placeholder="Görev başlığı" />
        </div>
        <div>
          <label className="label mb-1.5 block">Atanan Rol</label>
          <RoleSelect value={(config.assignee_role as string) || ""} onChange={v => onChange("assignee_role", v)} />
        </div>
        {engineType === "DocumentUpload" && (
          <>
            <div>
              <label className="label mb-1.5 block">Belge Tipi</label>
              <input className="input" value={(config.doc_type as string) || ""} onChange={e => onChange("doc_type", e.target.value)} placeholder="örn. offer, invoice" />
            </div>
            <div>
              <label className="label mb-1.5 block">Min. Belge Sayısı</label>
              <input type="number" className="input" value={(config.min_count as number) || 1} onChange={e => onChange("min_count", parseInt(e.target.value))} />
            </div>
          </>
        )}
      </div>
    );
  }

  if (["ApprovalTask", "Approval", "MultiApproval"].includes(engineType)) {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">Görev Başlığı</label>
          <input className="input" value={(config.title as string) || ""} onChange={e => onChange("title", e.target.value)} />
        </div>
        <div>
          <label className="label mb-1.5 block">Onaylayıcı Rol</label>
          <RoleSelect value={(config.approver_role as string) || "approver"} onChange={v => onChange("approver_role", v)} />
        </div>
        <div>
          <label className="label mb-1.5 block">Tutar Alanı (opsiyonel)</label>
          <input className="input font-mono text-xs" value={(config.amount_field as string) || ""} onChange={e => onChange("amount_field", e.target.value)} placeholder="form.total_amount" />
        </div>
      </div>
    );
  }

  if (engineType === "ApprovalByLimitMatrix") {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">Tutar İfadesi</label>
          <input className="input font-mono text-xs" value={(config.amount_expr as string) || "{{ form.total_amount }}"} onChange={e => onChange("amount_expr", e.target.value)} />
        </div>
      </div>
    );
  }

  if (engineType === "IF") {
    const branches = (config.branches as Array<{ label: string; handle: string; condition: Record<string, unknown> }>) || [];
    return (
      <div className="space-y-3">
        <label className="label block">Dallar</label>
        {branches.map((branch, i) => (
          <div key={i} className="border border-border rounded-lg p-3 space-y-2">
            <div className="flex items-center gap-2">
              <input className="input text-xs" placeholder="Etiket" value={branch.label} onChange={e => {
                const nb = [...branches]; nb[i] = { ...nb[i], label: e.target.value }; onChange("branches", nb);
              }} />
              <input className="input text-xs font-mono" placeholder="Handle" value={branch.handle} onChange={e => {
                const nb = [...branches]; nb[i] = { ...nb[i], handle: e.target.value }; onChange("branches", nb);
              }} />
            </div>
            <div>
              <label className="text-[10px] text-accent-muted">Koşul (JSON)</label>
              <textarea
                className="input text-xs font-mono resize-none mt-1"
                rows={3}
                value={JSON.stringify(branch.condition || {}, null, 2)}
                onChange={e => {
                  try {
                    const nb = [...branches]; nb[i] = { ...nb[i], condition: JSON.parse(e.target.value) }; onChange("branches", nb);
                  } catch { /* invalid JSON */ }
                }}
              />
            </div>
          </div>
        ))}
        <button className="btn-secondary text-xs w-full" onClick={() => onChange("branches", [...branches, { label: "Yeni Dal", handle: `branch_${branches.length}`, condition: {} }])}>
          + Dal Ekle
        </button>
      </div>
    );
  }

  if (engineType === "Calculate") {
    const calcs = (config.calculations as Array<{ output_field: string; expression: string }>) || [];
    return (
      <div className="space-y-3">
        <label className="label block">Hesaplamalar</label>
        {calcs.map((c, i) => (
          <div key={i} className="border border-border rounded-lg p-3 space-y-2">
            <input className="input text-xs font-mono" placeholder="Çıkış alanı (calc.total)" value={c.output_field} onChange={e => {
              const nc = [...calcs]; nc[i] = { ...nc[i], output_field: e.target.value }; onChange("calculations", nc);
            }} />
            <input className="input text-xs font-mono" placeholder="{{ form.amount }} * 1.20" value={c.expression} onChange={e => {
              const nc = [...calcs]; nc[i] = { ...nc[i], expression: e.target.value }; onChange("calculations", nc);
            }} />
          </div>
        ))}
        <button className="btn-secondary text-xs w-full" onClick={() => onChange("calculations", [...calcs, { output_field: "", expression: "" }])}>
          + Hesaplama Ekle
        </button>
      </div>
    );
  }

  if (["SetFields", "Transform"].includes(engineType)) {
    const mappings = (config.mappings as Array<{ target: string; source: string }>) || [];
    return (
      <div className="space-y-3">
        <label className="label block">Alan Eşlemeleri</label>
        {mappings.map((m, i) => (
          <div key={i} className="border border-border rounded-lg p-3 space-y-2">
            <input className="input text-xs font-mono" placeholder="Hedef (form.field)" value={m.target} onChange={e => {
              const nm = [...mappings]; nm[i] = { ...nm[i], target: e.target.value }; onChange("mappings", nm);
            }} />
            <input className="input text-xs font-mono" placeholder="Kaynak ({{ form.x }})" value={m.source} onChange={e => {
              const nm = [...mappings]; nm[i] = { ...nm[i], source: e.target.value }; onChange("mappings", nm);
            }} />
          </div>
        ))}
        <button className="btn-secondary text-xs w-full" onClick={() => onChange("mappings", [...mappings, { target: "", source: "" }])}>
          + Eşleme Ekle
        </button>
      </div>
    );
  }

  if (engineType === "HTTPRequest") {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">URL</label>
          <input className="input text-xs" value={(config.url as string) || ""} onChange={e => onChange("url", e.target.value)} placeholder="https://api.example.com/..." />
        </div>
        <div>
          <label className="label mb-1.5 block">Method</label>
          <select className="input text-xs" value={(config.method as string) || "POST"} onChange={e => onChange("method", e.target.value)}>
            {["GET", "POST", "PUT", "PATCH", "DELETE"].map(m => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className="label mb-1.5 block">Çıkış Anahtarı</label>
          <input className="input text-xs font-mono" value={(config.output_key as string) || ""} onChange={e => onChange("output_key", e.target.value)} placeholder="gen.response" />
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="mock" checked={(config.mock as boolean) !== false} onChange={e => onChange("mock", e.target.checked)} />
          <label htmlFor="mock" className="text-xs font-medium text-accent-muted">Mock Mod (Demo)</label>
        </div>
      </div>
    );
  }

  if (engineType === "End") {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">Bitiş Durumu</label>
          <select className="input text-xs" value={(config.status as string) || "completed"} onChange={e => onChange("status", e.target.value)}>
            <option value="completed">Tamamlandı</option>
            <option value="rejected">Reddedildi</option>
            <option value="cancelled">İptal</option>
          </select>
        </div>
      </div>
    );
  }

  if (engineType === "SubprocessCall") {
    return (
      <div className="space-y-3">
        <div>
          <label className="label mb-1.5 block">Alt Süreç ID</label>
          <input className="input text-xs font-mono" value={(config.subprocess_flow_id as string) || ""} onChange={e => onChange("subprocess_flow_id", e.target.value)} placeholder="flow_uuid" />
        </div>
        <div>
          <label className="label mb-1.5 block">Input Mapping (JSON)</label>
          <textarea
            className="input text-xs font-mono resize-none"
            rows={4}
            value={JSON.stringify(config.input_mapping || {}, null, 2)}
            onChange={e => { try { onChange("input_mapping", JSON.parse(e.target.value)); } catch { /* invalid */ } }}
          />
        </div>
        <div>
          <label className="label mb-1.5 block">Output Mapping (JSON)</label>
          <textarea
            className="input text-xs font-mono resize-none"
            rows={4}
            value={JSON.stringify(config.output_mapping || {}, null, 2)}
            onChange={e => { try { onChange("output_mapping", JSON.parse(e.target.value)); } catch { /* invalid */ } }}
          />
        </div>
      </div>
    );
  }

  // Generic JSON editor for unknown types
  return (
    <div>
      <label className="label mb-1.5 block">Konfigürasyon (JSON)</label>
      <textarea
        className="input text-xs font-mono resize-none"
        rows={8}
        value={JSON.stringify(config, null, 2)}
        onChange={e => { try { const c = JSON.parse(e.target.value); Object.keys(c).forEach(k => onChange(k, c[k])); } catch { /* invalid */ } }}
      />
    </div>
  );
}

function RoleSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const roles = ["admin", "approver", "viewer", "procurement", "finance", "legal"];
  return (
    <select className="input text-xs" value={value} onChange={e => onChange(e.target.value)}>
      <option value="">— Seçiniz —</option>
      {roles.map(r => <option key={r} value={r}>{r}</option>)}
    </select>
  );
}
