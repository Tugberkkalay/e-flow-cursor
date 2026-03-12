"use client";

import {
  BaseEdge,
  EdgeLabelRenderer,
  type EdgeProps,
  getSmoothStepPath,
} from "@xyflow/react";

export function SmartCurvedRoutedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  selected,
  data,
  markerEnd,
  style,
  label,
}: EdgeProps) {
  const parallelIndex = Number(data?.parallelIndex ?? 0);
  const laneOffset = parallelIndex * 18;
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 18,
    offset: 28 + Math.abs(laneOffset),
    centerX:
      Math.abs(targetX - sourceX) > Math.abs(targetY - sourceY)
        ? (sourceX + targetX) / 2 + laneOffset
        : undefined,
    centerY:
      Math.abs(targetY - sourceY) >= Math.abs(targetX - sourceX)
        ? (sourceY + targetY) / 2 + laneOffset
        : undefined,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        style={{
          stroke: selected ? "#0f172a" : "#94a3b8",
          strokeWidth: selected ? 2.4 : 1.7,
          ...style,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          }}
          className="pointer-events-none absolute rounded-full border border-slate-200 bg-white/95 px-2.5 py-1 text-[11px] font-medium text-slate-600 shadow-[0_10px_24px_-18px_rgba(15,23,42,0.4)]"
        >
          {String(label ?? data?.label ?? "")}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
