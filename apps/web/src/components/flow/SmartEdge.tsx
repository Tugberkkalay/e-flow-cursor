"use client";
import { memo } from "react";
import { EdgeProps, getSmoothStepPath, EdgeLabelRenderer, BaseEdge } from "reactflow";

interface SmartEdgeData {
  label?: string;
  animated?: boolean;
}

function SmartEdgeComponent({
  id, sourceX, sourceY, targetX, targetY,
  sourcePosition, targetPosition, data, selected, label,
  markerEnd,
}: EdgeProps<SmartEdgeData>) {
  // Compute a smart smoothstep path
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX, sourceY, targetX, targetY,
    sourcePosition, targetPosition,
    borderRadius: 12,
    offset: 24,
  });

  const edgeLabel = label || data?.label;
  const strokeColor = selected ? "#1A1F36" : "#D1D5DB";
  const strokeWidth = selected ? 2 : 1.5;

  return (
    <>
      {/* Shadow/glow for selected */}
      {selected && (
        <BaseEdge
          path={edgePath}
          style={{ stroke: "#1A1F36", strokeWidth: 4, strokeOpacity: 0.1 }}
        />
      )}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: strokeColor,
          strokeWidth,
          strokeDasharray: data?.animated ? "6 3" : undefined,
        }}
      />

      {edgeLabel && (
        <EdgeLabelRenderer>
          <div
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
            className="absolute nodrag nopan"
          >
            <div className="bg-surface border border-border rounded-md px-2 py-0.5 text-[10px] font-medium text-accent-muted shadow-xs whitespace-nowrap">
              {edgeLabel}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export const SmartEdge = memo(SmartEdgeComponent);
