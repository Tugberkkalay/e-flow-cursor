"use client";
import { useAuthStore } from "@/store/auth";
import { Settings, Zap } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuthStore();

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="card p-6">
        <h3 className="text-sm font-semibold text-accent mb-4">Sistem Bilgileri</h3>
        <div className="space-y-3">
          {[
            { label: "Uygulama", value: "e-Flow Enterprise" },
            { label: "Sürüm", value: "1.0.0 MVP" },
            { label: "Ortam", value: "Demo" },
            { label: "API", value: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" },
          ].map(item => (
            <div key={item.label} className="flex items-center gap-4">
              <span className="text-xs font-medium text-accent-muted w-24">{item.label}</span>
              <span className="text-sm text-accent">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-sm font-semibold text-accent mb-4">Aktif Oturum</h3>
        {user ? (
          <div className="space-y-3">
            {[
              { label: "Ad Soyad", value: user.full_name },
              { label: "E-posta", value: user.email },
              { label: "Rol", value: user.role },
              { label: "Departman", value: user.department || "—" },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-4">
                <span className="text-xs font-medium text-accent-muted w-24">{item.label}</span>
                <span className="text-sm text-accent">{item.value}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-accent-muted">Oturum bulunamadı.</div>
        )}
      </div>

      <div className="card p-6">
        <h3 className="text-sm font-semibold text-accent mb-2">Expression Engine</h3>
        <p className="text-xs text-accent-muted mb-4">Akış context değişkenlerine erişim için <code className="bg-muted px-1 rounded font-mono">{`{{ expr }}`}</code> sözdizimini kullanın.</p>
        <div className="bg-muted rounded-lg p-3 text-xs font-mono space-y-1 text-accent-muted">
          <div><span className="text-info-foreground">{`{{ form.total_amount }}`}</span> → Form değerine erişim</div>
          <div><span className="text-info-foreground">{`{{ form.amount * 1.20 }}`}</span> → Hesaplama</div>
          <div><span className="text-info-foreground">{`{{ approval.last_decision }}`}</span> → Onay kararı</div>
          <div><span className="text-info-foreground">{`{{ calc.normalized_amount }}`}</span> → Hesaplanan değer</div>
          <div><span className="text-info-foreground">{`{{ flags.match_status }}`}</span> → Flag değerleri</div>
        </div>
      </div>
    </div>
  );
}
