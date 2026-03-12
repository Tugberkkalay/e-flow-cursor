"use client";

import { create } from "zustand";

type AuthUser = {
  id: string;
  full_name: string;
  role: string;
  email: string;
  org_id: string;
};

type AppState = {
  token: string | null;
  me: AuthUser | null;
  selectedNodeId: string | null;
  setToken: (token: string | null) => void;
  setMe: (me: AuthUser | null) => void;
  setSelectedNodeId: (id: string | null) => void;
};

export const useAppStore = create<AppState>((set) => ({
  token: null,
  me: null,
  selectedNodeId: null,
  setToken: (token) => set({ token }),
  setMe: (me) => set({ me }),
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
}));
