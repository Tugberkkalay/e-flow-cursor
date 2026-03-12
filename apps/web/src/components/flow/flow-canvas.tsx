"use client";

import React, { useCallback, useRef, useMemo } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  Edge,
  ReactFlowProvider,
  useReactFlow,
  Panel,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { CustomNode } from "./custom-node";
import { SmartCurvedEdge } from "./smart-edge";
import { NodePalette } from "./node-palette";
import { PropertiesPanel } from "./properties-panel";
import { useAppStore } from "@/store";
import { NodeDefinition, getNodeDef } from "@/lib/node-registry";
import { Button } from "@/components/ui/button";
import { Maximize2, LayoutGrid } from "lucide-react";

const nodeTypes = {
  customNode: CustomNode,
};

const edgeTypes = {
  smartEdge: SmartCurvedEdge,
};

const defaultEdgeOptions = {
  type: "smartEdge",
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 16,
    height: 16,
    color: "#94a3b8",
  },
  style: { stroke: "#94a3b8", strokeWidth: 2 },
};

function FlowCanvasInner() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition, fitView } = useReactFlow();
  const {
    nodes: storeNodes,
    edges: storeEdges,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    selectedNodeId,
    setSelectedNodeId,
  } = useAppStore();

  const [nodes, setNodes, onNodesChange] = useNodesState(storeNodes as unknown as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges as unknown as Edge[]);

  React.useEffect(() => {
    setNodes(storeNodes as unknown as Node[]);
  }, [storeNodes, setNodes]);

  React.useEffect(() => {
    setEdges(storeEdges as unknown as Edge[]);
  }, [storeEdges, setEdges]);

  React.useEffect(() => {
    setStoreNodes(nodes as unknown as any[]);
  }, [nodes, setStoreNodes]);

  React.useEffect(() => {
    setStoreEdges(edges as unknown as any[]);
  }, [edges, setStoreEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      const sourceNode = nodes.find((n) => n.id === connection.source);
      const sourceNodeDef = sourceNode ? getNodeDef((sourceNode.data as any).nodeType) : null;

      let label: string | undefined;
      if (connection.sourceHandle) {
        const handleLabels: Record<string, string> = {
          true: "Evet",
          false: "Hayır",
          approved: "Onaylandı",
          rejected: "Reddedildi",
          matched: "Eşleşti",
          mismatch: "Uyumsuz",
          ambiguous: "Belirsiz",
          pass: "Geçti",
          fail: "Kaldı",
          resolved: "Çözüldü",
          escalated: "Eskalasyon",
        };
        label = handleLabels[connection.sourceHandle] || connection.sourceHandle;
      }

      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            type: "smartEdge",
            label,
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 16,
              height: 16,
              color: "#94a3b8",
            },
          },
          eds
        )
      );
    },
    [nodes, setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNodeId(node.id);
    },
    [setSelectedNodeId]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, [setSelectedNodeId]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const nodeDefJson = event.dataTransfer.getData("application/reactflow");
      if (!nodeDefJson) return;

      const nodeDef: NodeDefinition = JSON.parse(nodeDefJson);
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: `node_${Date.now()}`,
        type: "customNode",
        position,
        data: {
          label: nodeDef.label,
          nodeType: nodeDef.type,
          engineType: nodeDef.engineType,
          category: nodeDef.category,
          config: { ...nodeDef.defaultConfig },
          icon: nodeDef.icon,
          color: nodeDef.color,
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [screenToFlowPosition, setNodes]
  );

  const onDragStartPalette = useCallback(
    (event: React.DragEvent, nodeDef: NodeDefinition) => {
      event.dataTransfer.setData("application/reactflow", JSON.stringify(nodeDef));
      event.dataTransfer.effectAllowed = "move";
    },
    []
  );

  const handleDeleteNode = useCallback(
    (id: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== id));
      setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
      setSelectedNodeId(null);
    },
    [setNodes, setEdges, setSelectedNodeId]
  );

  return (
    <div className="flex h-full">
      {/* Node Palette */}
      <div className="w-[260px] border-r shrink-0 overflow-hidden">
        <NodePalette onDragStart={onDragStartPalette} />
      </div>

      {/* Canvas */}
      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          snapToGrid
          snapGrid={[16, 16]}
          className="bg-[#F7F8FA]"
          proOptions={{ hideAttribution: true }}
          deleteKeyCode={["Backspace", "Delete"]}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#dde1e7" />
          <MiniMap
            nodeColor={(node) => {
              const def = getNodeDef((node.data as any)?.nodeType);
              return def?.color || "#94a3b8";
            }}
            style={{ width: 150, height: 100 }}
            maskColor="rgba(247, 248, 250, 0.8)"
          />
          <Controls showInteractive={false} />
          <Panel position="top-right" className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 shadow-sm bg-white"
              onClick={() => fitView({ padding: 0.2, duration: 200 })}
            >
              <Maximize2 className="h-3.5 w-3.5 mr-1.5" />
              Sığdır
            </Button>
          </Panel>
        </ReactFlow>
      </div>

      {/* Properties Panel */}
      {selectedNodeId && (
        <PropertiesPanel
          onClose={() => setSelectedNodeId(null)}
          onDelete={handleDeleteNode}
        />
      )}
    </div>
  );
}

export function FlowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  );
}
