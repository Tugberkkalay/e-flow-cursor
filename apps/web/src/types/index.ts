export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "approver" | "viewer";
  department?: string;
  cost_center?: string;
  manager_id?: string;
  org_id: string;
}

export interface FlowDefinition {
  id: string;
  name: string;
  description?: string;
  status: "draft" | "published";
  current_version?: number;
  form_id?: string;
  created_at: string;
  updated_at: string;
  org_id: string;
}

export interface FlowVersion {
  id: string;
  flow_id: string;
  version: number;
  graph_json: GraphData;
  status: "draft" | "published";
  created_at: string;
}

export interface GraphData {
  nodes: FlowNode[];
  edges: FlowEdge[];
  viewport?: { x: number; y: number; zoom: number };
}

export interface FlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: NodeData;
  width?: number;
  height?: number;
}

export interface NodeData {
  label: string;
  nodeType: string;
  engineType: string;
  category: string;
  config: Record<string, any>;
  icon?: string;
  color?: string;
  description?: string;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  type?: string;
  data?: Record<string, any>;
  animated?: boolean;
}

export interface FormDefinition {
  id: string;
  name: string;
  description?: string;
  status: "draft" | "published";
  version: number;
  fields: FormField[];
  created_at: string;
  updated_at: string;
  org_id: string;
}

export interface FormField {
  id: string;
  key: string;
  label: string;
  type: FieldType;
  required: boolean;
  placeholder?: string;
  default_value?: any;
  options?: { label: string; value: string }[];
  rules?: FieldRule[];
  calculation?: string;
  config?: Record<string, any>;
  order: number;
}

export type FieldType =
  | "text"
  | "textarea"
  | "number"
  | "money"
  | "date"
  | "dropdown"
  | "multi_select"
  | "boolean"
  | "file_upload"
  | "line_items";

export interface FieldRule {
  id: string;
  type: "visibility" | "required";
  condition: {
    field_key: string;
    operator: "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "contains" | "in";
    value: any;
  };
}

export interface ProcessInstance {
  id: string;
  flow_id: string;
  flow_name: string;
  version_id: string;
  status: "running" | "completed" | "failed" | "cancelled" | "pending";
  variables: Record<string, any>;
  current_node_id?: string;
  current_node_label?: string;
  requester_id: string;
  requester_name: string;
  started_at: string;
  completed_at?: string;
  org_id: string;
}

export interface NodeInstance {
  id: string;
  instance_id: string;
  node_id: string;
  node_type: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error?: string;
  started_at?: string;
  completed_at?: string;
  assignee_id?: string;
  retry_count: number;
}

export interface TaskInstance {
  id: string;
  instance_id: string;
  node_instance_id: string;
  task_type: string;
  title: string;
  description?: string;
  assignee_id: string;
  assignee_name?: string;
  status: "pending" | "completed" | "cancelled";
  form_data?: Record<string, any>;
  due_date?: string;
  created_at: string;
  completed_at?: string;
  flow_name?: string;
  instance_title?: string;
}

export interface ApprovalInstance {
  id: string;
  instance_id: string;
  node_instance_id: string;
  approver_id: string;
  approver_name?: string;
  decision?: "approved" | "rejected" | "revision";
  comment?: string;
  decided_at?: string;
  created_at: string;
  flow_name?: string;
  instance_title?: string;
  amount?: number;
}

export interface AuditEvent {
  id: string;
  instance_id?: string;
  user_id?: string;
  user_name?: string;
  event_type: string;
  event_data: Record<string, any>;
  timestamp: string;
  org_id: string;
}

export interface Document {
  id: string;
  instance_id: string;
  doc_type: string;
  filename: string;
  version: number;
  extracted_json?: Record<string, any>;
  uploaded_by: string;
  uploaded_at: string;
  storage_key: string;
}

export interface Delegation {
  id: string;
  from_user_id: string;
  to_user_id: string;
  start_date: string;
  end_date: string;
  role_scope?: string;
  active: boolean;
}

export interface ApprovalLimit {
  id: string;
  department?: string;
  budget_type?: string;
  currency: string;
  min_amount: number;
  max_amount: number;
  approver_role: string;
  org_id: string;
}

export type NodeCategory =
  | "triggers"
  | "human_tasks"
  | "approval"
  | "logic"
  | "data"
  | "document"
  | "integrations"
  | "events"
  | "error"
  | "reuse";
