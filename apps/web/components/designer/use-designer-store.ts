"use client";

import { create } from "zustand";
import type { Edge, Node } from "@xyflow/react";

type DesignerState = {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  search: string;
  neighborFocus: boolean;
  setGraph: (nodes: Node[], edges: Edge[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSearch: (value: string) => void;
  toggleNeighborFocus: () => void;
  updateNodeData: (id: string, data: Record<string, unknown>) => void;
};

export const useDesignerStore = create<DesignerState>((set) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  search: "",
  neighborFocus: true,
  setGraph: (nodes, edges) => set({ nodes, edges }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  setSearch: (search) => set({ search }),
  toggleNeighborFocus: () =>
    set((state) => ({ neighborFocus: !state.neighborFocus })),
  updateNodeData: (id, data) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id
          ? {
              ...node,
              data: {
                ...(node.data as Record<string, unknown>),
                ...data,
              },
            }
          : node,
      ),
    })),
}));
