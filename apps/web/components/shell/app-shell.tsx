"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowRightLeft,
  FileText,
  FolderCog,
  Gauge,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Izleme", icon: Gauge },
  { href: "/design", label: "Tasarim", icon: FolderCog },
  { href: "/processes", label: "Surecler", icon: ArrowRightLeft },
  { href: "/inbox", label: "Onaylarim", icon: Activity },
  { href: "/users", label: "Kullanicilar", icon: Users },
  { href: "/audit", label: "Denetim", icon: ShieldCheck },
  { href: "/settings", label: "Ayarlar", icon: Settings },
];

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#f7f8fa]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1700px] gap-6 px-4 py-4 md:px-6 xl:px-8">
        <aside className="hidden w-[286px] shrink-0 rounded-[32px] border border-slate-200/80 bg-white px-5 py-6 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.34)] lg:flex lg:flex-col">
          <div className="flex items-center justify-between gap-3 px-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                e-Flow Enterprise
              </div>
              <div className="mt-2 text-2xl font-semibold text-slate-950">
                Workflow OS
              </div>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
              <FileText className="h-5 w-5" />
            </div>
          </div>

          <div className="mt-6 px-3">
            <Badge tone="muted">Production-grade MVP</Badge>
          </div>

          <nav className="mt-8 space-y-1">
            {nav.map((item) => {
              const Icon = item.icon;
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium text-slate-500 transition-all duration-200",
                    active
                      ? "bg-slate-950 text-white shadow-[0_22px_50px_-30px_rgba(15,23,42,0.65)]"
                      : "hover:bg-slate-50 hover:text-slate-950",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-auto rounded-[28px] border border-slate-200 bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-900">
              Lazy BPM Engine
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Runtime path resolution, approval matrix, immutable audit ve
              template akislari ayni cekirdekte calisiyor.
            </p>
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col gap-6">
          <header className="flex flex-col justify-between gap-4 rounded-[32px] border border-slate-200/80 bg-white px-6 py-5 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.24)] md:flex-row md:items-center">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Enterprise BPM / Workflow Automation
              </div>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
                Apple-like control room for enterprise operations
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <Badge tone="success">Audit immutable</Badge>
              <Badge tone="default">RBAC enabled</Badge>
              <Badge tone="warning">Node versioning ready</Badge>
            </div>
          </header>
          {children}
        </main>
      </div>
    </div>
  );
}
