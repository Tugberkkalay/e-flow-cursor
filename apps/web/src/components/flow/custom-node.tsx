"use client";

import React, { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { getNodeDef } from "@/lib/node-registry";
import * as LucideIcons from "lucide-react";

function getIcon(iconName: string) {
  const icons = LucideIcons as any;
  return icons[iconName] || icons.Circle;
}

function CustomNodeComponent({ data, selected, id }: NodeProps) {
  const nodeData = data as any;
  const def = getNodeDef(nodeData.nodeType);
  const Icon = getIcon(def?.icon || nodeData.icon || "Circle");
  const color = def?.color || nodeData.color || "#64748b";
  const bgColor = def?.bgColor || nodeData.bgColor || "#f8fafc";
  const hasMultipleOutputs = def?.handles?.source && def.handles.source.length > 1;

  return (
    <div
      className={cn(
        "group relative min-w-[180px] max-w-[220px] rounded-xl border bg-white transition-all duration-150",
        selected
          ? "border-primary/40 shadow-md ring-2 ring-primary/10"
          : "border-gray-200/80 shadow-sm hover:shadow-md hover:border-gray-300"
      )}
    >
      {/* Target handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-white !border-2 !border-gray-300 hover:!border-primary !-top-1.5 !rounded-full transition-colors"
      />

      {/* Node Content */}
      <div className="px-3.5 py-3">
        <div className="flex items-start gap-2.5">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
            style={{ backgroundColor: bgColor }}
          >
            <Icon className="h-4 w-4" style={{ color }} strokeWidth={1.8} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[13px] font-semibold text-gray-800 truncate leading-tight">
              {nodeData.label}
            </div>
            <div className="text-[11px] text-gray-400 mt-0.5 truncate">
              {def?.description || nodeData.description || ""}
            </div>
          </div>
        </div>

        {/* Config preview */}
        {nodeData.config?.condition && (
          <div className="mt-2 rounded-md bg-gray-50 px-2 py-1">
            <code className="text-[10px] text-gray-500 truncate block">
              {nodeData.config.condition}
            </code>
          </div>
        )}
      </div>

      {/* Source handles */}
      {hasMultipleOutputs ? (
        <div className="flex justify-around px-4">
          {def?.handles?.source.map((handleId, idx) => (
            <div key={handleId} className="relative flex flex-col items-center pb-1">
              <span className="text-[9px] font-medium text-gray-400 mb-0.5">
                {handleId === "true" ? "Evet" : handleId === "false" ? "Hayır" :
                 handleId === "approved" ? "Onay" : handleId === "rejected" ? "Red" :
                 handleId === "matched" ? "Eşleşti" : handleId === "mismatch" ? "Uyumsuz" :
                 handleId === "pass" ? "Geçti" : handleId === "fail" ? "Kaldı" :
                 handleId === "resolved" ? "Çözüldü" : handleId === "escalated" ? "Eskalasyon" :
                 handleId === "ambiguous" ? "Belirsiz" : handleId}
              </span>
              <Handle
                type="source"
                position={Position.Bottom}
                id={handleId}
                className="!relative !transform-none !w-2.5 !h-2.5 !bg-white !border-2 !rounded-full transition-colors"
                style={{
                  borderColor: handleId === "true" || handleId === "approved" || handleId === "matched" || handleId === "pass" || handleId === "resolved"
                    ? "#10b981"
                    : handleId === "false" || handleId === "rejected" || handleId === "fail" || handleId === "mismatch"
                    ? "#ef4444"
                    : "#f59e0b",
                  top: "auto",
                  left: "auto",
                }}
              />
            </div>
          ))}
        </div>
      ) : (
        <Handle
          type="source"
          position={Position.Bottom}
          className="!w-3 !h-3 !bg-white !border-2 !border-gray-300 hover:!border-primary !-bottom-1.5 !rounded-full transition-colors"
        />
      )}
    </div>
  );
}

export const CustomNode = memo(CustomNodeComponent);
