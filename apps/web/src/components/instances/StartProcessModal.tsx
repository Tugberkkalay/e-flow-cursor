"use client";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "@/lib/api";
import { toast } from "sonner";
import { X, Play } from "lucide-react";
import { useRouter } from "next/navigation";

interface Props {
  onClose: () => void;
  onStarted: () => void;
}

export function StartProcessModal({ onClose, onStarted }: Props) {
  const router = useRouter();
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [title, setTitle] = useState("");
  const [inputs, setInputs] = useState<Record<string, string>>({});

  const { data: flows = [] } = useQuery({
    queryKey: ["flows"],
    queryFn: () => api.get("/flows").then(r => r.data),
  });

  const publishedFlows = flows.filter((f: { latest_version?: { status: string } }) => f.latest_version?.status === "published");

  const startMutation = useMutation({
    mutationFn: () => api.post("/instances/start", {
      flow_version_id: selectedVersionId,
      title: title || "Yeni Süreç",
      initial_inputs: inputs,
    }),
    onSuccess: (res) => {
      toast.success("Süreç başlatıldı!");
      onStarted();
      router.push(`/processes/${res.data.id}`);
    },
    onError: () => toast.error("Süreç başlatılamadı"),
  });

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-lg animate-scale-in">
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h3 className="text-sm font-semibold text-accent">Süreç Başlat</h3>
          <button onClick={onClose} className="btn-icon text-accent-muted"><X size={16} /></button>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="label mb-1.5 block">Akış Seçin</label>
            <select
              className="input"
              value={selectedVersionId}
              onChange={e => {
                const flow = flows.find((f: { latest_version?: { id: string }; name: string }) => f.latest_version?.id === e.target.value);
                setSelectedVersionId(e.target.value);
                if (flow && !title) setTitle(flow.name);
              }}
            >
              <option value="">— Yayınlanmış akış seçin —</option>
              {publishedFlows.map((f: { id: string; name: string; latest_version?: { id: string } }) => (
                <option key={f.id} value={f.latest_version?.id}>{f.name}</option>
              ))}
            </select>
            {publishedFlows.length === 0 && (
              <p className="text-xs text-warning-foreground mt-1">Yayınlanmış akış bulunamadı. Önce bir akışı yayınlayın.</p>
            )}
          </div>

          <div>
            <label className="label mb-1.5 block">Süreç Başlığı</label>
            <input
              className="input"
              placeholder="Bu sürece bir başlık verin"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
          </div>

          {/* Initial inputs */}
          <div>
            <label className="label mb-2 block">Başlangıç Verileri</label>
            <div className="border border-border rounded-lg overflow-hidden">
              <div className="grid grid-cols-2 gap-0">
                {["title", "total_amount", "currency", "request_type", "vendor_name", "description"].map(key => (
                  <div key={key} className="flex flex-col gap-0.5 p-3 border-b border-r border-border last:border-r-0">
                    <label className="text-[10px] font-mono text-accent-muted">{key}</label>
                    <input
                      className="text-xs bg-transparent outline-none text-accent"
                      placeholder={key === "total_amount" ? "0" : key === "currency" ? "TRY" : ""}
                      value={inputs[key] || ""}
                      onChange={e => setInputs(prev => ({ ...prev, [key]: e.target.value }))}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 pb-5 flex items-center justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>İptal</button>
          <button
            className="btn-primary"
            disabled={!selectedVersionId || startMutation.isPending}
            onClick={() => startMutation.mutate()}
          >
            <Play size={13} />
            {startMutation.isPending ? "Başlatılıyor..." : "Süreç Başlat"}
          </button>
        </div>
      </div>
    </div>
  );
}
