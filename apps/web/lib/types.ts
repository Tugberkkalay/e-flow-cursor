export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department?: string | null;
  cost_center?: string | null;
};

export type FlowNode = {
  id: string;
  label: string;
  primitive: string;
  preset: string;
  category: string;
  version?: number;
  config: Record<string, unknown>;
};

export type FlowEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  condition?: string | null;
};

export type FlowDefinition = {
  id: string;
  key: string;
  name: string;
  description?: string | null;
  status: string;
  latest_version: number;
  version_id?: string | null;
  version_status?: string | null;
  is_template: boolean;
  template_key?: string | null;
  graph_json?: {
    nodes: FlowNode[];
    edges: FlowEdge[];
  } | null;
};

export type FormDefinition = {
  id: string;
  key: string;
  name: string;
  status: string;
  version: number;
  schema_json: {
    title?: string;
    fields: Array<Record<string, unknown>>;
    rules_builder?: Record<string, unknown>;
  };
};

export type Task = {
  id: string;
  title: string;
  status: string;
  node_id: string;
  assignee_user_id?: string | null;
  assignee_role?: string | null;
  created_at: string;
  completed_at?: string | null;
  outcome?: string | null;
  comments?: string | null;
};

export type Approval = {
  id: string;
  status: string;
  node_id: string;
  approver_user_id?: string | null;
  approver_role?: string | null;
  created_at: string;
  decided_at?: string | null;
  decision?: string | null;
  comments?: string | null;
};

export type DocumentRecord = {
  id: string;
  document_type: string;
  version: number;
  file_name: string;
  extracted_json: Record<string, unknown>;
  metadata_json?: Record<string, unknown>;
  created_at: string;
};

export type AuditEvent = {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  payload_json: Record<string, unknown>;
  created_at: string;
};

export type Instance = {
  id: string;
  title: string;
  status: string;
  current_node_id?: string | null;
  variables_json: Record<string, unknown>;
  exports_json: Record<string, unknown>;
  started_at: string;
  updated_at: string;
  completed_at?: string | null;
  requester?: User | null;
  active_tasks?: Task[];
  active_approvals?: Approval[];
  tasks?: Task[];
  approvals?: Approval[];
  timeline?: AuditEvent[];
  documents?: DocumentRecord[];
};

export type InboxPayload = {
  tasks: Array<{
    id: string;
    process_instance_id: string;
    title: string;
    node_id: string;
    created_at: string;
  }>;
  approvals: Array<{
    id: string;
    process_instance_id: string;
    node_id: string;
    approver_role?: string | null;
    created_at: string;
  }>;
};
