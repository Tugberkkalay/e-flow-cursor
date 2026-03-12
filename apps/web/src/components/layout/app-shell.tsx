"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store";
import { Sidebar } from "./sidebar";
import { TopBar } from "./top-bar";

interface AppShellProps {
  children: React.ReactNode;
  fullWidth?: boolean;
}

export function AppShell({ children, fullWidth }: AppShellProps) {
  const { sidebarCollapsed } = useAppStore();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          "sidebar-transition",
          sidebarCollapsed ? "ml-[68px]" : "ml-[240px]"
        )}
      >
        <TopBar />
        <main className={cn("min-h-[calc(100vh-56px)]", !fullWidth && "p-6")}>
          {children}
        </main>
      </div>
    </div>
  );
}
