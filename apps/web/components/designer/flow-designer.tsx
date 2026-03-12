"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import dagre from "dagre";
import * as Icons from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  addEdge,
  Background,
  ConnectionMode,
  type Connection,
  Controls,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  ReactFlow,
  ReactFlowProvider,
  applyEdgeChanges,
  applyNodeChanges,
  MarkerType,
  MiniMap,
  useReactFlow,
} from "@xyflow/react";

import type { FlowDefinition, FormDefinition } from "@/lib/types";
import { cn } from "@/lib/utils";
import { nodeRegistry, paletteTabs } from "@/components/designer/node-registry";
import { SmartCurvedRoutedEdge } from "@/components/designer/smart-edge";
import { useDesignerStore } from "@/components/designer/use-designer-store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import "@xyflow/react/dist/style.css";

type DesignerProps = {
  initialFlows: FlowDefinition[];
  forms: FormDefinition[];
  token: string;
  apiBaseUrl: string;
};

type WorkflowNodeData = {
  label: string;
  primitive: string;
  preset: string;
  category: string;
  version: number;
  config: Record<string, unknown>;
  color: string;
  outputs: string[];
};

const nodeWidth = 240;
const nodeHeight = 108;

function WorkflowNode({ data, selected }: { data: WorkflowNodeData; selected?: boolean }) {
  return (
    <div
      className={cn(
        "min-w-[240px] rounded-[24px] border bg-white p-4 shadow-[0_14px_40px_-24px_rgba(15,23,42,0.28)] transition-all duration-200",
        selected
          ? "border-slate-900 shadow-[0_22px_55px_-26px_rgba(15,23,42,0.4)]"
          : "border-slate-200 hover:border-slate-300",
      )}
      style={{
        boxShadow: selected
          ? "0 24px 56px -26px rgba(15,23,42,0.42)"
          : "0 14px 40px -24px rgba(15,23,42,0.28)",
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-2xl"
          style={{ backgroundColor: data.color }}
        >
          <div className="h-2.5 w-2.5 rounded-full bg-slate-900" />
        </div>
        <Badge tone="muted">{data.primitive}</Badge>
      </div>
      <div className="mt-4">
        <div className="text-[15px] font-semibold text-slate-950">{data.label}</div>
        <div className="mt-1 text-sm text-slate-500">{data.preset}</div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {data.outputs.slice(0, 2).map((output) => (
          <span
            key={output}
            className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500"
          >
            {output}
          </span>
        ))}
      </div>
    </div>
  );
}

const nodeTypes = {
  workflowNode: WorkflowNode,
};

const edgeTypes = {
  smart: SmartCurvedRoutedEdge,
};

function buildElements(flow?: FlowDefinition | null) {
  const graph = flow?.graph_json ?? { nodes: [], edges: [] };
  const rfNodes: Node<WorkflowNodeData>[] = graph.nodes.map((node, index) => {
    const registry = nodeRegistry.find((item) => item.key === node.preset);
    return {
      id: node.id,
      type: "workflowNode",
      position:
        (node as unknown as { position?: { x: number; y: number } }).position ??
        { x: (index % 3) * 280, y: Math.floor(index / 3) * 160 },
      data: {
        label: node.label,
        primitive: node.primitive,
        preset: node.preset,
        category: node.category,
        version: node.version ?? 1,
        config: node.config ?? {},
        color: registry?.color ?? "#E2E8F0",
        outputs: registry?.outputs ?? [],
      },
    };
  });

  const edgeGroups = graph.edges.reduce<Record<string, number>>((acc, edge) => {
    const key = `${edge.source}-${edge.target}`;
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  const seen: Record<string, number> = {};

  const rfEdges: Edge[] = graph.edges.map((edge) => {
    const groupKey = `${edge.source}-${edge.target}`;
    const index = seen[groupKey] ?? 0;
    seen[groupKey] = index + 1;

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "smart",
      label: edge.label,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
      data: {
        label: edge.label,
        condition: edge.condition,
        parallelIndex: index - (edgeGroups[groupKey] - 1) / 2,
      },
      style: { stroke: "#94a3b8" },
    };
  });

  return layoutElements(rfNodes, rfEdges);
}

function layoutElements(nodes: Node<WorkflowNodeData>[], edges: Edge[]) {
  const graph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "LR", ranksep: 120, nodesep: 40, marginx: 24, marginy: 24 });

  nodes.forEach((node) => graph.setNode(node.id, { width: nodeWidth, height: nodeHeight }));
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target));
  dagre.layout(graph);

  return {
    nodes: nodes.map((node) => {
      const position = graph.node(node.id);
      return {
        ...node,
        position: {
          x: position.x - nodeWidth / 2,
          y: position.y - nodeHeight / 2,
        },
      };
    }),
    edges,
  };
}

function iconFor(name: string) {
  return (Icons as unknown as Record<string, LucideIcon>)[name] ?? Icons.Circle;
}

function Studio({
  initialFlows,
  forms,
  token,
  apiBaseUrl,
}: DesignerProps) {
  const flowViewport = useRef<HTMLDivElement | null>(null);
  const initialActiveFlow =
    initialFlows.find((flow) => !flow.is_template) ?? initialFlows[0] ?? null;
  const initialElements = buildElements(initialActiveFlow);
  const [flows, setFlows] = useState(initialFlows);
  const [activeFlowId, setActiveFlowId] = useState(
    initialActiveFlow?.id ?? "",
  );
  const [nodes, setNodes] = useState<Node<WorkflowNodeData>[]>(initialElements.nodes);
  const [edges, setEdges] = useState<Edge[]>(initialElements.edges);
  const [activeTab, setActiveTab] = useState("Flow Designer");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [expressionPreview, setExpressionPreview] = useState<string>("");
  const [attachedFormId, setAttachedFormId] = useState(forms[0]?.id ?? "");
  const idCounter = useRef(initialFlows.length + 1);

  const {
    selectedNodeId,
    setSelectedNodeId,
    search,
    setSearch,
    neighborFocus,
    toggleNeighborFocus,
  } = useDesignerStore();
  const reactFlow = useReactFlow();

  const templates = useMemo(
    () => flows.filter((flow) => flow.is_template),
    [flows],
  );

  const activeFlow = useMemo(
    () => flows.find((flow) => flow.id === activeFlowId) ?? null,
    [activeFlowId, flows],
  );

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  );

  const adjacency = useMemo(() => {
    if (!selectedNodeId) return new Set<string>();
    const set = new Set<string>([selectedNodeId]);
    edges.forEach((edge) => {
      if (edge.source === selectedNodeId) set.add(edge.target);
      if (edge.target === selectedNodeId) set.add(edge.source);
    });
    return set;
  }, [edges, selectedNodeId]);

  const palette = useMemo(() => {
    return nodeRegistry.filter((node) => {
      const matchSearch =
        !search ||
        `${node.label} ${node.category} ${node.tags.join(" ")}`
          .toLowerCase()
          .includes(search.toLowerCase());
      const matchTab = activeTab === "Flow Designer";
      return matchSearch && matchTab;
    });
  }, [search, activeTab]);

  const loadFlow = useCallback(
    (flowId: string, sourceFlows?: FlowDefinition[]) => {
      const nextFlows = sourceFlows ?? flows;
      const flow = nextFlows.find((item) => item.id === flowId) ?? null;
      const nextElements = buildElements(flow);
      setActiveFlowId(flowId);
      setNodes(nextElements.nodes);
      setEdges(nextElements.edges);
      setSelectedNodeId(nextElements.nodes[0]?.id ?? null);
      setStatusMessage("");
    },
    [flows, setSelectedNodeId],
  );

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((current) => applyNodeChanges(changes, current) as Node<WorkflowNodeData>[]);
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((current) => applyEdgeChanges(changes, current) as Edge[]);
  }, []);

  const onConnect = useCallback(
    (connection: Connection) => {
      const edgeId = `${connection.source}-${connection.target}-${idCounter.current++}`;
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id: edgeId,
            type: "smart",
            label: "Next",
            markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
            data: { label: "Next", parallelIndex: 0 },
          },
          current,
        ),
      );
    },
    [],
  );

  const addPaletteNode = (key: string) => {
    const registry = nodeRegistry.find((item) => item.key === key);
    if (!registry) return;
    const position = reactFlow.screenToFlowPosition({
      x: (flowViewport.current?.clientWidth ?? 960) / 2,
      y: (flowViewport.current?.clientHeight ?? 640) / 2,
    });
    const newNode: Node<WorkflowNodeData> = {
      id: `${registry.key}-${idCounter.current++}`,
      type: "workflowNode",
      position,
      data: {
        label: registry.label,
        primitive: registry.primitive,
        preset: registry.key,
        category: registry.category,
        version: 1,
        config: registry.defaultConfig,
        color: registry.color,
        outputs: registry.outputs,
      },
    };
    setNodes((current) => [...current, newNode]);
    setSelectedNodeId(newNode.id);
  };

  const updateSelectedNode = (patch: Partial<WorkflowNodeData>) => {
    if (!selectedNode) return;
    setNodes((current) =>
      current.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                ...patch,
                config: {
                  ...(node.data.config ?? {}),
                  ...(patch.config ?? {}),
                },
              },
            }
          : node,
      ),
    );
  };

  const serializeGraph = () => ({
    nodes: nodes.map((node) => ({
      id: node.id,
      label: node.data.label,
      primitive: node.data.primitive,
      preset: node.data.preset,
      category: node.data.category,
      version: node.data.version,
      config: node.data.config,
      position: node.position,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: String(edge.label ?? edge.data?.label ?? "Next"),
      condition: (edge.data?.condition as string | undefined) ?? null,
    })),
  });

  const saveFlow = async () => {
    if (!activeFlow) return;
    const response = await fetch(`${apiBaseUrl}/flows/${activeFlow.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        name: activeFlow.name,
        description: activeFlow.description,
        graph_json: serializeGraph(),
      }),
    });
    const updated = (await response.json()) as FlowDefinition;
    setFlows((current) =>
      current.map((flow) => (flow.id === updated.id ? updated : flow)),
    );
    setStatusMessage("Draft saved.");
  };

  const publishFlow = async () => {
    if (!activeFlow) return;
    await saveFlow();
    const response = await fetch(`${apiBaseUrl}/flows/${activeFlow.id}/publish`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const updated = (await response.json()) as FlowDefinition;
    setFlows((current) =>
      current.map((flow) => (flow.id === updated.id ? updated : flow)),
    );
    setStatusMessage(`Published v${updated.latest_version}.`);
  };

  const createFromTemplate = async (templateKey: string, name: string) => {
    const response = await fetch(`${apiBaseUrl}/flows`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        name,
        key: `${templateKey}-${idCounter.current++}`,
        template_key: templateKey,
      }),
    });
    const created = (await response.json()) as FlowDefinition;
    const nextFlows = [created, ...flows];
    setFlows(nextFlows);
    loadFlow(created.id, nextFlows);
    setStatusMessage(`Template cloned: ${created.name}`);
  };

  const autoArrange = () => {
    const layouted = layoutElements(nodes, edges);
    setNodes(layouted.nodes);
    reactFlow.fitView({ padding: 0.18, duration: 200 });
  };

  const testExpression = async () => {
    if (!selectedNode) return;
    const expression =
      String(selectedNode.data.config.testExpression ?? "") ||
      String(selectedNode.data.config.action ?? "");
    if (!expression) {
      setExpressionPreview("No expression configured.");
      return;
    }
    const response = await fetch(`${apiBaseUrl}/expressions/preview`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ expr: expression, context_sample: {} }),
    });
    const payload = (await response.json()) as { result: unknown };
    setExpressionPreview(JSON.stringify(payload.result));
  };

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden">
        <CardHeader className="border-b border-slate-100">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <CardTitle>Design Studio</CardTitle>
              <CardDescription>
                Knowledge-graph hissi veren canvas, smart routed edge’ler,
                versioned flow publishing ve form binding.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <select
                className="h-10 rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-600 outline-none"
                value={activeFlowId}
                onChange={(event) => loadFlow(event.target.value)}
              >
                {flows.map((flow) => (
                  <option key={flow.id} value={flow.id}>
                    {flow.name} {flow.is_template ? "(template)" : ""}
                  </option>
                ))}
              </select>
              <select
                className="h-10 rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-600 outline-none"
                value={attachedFormId}
                onChange={(event) => setAttachedFormId(event.target.value)}
              >
                {forms.map((form) => (
                  <option key={form.id} value={form.id}>
                    {form.name} v{form.version}
                  </option>
                ))}
              </select>
              <Button variant="secondary" onClick={autoArrange}>
                Auto Arrange
              </Button>
              <Button variant="secondary" onClick={saveFlow}>
                Kaydet
              </Button>
              <Button onClick={publishFlow}>Yayinla</Button>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Badge tone="muted">Status: {activeFlow?.status ?? "draft"}</Badge>
            <Badge tone="default">
              Version: {activeFlow?.latest_version ?? 1}
            </Badge>
            <Badge tone="success">
              Form bagli: {forms.find((item) => item.id === attachedFormId)?.name}
            </Badge>
            {statusMessage ? <Badge tone="warning">{statusMessage}</Badge> : null}
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-4">
          <div className="grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)_330px]">
            <Card className="rounded-[28px] border-dashed shadow-none">
              <CardHeader className="pb-4">
                <CardTitle className="text-base">Node Palette</CardTitle>
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Node ara, tag yaz..."
                />
              </CardHeader>
              <CardContent className="space-y-3">
                {paletteTabs.map((tab) => (
                  <div key={tab} className="space-y-2">
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                      {tab}
                    </div>
                    <div className="space-y-2">
                      {palette
                        .filter((item) => item.category === tab)
                        .map((item) => {
                          const Icon = iconFor(item.icon);
                          return (
                            <button
                              key={item.key}
                              onClick={() => addPaletteNode(item.key)}
                              className="flex w-full items-center gap-3 rounded-2xl border border-slate-200 px-3 py-3 text-left transition-all duration-200 hover:border-slate-300 hover:bg-slate-50"
                            >
                              <div
                                className="flex h-10 w-10 items-center justify-center rounded-2xl"
                                style={{ backgroundColor: item.color }}
                              >
                                <Icon className="h-4 w-4 text-slate-800" />
                              </div>
                              <div className="min-w-0">
                                <div className="truncate text-sm font-medium text-slate-900">
                                  {item.label}
                                </div>
                                <div className="truncate text-xs text-slate-500">
                                  {item.tags.join(" · ")}
                                </div>
                              </div>
                            </button>
                          );
                        })}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4">
                  <TabsList>
                    <TabsTrigger value="Flow Designer">Flow Designer</TabsTrigger>
                    <TabsTrigger value="Form Builder">Dynamic Form Builder</TabsTrigger>
                  </TabsList>
                  <Button variant="ghost" onClick={toggleNeighborFocus}>
                    {neighborFocus ? "1-hop highlight on" : "1-hop highlight off"}
                  </Button>
                </div>

                <TabsContent value="Flow Designer" className="m-0">
                  <div ref={flowViewport} className="h-[760px] bg-[#fbfcfd]">
                    <ReactFlow
                      nodes={nodes.map((node) => ({
                        ...node,
                        style:
                          neighborFocus && selectedNodeId && !adjacency.has(node.id)
                            ? { opacity: 0.26 }
                            : undefined,
                      }))}
                      edges={edges.map((edge) => ({
                        ...edge,
                        style:
                          neighborFocus && selectedNodeId && !adjacency.has(edge.source) && !adjacency.has(edge.target)
                            ? { opacity: 0.22 }
                            : edge.style,
                      }))}
                      nodeTypes={nodeTypes}
                      edgeTypes={edgeTypes}
                      onNodesChange={onNodesChange}
                      onEdgesChange={onEdgesChange}
                      onConnect={onConnect}
                      onNodeClick={(_, node) => setSelectedNodeId(node.id)}
                      onPaneClick={() => setSelectedNodeId(null)}
                      fitView
                      connectionMode={ConnectionMode.Loose}
                      defaultEdgeOptions={{
                        type: "smart",
                        markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
                      }}
                    >
                      <Background color="#e2e8f0" gap={24} size={1.2} />
                      <MiniMap
                        pannable
                        zoomable
                        style={{
                          backgroundColor: "rgba(255,255,255,0.96)",
                          border: "1px solid #e2e8f0",
                          borderRadius: 18,
                        }}
                        nodeColor={(node) => String((node.data as WorkflowNodeData).color)}
                      />
                      <Controls className="rounded-2xl border border-slate-200 bg-white shadow-[0_12px_30px_-20px_rgba(15,23,42,0.3)]" />
                    </ReactFlow>
                  </div>
                </TabsContent>

                <TabsContent value="Form Builder" className="m-0">
                  <div className="grid h-[760px] gap-4 p-4 xl:grid-cols-[320px_minmax(0,1fr)]">
                    <Card className="rounded-[28px] shadow-none">
                      <CardHeader>
                        <CardTitle className="text-base">Forms</CardTitle>
                        <CardDescription>
                          Stable snake_case keys, calculations, conditional
                          visibility ve line-items support.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {forms.map((form) => (
                          <button
                            key={form.id}
                            className={cn(
                              "w-full rounded-2xl border px-4 py-3 text-left transition-all",
                              attachedFormId === form.id
                                ? "border-slate-900 bg-slate-950 text-white"
                                : "border-slate-200 bg-white hover:border-slate-300",
                            )}
                            onClick={() => setAttachedFormId(form.id)}
                          >
                            <div className="text-sm font-semibold">{form.name}</div>
                            <div className="mt-1 text-xs opacity-70">
                              {form.key} · v{form.version}
                            </div>
                          </button>
                        ))}
                      </CardContent>
                    </Card>

                    <Card className="rounded-[28px] shadow-none">
                      <CardHeader>
                        <CardTitle className="text-base">
                          {forms.find((form) => form.id === attachedFormId)?.name}
                        </CardTitle>
                        <CardDescription>
                          Rules builder ve hesaplama alanlari MVP seviyesinde
                          ayni panelde gosteriliyor.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-4 lg:grid-cols-2">
                        {(forms.find((form) => form.id === attachedFormId)?.schema_json.fields ??
                          []).map((field, index) => (
                          <div
                            key={`${String(field.key)}-${index}`}
                            className="rounded-[22px] border border-slate-200 bg-slate-50 p-4"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div>
                                <div className="text-sm font-semibold text-slate-900">
                                  {String(field.label)}
                                </div>
                                <div className="mt-1 text-xs text-slate-500">
                                  {String(field.key)} · {String(field.type)}
                                </div>
                              </div>
                              <Badge
                                tone={
                                  field.required ? "warning" : field.calculation ? "success" : "muted"
                                }
                              >
                                {field.required
                                  ? "Required"
                                  : field.calculation
                                    ? "Calculated"
                                    : "Optional"}
                              </Badge>
                            </div>
                            {"calculation" in field && field.calculation ? (
                              <div className="mt-3 rounded-2xl bg-white px-3 py-2 text-xs text-slate-600">
                                {String(field.calculation)}
                              </div>
                            ) : null}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </div>

            <Card className="rounded-[28px] shadow-none">
              <CardHeader>
                <CardTitle className="text-base">Properties Panel</CardTitle>
                <CardDescription>
                  Node config, condition test, subprocess I/O mapping ve output
                  contract.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {selectedNode ? (
                  <>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                        Label
                      </label>
                      <Input
                        value={selectedNode.data.label}
                        onChange={(event) =>
                          updateSelectedNode({ label: event.target.value })
                        }
                      />
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                          Primitive
                        </label>
                        <Input value={selectedNode.data.primitive} readOnly />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                          Preset
                        </label>
                        <Input value={selectedNode.data.preset} readOnly />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                        Action / Test Expression
                      </label>
                      <Input
                        value={String(
                          selectedNode.data.config.testExpression ??
                            selectedNode.data.config.action ??
                            "",
                        )}
                        onChange={(event) =>
                          updateSelectedNode({
                            config: {
                              ...selectedNode.data.config,
                              testExpression: event.target.value,
                            },
                          })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                        Notes
                      </label>
                      <Textarea
                        value={JSON.stringify(selectedNode.data.config, null, 2)}
                        onChange={(event) => {
                          try {
                            updateSelectedNode({
                              config: JSON.parse(event.target.value) as Record<
                                string,
                                unknown
                              >,
                            });
                          } catch {
                            // Keep raw value untouched until valid JSON.
                          }
                        }}
                      />
                    </div>

                    {selectedNode.data.preset === "subprocess_call" ? (
                      <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                        <div className="text-sm font-semibold text-slate-900">
                          Input / Output Mapping
                        </div>
                        <div className="mt-3 grid gap-3">
                          {Object.entries(
                            (selectedNode.data.config.input_mapping ??
                              {}) as Record<string, string>,
                          ).map(([key, value]) => (
                            <div key={key} className="rounded-2xl bg-white p-3">
                              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                                INPUT {key}
                              </div>
                              <div className="mt-1 text-sm text-slate-600">{value}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <div className="space-y-3 rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-semibold text-slate-900">
                          Condition test
                        </div>
                        <Button size="sm" variant="secondary" onClick={testExpression}>
                          Test
                        </Button>
                      </div>
                      <div className="rounded-2xl bg-white px-3 py-3 text-sm text-slate-600">
                        {expressionPreview || "Preview sonucu burada gorunur."}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="rounded-[24px] border border-dashed border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-500">
                    Canvas uzerinde bir node secin. Sag panel node config, rule
                    expression, retry policy ve subprocess mapping detaylarini
                    gosterecek.
                  </div>
                )}

                <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4">
                  <div className="text-sm font-semibold text-slate-900">
                    Template gallery
                  </div>
                  <div className="mt-4 space-y-3">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        className="rounded-[22px] border border-slate-200 bg-white p-4"
                      >
                        <div className="text-sm font-semibold text-slate-900">
                          {template.name}
                        </div>
                        <div className="mt-1 text-sm leading-6 text-slate-500">
                          {template.description}
                        </div>
                        <Button
                          size="sm"
                          className="mt-3"
                          variant="secondary"
                          onClick={() =>
                            createFromTemplate(
                              template.template_key ?? template.key,
                              `${template.name} Clone`,
                            )
                          }
                        >
                          Create from template
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function FlowDesigner(props: DesignerProps) {
  return (
    <ReactFlowProvider>
      <Studio {...props} />
    </ReactFlowProvider>
  );
}
