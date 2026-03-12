const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("eflow_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, body?: unknown) => request<T>(endpoint, { method: "POST", body }),
  put: <T>(endpoint: string, body?: unknown) => request<T>(endpoint, { method: "PUT", body }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),
};

export const auth = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; user: any }>("/auth/login", { email, password }),
  me: () => api.get<any>("/auth/me"),
};

export const flows = {
  list: () => api.get<any[]>("/flows"),
  get: (id: string) => api.get<any>(`/flows/${id}`),
  create: (data: any) => api.post<any>("/flows", data),
  update: (id: string, data: any) => api.put<any>(`/flows/${id}`, data),
  publish: (id: string) => api.post<any>(`/flows/${id}/publish`),
  versions: (id: string) => api.get<any[]>(`/flows/${id}/versions`),
};

export const forms = {
  list: () => api.get<any[]>("/forms"),
  get: (id: string) => api.get<any>(`/forms/${id}`),
  create: (data: any) => api.post<any>("/forms", data),
  update: (id: string, data: any) => api.put<any>(`/forms/${id}`, data),
  publish: (id: string) => api.post<any>(`/forms/${id}/publish`),
};

export const instances = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return api.get<any[]>(`/instances${qs}`);
  },
  get: (id: string) => api.get<any>(`/instances/${id}`),
  start: (data: any) => api.post<any>("/instances/start", data),
  action: (id: string, action: any) => api.post<any>(`/instances/${id}/actions`, action),
  timeline: (id: string) => api.get<any[]>(`/instances/${id}/timeline`),
};

export const inbox = {
  list: () => api.get<any[]>("/inbox"),
  completeTask: (id: string, data: any) => api.post<any>(`/tasks/${id}/complete`, data),
  decide: (id: string, data: any) => api.post<any>(`/approvals/${id}/decide`, data),
};

export const users = {
  list: () => api.get<any[]>("/users"),
  create: (data: any) => api.post<any>("/users", data),
  update: (id: string, data: any) => api.put<any>(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
};

export const admin = {
  delegations: () => api.get<any[]>("/delegations"),
  createDelegation: (data: any) => api.post<any>("/delegations", data),
  approvalLimits: () => api.get<any[]>("/approval-limits"),
  createApprovalLimit: (data: any) => api.post<any>("/approval-limits", data),
};

export const expressions = {
  preview: (expr: string, context: Record<string, any>) =>
    api.post<{ result: any }>("/expressions/preview", { expression: expr, context }),
  schema: () => api.get<any>("/context/schema"),
};
