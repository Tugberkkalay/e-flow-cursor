"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Cog,
  FileText,
  LayoutDashboard,
  ListChecks,
  Palette,
  Shield,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "İzleme", icon: LayoutDashboard },
  { href: "/design", label: "Tasarım", icon: Palette },
  { href: "/processes", label: "Süreçler", icon: Activity },
  { href: "/inbox", label: "Onaylarım", icon: ListChecks },
  { href: "/users", label: "Kullanıcılar", icon: Users },
  { href: "/audit", label: "Denetim", icon: Shield },
  { href: "/settings", label: "Ayarlar", icon: Cog },
];

export function AppShell({
  title,
  subtitle,
  children,
  actionSlot,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  actionSlot?: React.ReactNode;
}) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-[#F7F8FA] text-[#142033]">
      <div className="mx-auto flex max-w-[1600px] gap-4 px-4 py-4 lg:px-6">
        <aside className="sticky top-4 h-[calc(100vh-2rem)] w-64 rounded-2xl border border-[#E7EBF0] bg-white p-4 shadow-[0_8px_30px_rgba(16,24,40,0.06)]">
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-[#EEF1F5] bg-[#FBFCFE] p-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1E2A38] text-white">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold">e-Flow Enterprise</p>
              <p className="text-xs text-[#5A6678]">BPM Automation</p>
            </div>
          </div>
          <nav className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={item.label}
                  className={cn(
                    "group flex items-center gap-2.5 rounded-xl border px-3 py-2 text-sm font-medium transition-all duration-200 ease-out",
                    active
                      ? "border-[#CAD6E8] bg-[#EEF2FA] text-[#1E2A38] shadow-sm"
                      : "border-transparent text-[#445267] hover:border-[#E3E8F0] hover:bg-white hover:shadow-sm",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-6 rounded-xl border border-[#EDF1F7] bg-[#FAFBFD] p-3">
            <p className="text-xs text-[#5A6678]">Environment</p>
            <div className="mt-1 flex items-center gap-2">
              <Badge variant="default">MVP</Badge>
              <Badge variant="success">Draft</Badge>
            </div>
          </div>
        </aside>
        <main className="flex-1 rounded-2xl border border-[#E7EBF0] bg-white shadow-[0_8px_30px_rgba(16,24,40,0.04)]">
          <header className="flex items-center justify-between border-b border-[#EEF1F5] px-6 py-5">
            <div>
              <h1 className="text-[22px] font-semibold tracking-tight">{title}</h1>
              {subtitle ? (
                <p className="mt-1 text-sm text-[#5A6678]">{subtitle}</p>
              ) : null}
            </div>
            <div>{actionSlot}</div>
          </header>
          <section className="p-6">{children}</section>
        </main>
      </div>
    </div>
  );
}
