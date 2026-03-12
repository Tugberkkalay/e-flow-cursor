"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAppStore } from "@/store";
import { FlowCanvas } from "@/components/flow/flow-canvas";
import {
  Save,
  Upload,
  ArrowLeft,
  FileText,
  ChevronDown,
} from "lucide-react";
import Link from "next/link";
import { statusColor } from "@/lib/utils";

export default function FlowDesignerPage() {
  const { currentFlow } = useAppStore();
  const flowName = currentFlow?.name || "Yeni Akış";
  const flowStatus = currentFlow?.status || "draft";
  const flowVersion = currentFlow?.current_version || 1;

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Top Bar */}
      <header className="flex h-12 items-center justify-between border-b bg-white px-4 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/designer">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold">{flowName}</h1>
            <Badge variant="outline" className={statusColor(flowStatus)}>
              {flowStatus === "published" ? "Yayında" : "Taslak"}
            </Badge>
            <span className="text-xs text-muted-foreground">v{flowVersion}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs">
            <FileText className="h-3.5 w-3.5" />
            Form Bağla
          </Button>
          <Button variant="outline" size="sm" className="h-8 gap-1.5 text-xs">
            <Save className="h-3.5 w-3.5" />
            Kaydet
          </Button>
          <Button size="sm" className="h-8 gap-1.5 text-xs">
            <Upload className="h-3.5 w-3.5" />
            Yayınla
          </Button>
        </div>
      </header>

      {/* Canvas Area */}
      <div className="flex-1 overflow-hidden">
        <FlowCanvas />
      </div>
    </div>
  );
}
