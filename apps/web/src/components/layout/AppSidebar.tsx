"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Workflow, ClipboardList, CheckSquare,
  Users, Shield, Settings, LogOut, Zap, ChevronRight,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "İzleme", href: "/dashboard", icon: LayoutDashboard },
  { label: "Tasarım", href: "/design", icon: Workflow },
  { label: "Süreçler", href: "/processes", icon: ClipboardList },
  { label: "Onaylarım", href: "/inbox", icon: CheckSquare },
  { label: "Kullanıcılar", href: "/users", icon: Users },
  { label: "Denetim", href: "/audit", icon: Shield },
  { label: "Ayarlar", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-[220px] flex-shrink-0 bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <Zap size={15} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-accent tracking-tight">e-Flow</div>
            <div className="text-[10px] text-accent-muted font-medium uppercase tracking-wider">Enterprise</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href}>
              <div className={cn(active ? "sidebar-item-active" : "sidebar-item")}>
                <Icon size={16} className="flex-shrink-0" />
                <span className="flex-1">{label}</span>
                {active && <ChevronRight size={14} className="opacity-40" />}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-3 pb-4 border-t border-border pt-3">
        {user && (
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg">
            <div className="w-7 h-7 rounded-full bg-accent-soft flex items-center justify-center text-xs font-bold text-accent flex-shrink-0">
              {user.avatar_initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-accent truncate">{user.full_name}</div>
              <div className="text-[10px] text-accent-muted truncate capitalize">{user.role}</div>
            </div>
            <button
              onClick={logout}
              className="p-1 rounded hover:bg-surface-hover text-accent-muted hover:text-accent transition-colors"
              title="Çıkış"
            >
              <LogOut size={13} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
