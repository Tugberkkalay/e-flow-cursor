"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { toast } from "sonner";
import { Plus, Users, Shield, X, Pencil, Trash2 } from "lucide-react";
import { formatRelative } from "@/lib/utils";

const ROLE_COLORS: Record<string, string> = {
  admin: "badge-error", approver: "badge-warning", viewer: "badge-neutral",
  procurement: "badge-info", finance: "badge-success", legal: "badge-info",
};

const TABS = [
  { id: "users", label: "Kullanıcılar" },
  { id: "limits", label: "Onay Limit Matrisi" },
  { id: "delegations", label: "Vekaleten" },
];

export default function UsersPage() {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState("users");
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateLimit, setShowCreateLimit] = useState(false);

  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get("/users").then(r => r.data),
  });

  const { data: limits = [] } = useQuery({
    queryKey: ["approval-limits"],
    queryFn: () => api.get("/users/approval-limits").then(r => r.data),
  });

  const deleteLimitMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/users/approval-limits/${id}`),
    onSuccess: () => { toast.success("Limit silindi"); qc.invalidateQueries({ queryKey: ["approval-limits"] }); },
  });

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-semibold text-accent">Kullanıcı Yönetimi</h2>
        <button
          className="btn-primary"
          onClick={() => activeTab === "users" ? setShowCreateUser(true) : setShowCreateLimit(true)}
        >
          <Plus size={14} />
          {activeTab === "users" ? "Kullanıcı Ekle" : "Limit Ekle"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-border mb-4">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id ? "border-accent text-accent" : "border-transparent text-accent-muted hover:text-accent"
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Users Tab */}
      {activeTab === "users" && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted">
                {["Kullanıcı", "Rol", "Departman", "Maliyet Merkezi", "Durum", "Katılım"].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((user: { id: string; email: string; full_name: string; role: string; department?: string; cost_center?: string; is_active: boolean; avatar_initials: string; created_at: string }) => (
                <tr key={user.id} className="hover:bg-muted/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-accent-soft flex items-center justify-center text-xs font-bold text-accent flex-shrink-0">
                        {user.avatar_initials}
                      </div>
                      <div>
                        <div className="font-medium text-accent">{user.full_name}</div>
                        <div className="text-xs text-accent-muted">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`badge text-xs ${ROLE_COLORS[user.role] || "badge-neutral"}`}>{user.role}</span>
                  </td>
                  <td className="px-5 py-3.5"><span className="text-xs text-accent-muted">{user.department || "—"}</span></td>
                  <td className="px-5 py-3.5"><span className="text-xs font-mono text-accent-muted">{user.cost_center || "—"}</span></td>
                  <td className="px-5 py-3.5">
                    <span className={`badge text-xs ${user.is_active ? "badge-success" : "badge-neutral"}`}>
                      {user.is_active ? "Aktif" : "Pasif"}
                    </span>
                  </td>
                  <td className="px-5 py-3.5"><span className="text-xs text-accent-muted">{formatRelative(user.created_at)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Approval Limits */}
      {activeTab === "limits" && (
        <div className="card overflow-hidden">
          <div className="px-5 py-3 bg-muted border-b border-border">
            <p className="text-xs text-accent-muted">Tutar aralığına göre otomatik onay yönlendirmesi</p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted">
                {["Min Tutar", "Max Tutar", "Para Birimi", "Onaylayıcı", "Rol", ""].map(h => (
                  <th key={h} className="text-left px-5 py-3 text-xs font-semibold text-accent-muted uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {limits.map((lim: { id: string; min_amount: number; max_amount?: number; currency: string; approver_name: string; approver_role?: string }) => (
                <tr key={lim.id} className="hover:bg-muted/50 transition-colors">
                  <td className="px-5 py-3.5 text-sm font-medium text-accent">{lim.min_amount.toLocaleString("tr-TR")} ₺</td>
                  <td className="px-5 py-3.5 text-sm text-accent-muted">{lim.max_amount ? `${lim.max_amount.toLocaleString("tr-TR")} ₺` : "Sınırsız"}</td>
                  <td className="px-5 py-3.5"><span className="badge badge-neutral text-xs">{lim.currency}</span></td>
                  <td className="px-5 py-3.5 text-sm font-medium text-accent">{lim.approver_name}</td>
                  <td className="px-5 py-3.5"><span className="text-xs text-accent-muted">{lim.approver_role || "—"}</span></td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      className="btn-icon btn-ghost text-destructive"
                      onClick={() => { if (confirm("Silinsin mi?")) deleteLimitMutation.mutate(lim.id); }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
              {limits.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-12 text-center text-sm text-accent-muted">Onay limiti tanımlı değil.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Delegations placeholder */}
      {activeTab === "delegations" && (
        <div className="card p-12 text-center">
          <Shield size={24} className="text-accent-muted mx-auto mb-3" />
          <div className="text-sm font-medium text-accent">Vekalet Yönetimi</div>
          <div className="text-xs text-accent-muted mt-1">Kullanıcı vekalet atamaları burada listelenir.</div>
        </div>
      )}

      {showCreateUser && (
        <CreateUserModal onClose={() => setShowCreateUser(false)} onCreated={() => { qc.invalidateQueries({ queryKey: ["users"] }); setShowCreateUser(false); }} />
      )}

      {showCreateLimit && (
        <CreateLimitModal users={users} onClose={() => setShowCreateLimit(false)} onCreated={() => { qc.invalidateQueries({ queryKey: ["approval-limits"] }); setShowCreateLimit(false); }} />
      )}
    </div>
  );
}

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ email: "", full_name: "", password: "pass123", role: "viewer", department: "", cost_center: "" });
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    try {
      await api.post("/users", form);
      toast.success("Kullanıcı oluşturuldu");
      onCreated();
    } catch {
      toast.error("Kullanıcı oluşturulamadı");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h3 className="text-sm font-semibold text-accent">Yeni Kullanıcı</h3>
          <button onClick={onClose} className="btn-icon text-accent-muted"><X size={16} /></button>
        </div>
        <div className="px-6 py-5 space-y-3">
          {[
            { key: "email", label: "E-posta", type: "email" },
            { key: "full_name", label: "Ad Soyad", type: "text" },
            { key: "password", label: "Şifre", type: "password" },
            { key: "department", label: "Departman", type: "text" },
            { key: "cost_center", label: "Maliyet Merkezi", type: "text" },
          ].map(f => (
            <div key={f.key}>
              <label className="label mb-1.5 block">{f.label}</label>
              <input className="input" type={f.type} value={(form as Record<string, string>)[f.key]} onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))} />
            </div>
          ))}
          <div>
            <label className="label mb-1.5 block">Rol</label>
            <select className="input" value={form.role} onChange={e => setForm(p => ({ ...p, role: e.target.value }))}>
              {["admin", "approver", "viewer", "procurement", "finance", "legal"].map(r => <option key={r}>{r}</option>)}
            </select>
          </div>
        </div>
        <div className="px-6 pb-5 flex justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn-primary" onClick={submit} disabled={loading}>Oluştur</button>
        </div>
      </div>
    </div>
  );
}

function CreateLimitModal({ users, onClose, onCreated }: { users: { id: string; full_name: string }[]; onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ min_amount: "0", max_amount: "", currency: "TRY", approver_id: "", approver_role: "", priority: "0" });
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    try {
      await api.post("/users/approval-limits", {
        min_amount: parseFloat(form.min_amount),
        max_amount: form.max_amount ? parseFloat(form.max_amount) : null,
        currency: form.currency,
        approver_id: form.approver_id,
        approver_role: form.approver_role || null,
        priority: parseInt(form.priority),
      });
      toast.success("Limit eklendi");
      onCreated();
    } catch {
      toast.error("Limit eklenemedi");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <h3 className="text-sm font-semibold text-accent">Onay Limiti Ekle</h3>
          <button onClick={onClose} className="btn-icon text-accent-muted"><X size={16} /></button>
        </div>
        <div className="px-6 py-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label mb-1.5 block">Min Tutar</label><input className="input" type="number" value={form.min_amount} onChange={e => setForm(p => ({ ...p, min_amount: e.target.value }))} /></div>
            <div><label className="label mb-1.5 block">Max Tutar</label><input className="input" type="number" placeholder="Sınırsız" value={form.max_amount} onChange={e => setForm(p => ({ ...p, max_amount: e.target.value }))} /></div>
          </div>
          <div>
            <label className="label mb-1.5 block">Onaylayıcı</label>
            <select className="input" value={form.approver_id} onChange={e => setForm(p => ({ ...p, approver_id: e.target.value }))}>
              <option value="">— Seçiniz —</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
          </div>
          <div>
            <label className="label mb-1.5 block">Onaylayıcı Rol Adı</label>
            <input className="input" value={form.approver_role} onChange={e => setForm(p => ({ ...p, approver_role: e.target.value }))} placeholder="örn. Direktör" />
          </div>
        </div>
        <div className="px-6 pb-5 flex justify-end gap-2">
          <button className="btn-secondary" onClick={onClose}>İptal</button>
          <button className="btn-primary" onClick={submit} disabled={loading || !form.approver_id}>Ekle</button>
        </div>
      </div>
    </div>
  );
}
