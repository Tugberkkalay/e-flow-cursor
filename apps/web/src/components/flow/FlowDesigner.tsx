"use client";
import { useCallback, useRef, useState, useEffect } from "react";
import ReactFlow, {
  Background, Controls, MiniMap, addEdge,
  useNodesState, useEdgesState, Node, Edge, Connection,
  MarkerType, BackgroundVariant, ReactFlowProvider, useReactFlow,
} from "reactflow";
import "reactflow/dist/style.css";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { toast } from "sonner";
import { NodePalette } from "./NodePalette";
import { PropertiesPanel } from "./PropertiesPanel";
import { EFlowNode } from "./EFlowNode";
import { SmartEdge } from "./SmartEdge";
import { Save, Play, ChevronDown, Link, LayoutDashboard, Settings2 } from "lucide-react";

const nodeTypes = { eflowNode: EFlowNode };
const edgeTypes = { smartEdge: SmartEdge };

const defaultEdgeOptions = {
  type: "smoothstep",
  markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#D1D5DB" },
  style: { stroke: "#D1D5DB", strokeWidth: 1.5 },
};

function FlowCanvas({ flowId }: { flowId: string }) {
  const qc = useQueryClient();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [flowName, setFlowName] = useState("");
  const [flowStatus, setFlowStatus] = useState<"draft" | "published" | "archived">("draft");
  const [flowVersion, setFlowVersion] = useState(1);

  const { data: flow } = useQuery({
    queryKey: ["flow", flowId],
    queryFn: () => api.get(`/flows/${flowId}`).then(r => r.data),
  });

  useEffect(() => {
    if (flow) {
      setFlowName(flow.name);
      if (flow.latest_version) {
        setFlowStatus(flow.latest_version.status);
        setFlowVersion(flow.latest_version.version_number);
        const graph = flow.latest_version.graph_json;
        if (graph?.nodes?.length) {
          setNodes(graph.nodes.map((n: Node) => ({ ...n, type: "eflowNode" })));
        }
        if (graph?.edges?.length) {
          setEdges(graph.edges.map((e: Edge) => ({
            ...e,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#D1D5DB" },
          })));
        }
      }
    }
  }, [flow?.id]);

  const saveMutation = useMutation({
    mutationFn: (graphJson: object) =>
      api.put(`/flows/${flowId}`, { graph_json: graphJson }),
    onSuccess: () => {
      toast.success("Akış kaydedildi");
      qc.invalidateQueries({ queryKey: ["flow", flowId] });
    },
  });

  const publishMutation = useMutation({
    mutationFn: () => api.post(`/flows/${flowId}/publish`),
    onSuccess: () => {
      toast.success("Akış yayınlandı!");
      setFlowStatus("published");
      qc.invalidateQueries({ queryKey: ["flow", flowId] });
    },
  });

  const handleSave = useCallback(() => {
    const graphJson = {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
        label: e.label,
        type: e.type,
      })),
    };
    saveMutation.mutate(graphJson);
  }, [nodes, edges, saveMutation]);

  const onConnect = useCallback((connection: Connection) => {
    setEdges(eds => addEdge({
      ...connection,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#D1D5DB" },
    }, eds));
  }, [setEdges]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const engineType = event.dataTransfer.getData("application/eflow-node-type");
    const label = event.dataTransfer.getData("application/eflow-node-label");
    if (!engineType) return;

    const rect = reactFlowWrapper.current?.getBoundingClientRect();
    if (!rect) return;

    const position = project({
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    });

    const newNode: Node = {
      id: `node_${Date.now()}`,
      type: "eflowNode",
      position,
      data: {
        label,
        engineType,
        category: getCategoryForType(engineType),
        config: getDefaultConfig(engineType),
      },
    };

    setNodes(nds => nds.concat(newNode));
  }, [project, setNodes]);

  const handleNodeUpdate = useCallback((nodeId: string, newData: Record<string, unknown>) => {
    setNodes(nds => nds.map(n => n.id === nodeId ? { ...n, data: { ...n.data, ...newData } } : n));
    setSelectedNode(prev => prev?.id === nodeId ? { ...prev, data: { ...prev.data, ...newData } } : prev);
  }, [setNodes]);

  const onDragStart = useCallback((event: React.DragEvent, engineType: string, label: string) => {
    event.dataTransfer.setData("application/eflow-node-type", engineType);
    event.dataTransfer.setData("application/eflow-node-label", label);
    event.dataTransfer.effectAllowed = "move";
  }, []);

  // Auto-save shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSave]);

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-surface border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <input
            className="text-sm font-semibold text-accent bg-transparent outline-none border-b border-transparent hover:border-border focus:border-accent w-[200px] py-0.5"
            value={flowName}
            onChange={e => setFlowName(e.target.value)}
            onBlur={() => api.put(`/flows/${flowId}`, { name: flowName })}
          />
          <span className={`badge text-[10px] ${flowStatus === "published" ? "badge-success" : "badge-neutral"}`}>
            {flowStatus === "published" ? "Yayında" : "Taslak"}
          </span>
          <span className="text-xs text-accent-muted">v{flowVersion}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn-secondary btn-sm"
            onClick={handleSave}
            disabled={saveMutation.isPending}
          >
            <Save size={13} />
            {saveMutation.isPending ? "Kaydediyor..." : "Kaydet"}
          </button>
          {flowStatus !== "published" && (
            <button
              className="btn-primary btn-sm"
              onClick={() => { handleSave(); setTimeout(() => publishMutation.mutate(), 500); }}
              disabled={publishMutation.isPending}
            >
              <Play size={13} />
              Yayınla
            </button>
          )}
        </div>
      </div>

      {/* Canvas area */}
      <div className="flex flex-1 overflow-hidden">
        <NodePalette onDragStart={onDragStart} />

        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            deleteKeyCode={["Backspace", "Delete"]}
            className="bg-background"
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color="#E5E7EB"
            />
            <Controls className="shadow-md" />
            <MiniMap
              nodeColor={n => {
                const engineType = n.data?.engineType || "";
                if (engineType.includes("Start") || engineType.includes("Trigger")) return "#6366F1";
                if (engineType === "End") return "#94A3B8";
                if (["IF", "Switch", "Gateway"].includes(engineType)) return "#A855F7";
                if (["ApprovalTask", "Approval", "MultiApproval"].includes(engineType)) return "#EAB308";
                return "#22C55E";
              }}
              maskColor="rgba(247,248,250,0.8)"
              style={{ borderRadius: 8 }}
            />
          </ReactFlow>

          {/* Empty state */}
          {nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <div className="text-4xl mb-3">✦</div>
                <div className="text-sm font-medium text-accent-muted">Node'ları buraya sürükleyin</div>
                <div className="text-xs text-accent-muted/60 mt-1">Sol panelden node seçip canvas'a bırakın</div>
              </div>
            </div>
          )}
        </div>

        {selectedNode && (
          <PropertiesPanel
            node={selectedNode}
            onUpdate={handleNodeUpdate}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>
    </div>
  );
}

export function FlowDesigner({ flowId }: { flowId: string }) {
  return (
    <ReactFlowProvider>
      <div className="h-full">
        <FlowCanvas flowId={flowId} />
      </div>
    </ReactFlowProvider>
  );
}

function getCategoryForType(engineType: string): string {
  if (["ManualStart", "FormSubmitTrigger", "APITrigger", "ScheduledTrigger"].includes(engineType)) return "triggers";
  if (["FormFill", "DataEntry", "DocumentUpload", "ReviewComment", "VendorSelection", "DeliveryAcceptance"].includes(engineType)) return "human";
  if (["ApprovalTask", "Approval", "MultiApproval", "ApprovalByLimitMatrix"].includes(engineType)) return "approval";
  if (["IF", "Switch", "ParallelSplit", "ParallelJoin", "Gateway"].includes(engineType)) return "logic";
  if (["Calculate", "SetFields", "Transform", "NormalizeMoney", "ThreeWayMatch"].includes(engineType)) return "data";
  if (["HTTPRequest", "EmailSend", "ERPAdapter", "SubprocessCall"].includes(engineType)) return "integrations";
  if (["AuditEmit", "StopError", "PolicyCheck"].includes(engineType)) return "compliance";
  return "events";
}

function getDefaultConfig(engineType: string): Record<string, unknown> {
  const NODE_REGISTRY_MAP: Record<string, Record<string, unknown>> = {
    FormFill: { title: "Form Doldur", assignee_role: "" },
    DocumentUpload: { title: "Belge Yükle", doc_type: "generic", min_count: 1, assignee_role: "" },
    ApprovalTask: { title: "Onay Bekliyor", approver_role: "approver" },
    ApprovalByLimitMatrix: { amount_expr: "{{ form.total_amount }}" },
    IF: { branches: [{ label: "Evet", handle: "true", condition: {} }, { label: "Hayır", handle: "false", condition: {} }] },
    Calculate: { calculations: [] },
    SetFields: { mappings: [] },
    HTTPRequest: { url: "", method: "POST", mock: true },
    End: { status: "completed", exports: [] },
  };
  return NODE_REGISTRY_MAP[engineType] || {};
}
