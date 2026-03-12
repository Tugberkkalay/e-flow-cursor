import { create } from "zustand";
import { FlowNode, FlowEdge, User, ProcessInstance, FormDefinition, FlowDefinition } from "@/types";

interface AppState {
  user: User | null;
  setUser: (user: User | null) => void;

  // Flow Designer State
  nodes: FlowNode[];
  edges: FlowEdge[];
  selectedNodeId: string | null;
  setNodes: (nodes: FlowNode[]) => void;
  setEdges: (edges: FlowEdge[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  addNode: (node: FlowNode) => void;
  updateNode: (id: string, data: Partial<FlowNode>) => void;
  removeNode: (id: string) => void;
  addEdge: (edge: FlowEdge) => void;
  removeEdge: (id: string) => void;

  // Current flow
  currentFlow: FlowDefinition | null;
  setCurrentFlow: (flow: FlowDefinition | null) => void;

  // Flows list
  flows: FlowDefinition[];
  setFlows: (flows: FlowDefinition[]) => void;

  // Forms
  forms: FormDefinition[];
  setForms: (forms: FormDefinition[]) => void;
  currentForm: FormDefinition | null;
  setCurrentForm: (form: FormDefinition | null) => void;

  // Instances
  instances: ProcessInstance[];
  setInstances: (instances: ProcessInstance[]) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),

  nodes: [],
  edges: [],
  selectedNodeId: null,
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  addNode: (node) => set((s) => ({ nodes: [...s.nodes, node] })),
  updateNode: (id, data) =>
    set((s) => ({
      nodes: s.nodes.map((n) => (n.id === id ? { ...n, ...data } : n)),
    })),
  removeNode: (id) =>
    set((s) => ({
      nodes: s.nodes.filter((n) => n.id !== id),
      edges: s.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: s.selectedNodeId === id ? null : s.selectedNodeId,
    })),
  addEdge: (edge) => set((s) => ({ edges: [...s.edges, edge] })),
  removeEdge: (id) => set((s) => ({ edges: s.edges.filter((e) => e.id !== id) })),

  currentFlow: null,
  setCurrentFlow: (currentFlow) => set({ currentFlow }),

  flows: [],
  setFlows: (flows) => set({ flows }),

  forms: [],
  setForms: (forms) => set({ forms }),
  currentForm: null,
  setCurrentForm: (currentForm) => set({ currentForm }),

  instances: [],
  setInstances: (instances) => set({ instances }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
