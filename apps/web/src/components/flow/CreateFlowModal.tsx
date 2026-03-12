"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { toast } from "sonner";
import { X } from "lucide-react";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export function CreateFlowModal({ onClose, onCreated }: Props) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const res = await api.post("/flows", { name: name.trim(), description: description.trim() });
      toast.success("Akış oluşturuldu");
      onCreated();
      router.push(`/design/${res.data.id}`);
    } catch {
      toast.error("Akış oluşturulamadı");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md animate-scale-in">
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h3 className="text-sm font-semibold text-accent">Yeni Akış Oluştur</h3>
          <button onClick={onClose} className="btn-icon text-accent-muted">
            <X size={16} />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="label mb-1.5 block">Akış Adı</label>
            <input
              className="input"
              placeholder="örn. Yeni Çalışan İşe Alım Süreci"
              value={name}
              onChange={e => setName(e.target.value)}
              autoFocus
              onKeyDown={e => e.key === "Enter" && handleCreate()}
            />
          </div>
          <div>
            <label className="label mb-1.5 block">Açıklama (opsiyonel)</label>
            <textarea
              className="input resize-none"
              rows={3}
              placeholder="Bu akış ne yapar?"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>
        </div>
        <div className="px-6 pb-5 flex items-center justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn-primary" onClick={handleCreate} disabled={!name.trim() || loading}>
            {loading ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : null}
            Oluştur ve Tasarla
          </button>
        </div>
      </div>
    </div>
  );
}
