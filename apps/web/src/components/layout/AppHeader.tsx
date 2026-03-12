"use client";
import { usePathname } from "next/navigation";
import { Bell } from "lucide-react";

const ROUTE_TITLES: Record<string, { title: string; desc: string }> = {
  "/dashboard": { title: "İzleme", desc: "Süreç performansı ve bekleyen görevler" },
  "/design": { title: "Tasarım Stüdyosu", desc: "Flow Designer ve Form Builder" },
  "/processes": { title: "Süreçler", desc: "Tüm süreç örnekleri" },
  "/inbox": { title: "Onaylarım", desc: "Bekleyen görevler ve onaylar" },
  "/users": { title: "Kullanıcılar", desc: "Kullanıcı ve yetki yönetimi" },
  "/audit": { title: "Denetim Günlüğü", desc: "Değiştirilemez olay akışı" },
  "/settings": { title: "Ayarlar", desc: "Sistem konfigürasyonu" },
};

export function AppHeader() {
  const pathname = usePathname();

  const matchKey = Object.keys(ROUTE_TITLES).find(k => pathname === k || pathname.startsWith(k + "/")) || "/dashboard";
  const { title, desc } = ROUTE_TITLES[matchKey] || { title: "e-Flow", desc: "" };

  return (
    <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 bg-surface border-b border-border">
      <div>
        <h1 className="text-sm font-semibold text-accent">{title}</h1>
        <p className="text-xs text-accent-muted">{desc}</p>
      </div>
      <div className="flex items-center gap-2">
        <button className="btn-icon relative text-accent-muted hover:text-accent">
          <Bell size={16} />
        </button>
      </div>
    </header>
  );
}
