"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("admin@eflow.com");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);

  const QUICK_LOGINS = [
    { label: "Admin", email: "admin@eflow.com", password: "admin123" },
    { label: "Satın Alma", email: "procurement@eflow.com", password: "proc123" },
    { label: "Finans", email: "finance@eflow.com", password: "fin123" },
    { label: "Hukuk", email: "legal@eflow.com", password: "leg123" },
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      login(res.data.access_token, res.data.user);
      toast.success("Giriş başarılı");
      router.push("/dashboard");
    } catch {
      toast.error("Geçersiz kullanıcı adı veya şifre");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-[420px]">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary shadow-lg mb-4">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M6 14L11 19L22 8" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="14" cy="14" r="12" stroke="white" strokeWidth="1.5" opacity="0.3"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-accent tracking-tight">e-Flow Enterprise</h1>
          <p className="text-sm text-accent-muted mt-1">İş Akışı Otomasyon Platformu</p>
        </div>

        {/* Card */}
        <div className="card p-8">
          <h2 className="text-lg font-semibold text-accent mb-6">Giriş Yap</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label mb-1.5 block">E-posta</label>
              <input
                type="email"
                className="input"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="ornek@sirket.com"
                required
              />
            </div>

            <div>
              <label className="label mb-1.5 block">Şifre</label>
              <input
                type="password"
                className="input"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              className="btn-primary w-full mt-2"
              disabled={loading}
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : null}
              {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </button>
          </form>

          {/* Quick logins */}
          <div className="mt-6 pt-5 border-t border-border">
            <p className="text-xs text-accent-muted mb-3 uppercase tracking-wide font-medium">Hızlı Giriş (Demo)</p>
            <div className="grid grid-cols-2 gap-2">
              {QUICK_LOGINS.map(q => (
                <button
                  key={q.email}
                  type="button"
                  className="btn-secondary text-xs py-1.5 font-medium"
                  onClick={() => { setEmail(q.email); setPassword(q.password); }}
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-accent-muted mt-6">
          e-Flow Enterprise MVP · Demo Ortamı
        </p>
      </div>
    </div>
  );
}
