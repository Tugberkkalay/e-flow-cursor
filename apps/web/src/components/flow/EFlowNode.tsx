"use client";
import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { nodeTypeColor } from "@/lib/utils";
import { NODE_REGISTRY } from "@/lib/nodeRegistry";

interface NodeData {
  label: string;
  engineType: string;
  category: string;
  config: Record<string, unknown>;
  selected?: boolean;
}

const CATEGORY_ICONS: Record<string, string> = {
  triggers: "▶",
  human: "👤",
  approval: "✅",
  logic: "⚡",
  data: "📊",
  integrations: "🔗",
  compliance: "🛡",
  events: "⏹",
};

function EFlowNodeComponent({ data, selected }: NodeProps<NodeData>) {
  const colors = nodeTypeColor(data.engineType);
  const def = NODE_REGISTRY.find(n => n.engineType === data.engineType);
  const icon = def?.icon || CATEGORY_ICONS[data.category] || "•";
  const isBranching = def?.isBranching;
  const outputs = def?.outputs || [];

  const isStartNode = ["ManualStart", "FormSubmitTrigger", "APITrigger", "ScheduledTrigger"].includes(data.engineType);
  const isEndNode = data.engineType === "End";
  const isStopError = data.engineType === "StopError";

  return (
    <div
      className={`
        relative rounded-xl border-2 transition-all duration-150 min-w-[160px] max-w-[200px]
        ${colors.bg} ${selected ? "border-accent shadow-node-selected" : `${colors.border} shadow-node`}
        ${selected ? "ring-0" : ""}
      `}
      style={{ fontFamily: "inherit" }}
    >
      {/* Input handle */}
      {!isStartNode && (
        <Handle
          type="target"
          position={Position.Top}
          id="in"
          className="!w-3 !h-3 !bg-white !border-2 !border-current !rounded-full"
          style={{ top: -6 }}
        />
      )}

      {/* Content */}
      <div className="px-3.5 py-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm leading-none">{icon}</span>
          <span className={`text-xs font-semibold ${colors.text} truncate`}>{data.label}</span>
        </div>
        {data.engineType && (
          <div className="text-[10px] text-gray-400 font-mono truncate">{data.engineType}</div>
        )}
      </div>

      {/* Output handles */}
      {!isEndNode && !isStopError && (
        <>
          {isBranching && outputs.length > 1 ? (
            <>
              {outputs.map((out, i) => {
                const totalW = outputs.length;
                const pct = ((i + 1) / (totalW + 1)) * 100;
                return (
                  <Handle
                    key={out.id}
                    type="source"
                    position={Position.Bottom}
                    id={out.id}
                    className="!w-3 !h-3 !bg-white !border-2 !border-current !rounded-full"
                    style={{ bottom: -6, left: `${pct}%` }}
                  >
                    <div
                      className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-gray-400 whitespace-nowrap font-medium"
                      style={{ pointerEvents: "none" }}
                    >
                      {out.label}
                    </div>
                  </Handle>
                );
              })}
            </>
          ) : (
            <Handle
              type="source"
              position={Position.Bottom}
              id="out"
              className="!w-3 !h-3 !bg-white !border-2 !border-current !rounded-full"
              style={{ bottom: -6 }}
            />
          )}
        </>
      )}

      {/* Selected indicator */}
      {selected && (
        <div className={`absolute inset-0 rounded-xl pointer-events-none ring-2 ring-accent/30`} />
      )}
    </div>
  );
}

export const EFlowNode = memo(EFlowNodeComponent);
