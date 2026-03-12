"use client";

import { useMemo, useState } from "react";
import {
  EdgeLabelRenderer,
  EdgeProps,
  Position,
  getBezierPath,
  useStore,
} from "@xyflow/react";

function intersectsRect(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  rect: { x: number; y: number; w: number; h: number },
) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  return (
    mx >= rect.x - 16 &&
    mx <= rect.x + rect.w + 16 &&
    my >= rect.y - 16 &&
    my <= rect.y + rect.h + 16
  );
}

function customCurvePath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  parallelOffset: number,
  obstacleYOffset: number,
) {
  const dx = targetX - sourceX;
  const cx1 = sourceX + dx * 0.25 + parallelOffset;
  const cx2 = sourceX + dx * 0.75 + parallelOffset;
  const cy1 = sourceY + obstacleYOffset;
  const cy2 = targetY + obstacleYOffset;
  return `M ${sourceX},${sourceY} C ${cx1},${cy1} ${cx2},${cy2} ${targetX},${targetY}`;
}

export function SmartCurvedRoutedEdge({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  selected,
  data,
}: EdgeProps) {
  const [hovered, setHovered] = useState(false);
  const nodes = useStore((state) => state.nodes);
  const edges = useStore((state) => state.edges);

  const { path, labelX, labelY } = useMemo(() => {
    const siblings = edges.filter((edge) => edge.source === source && edge.target === target);
    const index = siblings.findIndex((edge) => edge.id === id);
    const parallelOffset =
      siblings.length > 1 ? (index - (siblings.length - 1) / 2) * 24 : 0;

    const hasObstacle = nodes.some((node) => {
      if (node.id === source || node.id === target) return false;
      const rect = {
        x: node.position.x,
        y: node.position.y,
        w: node.width ?? 180,
        h: node.height ?? 70,
      };
      return intersectsRect(sourceX, sourceY, targetX, targetY, rect);
    });

    const obstacleYOffset = hasObstacle ? 72 : 0;
    const curvedPath = customCurvePath(
      sourceX,
      sourceY,
      targetX,
      targetY,
      parallelOffset,
      obstacleYOffset,
    );

    const [bezierPath, , by] = getBezierPath({
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourcePosition: sourcePosition ?? Position.Right,
      targetPosition: targetPosition ?? Position.Left,
    });

    return {
      path: hasObstacle || siblings.length > 1 ? curvedPath : bezierPath,
      labelX: (sourceX + targetX) / 2 + parallelOffset * 0.2,
      labelY: hasObstacle ? (sourceY + targetY) / 2 + 24 : by,
    };
  }, [
    edges,
    id,
    nodes,
    source,
    sourceX,
    sourceY,
    sourcePosition,
    target,
    targetX,
    targetY,
    targetPosition,
  ]);

  const label = String(data?.label ?? "");
  return (
    <>
      <path
        id={id}
        d={path}
        fill="none"
        stroke={selected || hovered ? "#223248" : "#8EA1BD"}
        strokeWidth={selected || hovered ? 2.6 : 1.8}
        markerEnd={markerEnd}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{ transition: "stroke 180ms ease, stroke-width 180ms ease" }}
      />
      {label ? (
        <EdgeLabelRenderer>
          <div
            className="pointer-events-none absolute rounded-md border border-[#E3E9F2] bg-white px-1.5 py-0.5 text-[11px] font-medium text-[#415166] shadow-sm"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
