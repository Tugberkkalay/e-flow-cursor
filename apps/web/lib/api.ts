import "server-only";

import { cache } from "react";

import type {
  FlowDefinition,
  FormDefinition,
  InboxPayload,
  Instance,
  User,
} from "@/lib/types";

const API_URL =
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "admin@eflow.local";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "admin123";

type FetchInit = RequestInit & {
  token?: string;
};

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  return response.json() as Promise<T>;
}

export const getDemoToken = cache(async () => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  const data = await parseJson<{ access_token: string }>(response);
  return data.access_token;
});

export const apiFetch = cache(
  async <T>(path: string, init?: FetchInit): Promise<T> => {
    const token = init?.token ?? (await getDemoToken());
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(init?.headers ?? {}),
      },
    });
    return parseJson<T>(response);
  },
);

export async function getMe() {
  return apiFetch<User>("/me");
}

export async function getFlows() {
  return apiFetch<FlowDefinition[]>("/flows");
}

export async function getForms() {
  return apiFetch<FormDefinition[]>("/forms");
}

export async function getInstances() {
  return apiFetch<Instance[]>("/instances");
}

export async function getInstance(id: string) {
  return apiFetch<Instance>(`/instances/${id}`);
}

export async function getInbox() {
  return apiFetch<InboxPayload>("/inbox");
}

export async function getUsers() {
  return apiFetch<User[]>("/admin/users");
}

export async function getDelegations() {
  return apiFetch<
    Array<{
      id: string;
      delegator_id: string;
      delegate_id: string;
      role_scope: string[];
      start_date: string;
      end_date: string;
      is_active: boolean;
    }>
  >("/admin/delegations");
}

export async function getApprovalLimits() {
  return apiFetch<
    Array<{
      id: string;
      department: string;
      budget_type: string;
      currency: string;
      min_amount: number;
      max_amount: number;
      approver_role: string;
      approver_user_id?: string | null;
    }>
  >("/admin/approval-limits");
}

export async function getAudit() {
  return apiFetch<
    Array<{
      id: string;
      event_type: string;
      entity_type: string;
      entity_id: string;
      actor_user_id?: string | null;
      process_instance_id?: string | null;
      payload_json: Record<string, unknown>;
      created_at: string;
    }>
  >("/audit");
}

export async function getContextSchema() {
  return apiFetch<Record<string, unknown>>("/context/schema");
}

export async function previewExpression(expr: string) {
  return apiFetch<{ result: unknown }>("/expressions/preview", {
    method: "POST",
    body: JSON.stringify({ expr, context_sample: {} }),
  });
}

export function getApiBaseUrl() {
  return API_URL;
}
