export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API error: ${response.status}`);
  }
  return (await response.json()) as T;
}

export type FlowItem = {
  id: string;
  code: string;
  name: string;
  latest_version: number;
  latest_status: string;
};

export type InstanceItem = {
  id: string;
  title: string;
  status: string;
  current_node_id: string | null;
  started_at: string;
};

export type InboxPayload = {
  tasks: Array<{
    id: string;
    instance_id: string;
    title: string;
    status: string;
    assignee_role: string | null;
  }>;
  approvals: Array<{
    id: string;
    instance_id: string;
    status: string;
    assignee_role: string | null;
  }>;
};
