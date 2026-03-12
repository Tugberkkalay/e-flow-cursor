"use client";

import React, { useMemo } from "react";
import { BaseEdge, EdgeProps, getSmoothStepPath, useInternalNode } from "@xyflow/react";

function getSmartPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  sourcePosition: string,
  targetPosition: string
): [string, number, number] {
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);

  const borderRadius = 16;
  const offset = 40;

  if (absDx < 5 && absDy < 5) {
    return [`M ${sourceX} ${sourceY} L ${targetX} ${targetY}`, (sourceX + targetX) / 2, (sourceY + targetY) / 2];
  }

  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;

  if (sourcePosition === "bottom" || sourcePosition === "right") {
    const cY1 = sourceY + offset;
    const cY2 = targetY - offset;

    if (dy > 60) {
      const path = `M ${sourceX} ${sourceY}
        C ${sourceX} ${sourceY + offset}, ${targetX} ${targetY - offset}, ${targetX} ${targetY}`;
      return [path, midX, midY];
    }

    const goRight = dx > 0;
    const sideOffset = goRight ? Math.max(absDx, 80) : -Math.max(absDx, 80);
    const cpX = sourceX + sideOffset * 0.6;

    const path = `M ${sourceX} ${sourceY}
      C ${sourceX} ${sourceY + offset * 1.5}, ${cpX} ${midY}, ${midX} ${midY}
      S ${targetX} ${targetY - offset * 1.5}, ${targetX} ${targetY}`;
    return [path, midX, midY];
  }

  const path = `M ${sourceX} ${sourceY}
    C ${sourceX} ${sourceY + offset}, ${targetX} ${targetY - offset}, ${targetX} ${targetY}`;
  return [path, midX, midY];
}

export function SmartCurvedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  label,
  data,
  selected,
}: EdgeProps) {
  const [path, labelX, labelY] = useMemo(
    () => getSmartPath(sourceX, sourceY, targetX, targetY, sourcePosition as string, targetPosition as string),
    [sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition]
  );

  const edgeColor = selected ? "#1e293b" : (data?.color as string) || "#94a3b8";
  const strokeWidth = selected ? 2.5 : 2;

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={path}
        style={{
          ...style,
          stroke: edgeColor,
          strokeWidth,
          fill: "none",
          transition: "stroke 150ms ease, stroke-width 150ms ease",
        }}
        markerEnd={markerEnd}
      />
      <path
        d={path}
        style={{
          stroke: "transparent",
          strokeWidth: 20,
          fill: "none",
          cursor: "pointer",
        }}
      />
      {label && (
        <foreignObject
          width={120}
          height={28}
          x={labelX - 60}
          y={labelY - 14}
          requiredExtensions="http://www.w3.org/1999/xhtml"
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              height: "100%",
            }}
          >
            <span
              style={{
                background: "white",
                border: "1px solid #e2e8f0",
                borderRadius: 6,
                padding: "2px 8px",
                fontSize: 11,
                fontWeight: 500,
                color: "#475569",
                whiteSpace: "nowrap",
                boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
              }}
            >
              {label as string}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}
