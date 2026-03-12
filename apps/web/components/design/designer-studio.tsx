"use client";

import { useCallback, useMemo, useState } from "react";
import dagre from "dagre";
import {
  Background,
  Connection,
  ConnectionMode,
  Controls,
  Edge,
  Handle,
  MiniMap,
  Node,
  NodeProps,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Plus, Save, Search, Sparkles, Wand2 } from "lucide-react";

import { SmartCurvedRoutedEdge } from "@/components/design/smart-routed-edge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { NODE_CATEGORIES, NODE_REGISTRY, NodeRegistryItem } from "@/lib/node-registry";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

type DesignerNodeData = {
  label: string;
  engineType: string;
  pastelColor: string;
  config: Record<string, unknown>;
};

function EnterpriseNode({ data, selected }: NodeProps<Node<DesignerNodeData>>) {
  const isBranching = ["if", "switch", "approval", "multiApproval"].includes(
    String(data.engineType),
  );

  return (
    <div
      className={cn(
        "min-w-[180px] rounded-2xl border bg-white px-3 py-2 shadow-[0_6px_20px_rgba(16,24,40,0.05)] transition-all duration-200",
        selected
          ? "border-[#9AB3D6] shadow-[0_10px_30px_rgba(24,48,86,0.15)]"
          : "border-[#DEE6F1] hover:border-[#CBD8E7] hover:shadow-[0_10px_28px_rgba(16,24,40,0.1)]",
      )}
      style={{ backgroundColor: data.pastelColor }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2.5 !w-2.5 !border !border-[#B8C7DA] !bg-white"
      />
      <div className="text-xs text-[#4F6178]">{data.engineType}</div>
      <div className="text-sm font-semibold text-[#203046]">{data.label}</div>
      <Handle
        type="source"
        id="main"
        position={Position.Right}
        className="!h-2.5 !w-2.5 !border !border-[#8CA2C0] !bg-[#1E2A38]"
      />
      {isBranching ? (
        <>
          <Handle
            type="source"
            id="yes"
            position={Position.Bottom}
            className="!h-2.5 !w-2.5 !border !border-[#8CA2C0] !bg-[#1E2A38]"
          />
          <Handle
            type="source"
            id="no"
            position={Position.Top}
            className="!h-2.5 !w-2.5 !border !border-[#8CA2C0] !bg-[#1E2A38]"
          />
        </>
      ) : null}
    </div>
  );
}

const nodeTypes = { enterpriseNode: EnterpriseNode };
const edgeTypes = { smart: SmartCurvedRoutedEdge };

const INITIAL_NODES: Node<DesignerNodeData>[] = [
  {
    id: "start",
    type: "enterpriseNode",
    position: { x: 40, y: 200 },
    data: {
      label: "Manual Start",
      engineType: "start",
      pastelColor: "#DCE8FF",
      config: {},
    },
  },
  {
    id: "fill",
    type: "enterpriseNode",
    position: { x: 320, y: 200 },
    data: {
      label: "Form Fill (PR)",
      engineType: "formFill",
      pastelColor: "#EAF5E9",
      config: {},
    },
  },
  {
    id: "approval",
    type: "enterpriseNode",
    position: { x: 620, y: 200 },
    data: {
      label: "Approval by Matrix",
      engineType: "approval",
      pastelColor: "#FFF4D9",
      config: { byLimitMatrix: true },
    },
  },
  {
    id: "end",
    type: "enterpriseNode",
    position: { x: 900, y: 200 },
    data: {
      label: "End",
      engineType: "end",
      pastelColor: "#EEF2F8",
      config: {
        exportMapping: {
          po_no: "{{ gen.po_no }}",
        },
      },
    },
  },
];

const INITIAL_EDGES: Edge[] = [
  {
    id: "e1",
    source: "start",
    target: "fill",
    type: "smart",
    markerEnd: "url(#arrow)",
  },
  {
    id: "e2",
    source: "fill",
    target: "approval",
    type: "smart",
    markerEnd: "url(#arrow)",
  },
  {
    id: "e3",
    source: "approval",
    target: "end",
    type: "smart",
    markerEnd: "url(#arrow)",
    data: { label: "Onaylandı" },
  },
];

function arrangeGraph(nodes: Node<DesignerNodeData>[], edges: Edge[]) {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "LR", nodesep: 80, ranksep: 130, marginx: 40, marginy: 40 });

  nodes.forEach((node) => {
    graph.setNode(node.id, { width: 220, height: 80 });
  });
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target));
  dagre.layout(graph);

  return nodes.map((node) => {
    const position = graph.node(node.id);
    return {
      ...node,
      position: { x: position.x - 110, y: position.y - 40 },
    };
  });
}

function DesignerStudioInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>(NODE_CATEGORIES[0]);
  const [flowName, setFlowName] = useState("Satın Alma Süreci");
  const [version, setVersion] = useState(3);
  const selectedNodeId = useAppStore((s) => s.selectedNodeId);
  const setSelectedNodeId = useAppStore((s) => s.setSelectedNodeId);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId),
    [nodes, selectedNodeId],
  );

  const visiblePaletteItems = useMemo(
    () =>
      NODE_REGISTRY.filter(
        (item) =>
          item.category === activeCategory &&
          (item.label.toLowerCase().includes(search.toLowerCase()) ||
            item.tags.some((tag) => tag.toLowerCase().includes(search.toLowerCase()))),
      ),
    [activeCategory, search],
  );

  const addNode = useCallback(
    (item: NodeRegistryItem) => {
      const id = `${item.key}_${Math.round(Math.random() * 99999)}`;
      const node: Node<DesignerNodeData> = {
        id,
        type: "enterpriseNode",
        position: {
          x: 180 + (nodes.length % 4) * 220,
          y: 80 + Math.floor(nodes.length / 4) * 120,
        },
        data: {
          label: item.label,
          engineType: item.engineType,
          pastelColor: item.pastelColor,
          config: item.defaultConfig,
        },
      };
      setNodes((current) => [...current, node]);
      setSelectedNodeId(id);
    },
    [nodes.length, setNodes, setSelectedNodeId],
  );

  const autoArrange = () => {
    setNodes((current) => arrangeGraph(current, edges));
  };

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: "smart",
            animated: false,
            markerEnd: "url(#arrow)",
          },
          eds,
        ),
      ),
    [setEdges],
  );

  const saveNodeConfig = (nextConfig: string) => {
    if (!selectedNodeId) return;
    try {
      const parsed = JSON.parse(nextConfig);
      setNodes((curr) =>
        curr.map((n) =>
          n.id === selectedNodeId
            ? { ...n, data: { ...n.data, config: parsed } }
            : n,
        ),
      );
    } catch {
      // best effort MVP editor
    }
  };

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Input
              value={flowName}
              onChange={(e) => setFlowName(e.target.value)}
              className="w-[260px]"
              aria-label="Flow name"
            />
            <Badge>Draft</Badge>
            <Badge variant="default">v{version}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary">Form bağla</Button>
            <Button variant="secondary" onClick={autoArrange}>
              <Sparkles className="mr-2 h-4 w-4" />
              Auto Arrange
            </Button>
            <Button variant="secondary" onClick={() => setVersion((v) => v + 1)}>
              <Save className="mr-2 h-4 w-4" />
              Kaydet
            </Button>
            <Button>Yayınla</Button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-12 gap-4">
        <Card className="col-span-3 h-[76vh] p-3">
          <Tabs value={activeCategory} onValueChange={setActiveCategory}>
            <TabsList className="mb-3 w-full justify-start overflow-x-auto">
              {NODE_CATEGORIES.map((category) => (
                <TabsTrigger key={category} value={category} className="whitespace-nowrap">
                  {category}
                </TabsTrigger>
              ))}
            </TabsList>
            {NODE_CATEGORIES.map((category) => (
              <TabsContent key={category} value={category} className="mt-0">
                <div className="relative mb-3">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-[#7A8797]" />
                  <Input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Node ara..."
                    className="pl-9"
                  />
                </div>
                <div className="h-[64vh] space-y-2 overflow-auto pr-1">
                  {visiblePaletteItems.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.key}
                        type="button"
                        className="flex w-full items-center justify-between rounded-xl border border-[#E7EBF0] bg-white px-3 py-2 text-left transition-all hover:border-[#C9D6E7] hover:shadow-sm"
                        onClick={() => addNode(item)}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="flex h-8 w-8 items-center justify-center rounded-lg"
                            style={{ backgroundColor: item.pastelColor }}
                          >
                            <Icon className="h-4 w-4 text-[#223248]" />
                          </span>
                          <div>
                            <p className="text-sm font-medium">{item.label}</p>
                            <p className="text-xs text-[#6A788A]">{item.engineType}</p>
                          </div>
                        </div>
                        <Plus className="h-4 w-4 text-[#6A788A]" />
                      </button>
                    );
                  })}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </Card>

        <Card className="col-span-6 h-[76vh] overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges.map((edge) => ({
              ...edge,
              type: "smart",
              data: { ...edge.data, label: edge.data?.label ?? edge.label },
            }))}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            defaultEdgeOptions={{ type: "smart" }}
            connectionMode={ConnectionMode.Loose}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          >
            <svg>
              <defs>
                <marker
                  id="arrow"
                  markerWidth="11"
                  markerHeight="11"
                  refX="9"
                  refY="5.5"
                  orient="auto"
                  markerUnits="strokeWidth"
                >
                  <path d="M0,0 L0,11 L10,5.5 z" fill="#6F86A6" />
                </marker>
              </defs>
            </svg>
            <Background gap={24} size={1} color="#E7EDF5" />
            <MiniMap
              pannable
              zoomable
              className="!bg-white !border !border-[#E8EDF3] !rounded-xl !shadow-sm"
              nodeColor={(node) =>
                ((node.data as DesignerNodeData | undefined)?.pastelColor as string) ||
                "#DDE6F2"
              }
            />
            <Controls
              showInteractive={false}
              className="!rounded-xl !border !border-[#E8EDF3] !bg-white !shadow-sm"
            />
            <Panel
              position="top-left"
              className="rounded-xl border border-[#E7EBF0] bg-white/90 px-3 py-2 text-xs text-[#5A6678] shadow-sm backdrop-blur-[2px]"
            >
              Knowledge-graph canvas · smart routed edges
            </Panel>
          </ReactFlow>
        </Card>

        <Card className="col-span-3 h-[76vh] p-3">
          <h3 className="mb-1 text-sm font-semibold">Properties Panel</h3>
          <p className="mb-3 text-xs text-[#6A788A]">
            Node ayarları · rules builder · mapping
          </p>
          {selectedNode ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs text-[#6A788A]">Node</p>
                <p className="text-sm font-medium">{selectedNode.data.label}</p>
              </div>
              <div>
                <p className="mb-1 text-xs text-[#6A788A]">Engine Type</p>
                <Input value={selectedNode.data.engineType} readOnly />
              </div>
              <div>
                <p className="mb-1 text-xs text-[#6A788A]">Config (JSON)</p>
                <Textarea
                  defaultValue={JSON.stringify(selectedNode.data.config, null, 2)}
                  onBlur={(e) => saveNodeConfig(e.target.value)}
                  className="h-44 font-mono text-xs"
                />
              </div>
              {selectedNode.data.engineType === "subprocessCall" ? (
                <div className="space-y-2 rounded-xl border border-[#E8EDF3] bg-[#F8FAFD] p-3">
                  <p className="text-xs font-medium">Subprocess I/O Mapping (MVP)</p>
                  <Input placeholder="inputMapping.form_total -> form.total_amount" />
                  <Input placeholder="outputMapping.exports.po_no -> gen.po_no" />
                </div>
              ) : null}
              <div className="space-y-2 rounded-xl border border-[#E8EDF3] bg-[#F8FAFD] p-3">
                <p className="text-xs font-medium">Condition Test</p>
                <Input placeholder="{{ form.total_amount > 50000 }}" />
                <Button variant="secondary" size="sm">
                  <Wand2 className="mr-1 h-4 w-4" />
                  Test
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-[#D8E0EA] bg-[#FBFCFE] p-4 text-xs text-[#728097]">
              Düzenlemek için canvas üzerinden bir node seçin.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export function DesignerStudio() {
  return (
    <ReactFlowProvider>
      <DesignerStudioInner />
    </ReactFlowProvider>
  );
}
