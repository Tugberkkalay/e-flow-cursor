from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import (
    ApprovalInstance,
    ApprovalLimit,
    AuditEvent,
    NodeInstance,
    ProcessInstance,
    ProcessVersion,
    TaskInstance,
    User,
)
from app.services.expression_engine import resolve_expression, safe_eval


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return uuid4().hex


class LegacyNodeAdapter:
    """Compatibility adapter skeleton for old node payloads."""

    @staticmethod
    def adapt(node: dict[str, Any]) -> dict[str, Any]:
        data = node.get("data", {})
        if "engineType" not in data and node.get("type"):
            data["engineType"] = node["type"]
        node["data"] = data
        return node


class BPMEngine:
    def __init__(self, db: Session):
        self.db = db

    def _emit_audit(
        self,
        org_id: str,
        event_type: str,
        *,
        instance_id: str | None = None,
        user_id: str | None = None,
        flow_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.db.add(
            AuditEvent(
                org_id=org_id,
                process_instance_id=instance_id,
                flow_id=flow_id,
                user_id=user_id,
                event_type=event_type,
                payload_json=payload or {},
            )
        )

    def _graph_index(self, version: ProcessVersion) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
        graph = version.graph_json or {}
        nodes = {node["id"]: LegacyNodeAdapter.adapt(node) for node in graph.get("nodes", [])}
        edges: dict[str, list[dict[str, Any]]] = {}
        for edge in graph.get("edges", []):
            edges.setdefault(edge["source"], []).append(edge)
        return nodes, edges

    def _build_context(self, instance: ProcessInstance) -> dict[str, Any]:
        context = {
            "form": {},
            "docs": {},
            "extract": {},
            "selection": {},
            "approval": {},
            "gen": {},
            "calc": {},
            "flags": {},
            "exports": instance.exports_json or {},
            "system": {},
        }
        context.update(instance.variables_json or {})
        return context

    def _save_context(self, instance: ProcessInstance, context: dict[str, Any]) -> None:
        instance.variables_json = context

    def _choose_edge(self, node: dict[str, Any], outgoing: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any] | None:
        if not outgoing:
            return None
        node_type = (node.get("data", {}).get("engineType") or node.get("type") or "").lower()
        node_data = node.get("data", {})

        if node_type in {"gateway", "if", "switch"}:
            if node_data.get("mode") == "switch":
                key = node_data.get("expression", "''")
                switch_value = safe_eval(key, context) if "{{" not in key else resolve_expression(key, context)
                for edge in outgoing:
                    if edge.get("data", {}).get("case") == switch_value:
                        return edge
                for edge in outgoing:
                    if edge.get("data", {}).get("default"):
                        return edge
                return outgoing[0]

            for edge in outgoing:
                cond = edge.get("data", {}).get("condition")
                if not cond:
                    continue
                expr = cond
                result = resolve_expression(f"{{{{ {expr} }}}}", context) if "{{" not in expr else resolve_expression(expr, context)
                if bool(result):
                    return edge
            # fallback
            default_edges = [e for e in outgoing if e.get("data", {}).get("default")]
            return default_edges[0] if default_edges else outgoing[0]

        return outgoing[0]

    def _route_approval_role(self, context: dict[str, Any], org_id: str) -> str:
        form = context.get("form", {})
        amount = float(form.get("total_amount", 0) or 0)
        dept = form.get("department") or context.get("system", {}).get("department") or "general"
        currency = form.get("currency", "TRY")
        stmt = select(ApprovalLimit).where(
            ApprovalLimit.org_id == org_id,
            ApprovalLimit.department == dept,
            ApprovalLimit.currency == currency,
            ApprovalLimit.min_amount <= amount,
            ApprovalLimit.max_amount >= amount,
        )
        match = self.db.execute(stmt).scalar_one_or_none()
        if match:
            return match.approver_role
        return "approver"

    def _create_task(self, instance: ProcessInstance, node_instance: NodeInstance, node: dict[str, Any]) -> None:
        data = node.get("data", {})
        self.db.add(
            TaskInstance(
                org_id=instance.org_id,
                process_instance_id=instance.id,
                node_instance_id=node_instance.id,
                task_type=data.get("taskType", "human"),
                title=data.get("title", node.get("id", "Task")),
                assignee_role=data.get("assigneeRole"),
                assignee_id=data.get("assigneeId"),
                payload_json=data.get("payload", {}),
            )
        )

    def _create_approval(self, instance: ProcessInstance, node_instance: NodeInstance, node: dict[str, Any], context: dict[str, Any]) -> None:
        data = node.get("data", {})
        role = data.get("assigneeRole")
        if data.get("byLimitMatrix"):
            role = self._route_approval_role(context, instance.org_id)
        self.db.add(
            ApprovalInstance(
                org_id=instance.org_id,
                process_instance_id=instance.id,
                node_instance_id=node_instance.id,
                strategy=data.get("strategy", "single"),
                assignee_role=role,
                assignee_id=data.get("assigneeId"),
            )
        )
        self._emit_audit(
            instance.org_id,
            "approval.created",
            instance_id=instance.id,
            payload={"node_id": node.get("id"), "assignee_role": role},
        )

    def run_until_wait(self, instance: ProcessInstance, actor: User | None = None) -> ProcessInstance:
        version = self.db.get(ProcessVersion, instance.process_version_id)
        if not version:
            raise ValueError("Process version not found")
        nodes, edges = self._graph_index(version)
        context = self._build_context(instance)

        while instance.status in {"running", "ready"} and instance.current_node_id:
            node = nodes.get(instance.current_node_id)
            if not node:
                instance.status = "error"
                self._emit_audit(instance.org_id, "instance.error", instance_id=instance.id, payload={"message": "node missing"})
                break

            engine_type = (node.get("data", {}).get("engineType") or node.get("type") or "").lower()
            node_instance = NodeInstance(
                org_id=instance.org_id,
                process_instance_id=instance.id,
                node_id=node["id"],
                node_type=engine_type,
                node_version=int(node.get("data", {}).get("nodeVersion", 1)),
                status="running",
                input_json=context,
            )
            self.db.add(node_instance)
            self.db.flush()
            self._emit_audit(instance.org_id, "node.started", instance_id=instance.id, payload={"node_id": node["id"], "type": engine_type})

            if engine_type in {"start", "manualstart", "event", "service", "script", "setfields", "calculate", "transform"}:
                if mappings := node.get("data", {}).get("setContext", {}):
                    for key, value in mappings.items():
                        if isinstance(value, str) and "{{" in value:
                            resolved = resolve_expression(value, context)
                        else:
                            resolved = value
                        self._set_by_path(context, key, resolved)
                if engine_type == "service":
                    # Mock integration output for MVP.
                    out_key = node.get("data", {}).get("outputKey", "gen.service_result")
                    self._set_by_path(context, out_key, {"ok": True, "idempotency_key": _id()})

                node_instance.status = "completed"
                node_instance.output_json = {"context_patch": node.get("data", {}).get("setContext", {})}
                node_instance.ended_at = _now()
                chosen = self._choose_edge(node, edges.get(node["id"], []), context)
                if chosen:
                    instance.current_node_id = chosen["target"]
                else:
                    instance.current_node_id = None
                    instance.status = "completed"
                    instance.finished_at = _now()
                self._emit_audit(
                    instance.org_id, "node.completed", instance_id=instance.id, payload={"node_id": node["id"], "next": instance.current_node_id}
                )
                continue

            if engine_type in {"humantask", "human", "formfill", "documentupload", "review"}:
                self._create_task(instance, node_instance, node)
                node_instance.status = "waiting"
                instance.status = "waiting_task"
                self._emit_audit(instance.org_id, "task.created", instance_id=instance.id, payload={"node_id": node["id"]})
                break

            if engine_type in {"approvaltask", "approval", "multiapproval"}:
                self._create_approval(instance, node_instance, node, context)
                node_instance.status = "waiting"
                instance.status = "waiting_approval"
                break

            if engine_type in {"gateway", "if", "switch", "parallelsplit", "paralleljoin"}:
                chosen = self._choose_edge(node, edges.get(node["id"], []), context)
                node_instance.status = "completed"
                node_instance.output_json = {"selected_edge": chosen["id"] if chosen else None}
                node_instance.ended_at = _now()
                if chosen:
                    instance.current_node_id = chosen["target"]
                else:
                    instance.status = "error"
                self._emit_audit(
                    instance.org_id, "gateway.routed", instance_id=instance.id, payload={"node_id": node["id"], "edge_id": chosen["id"] if chosen else None}
                )
                continue

            if engine_type in {"end"}:
                export_map = node.get("data", {}).get("exportMapping", {})
                exports: dict[str, Any] = {}
                for key, expr in export_map.items():
                    if isinstance(expr, str):
                        exports[key] = resolve_expression(expr, context) if "{{" in expr else safe_eval(expr, context)
                    else:
                        exports[key] = expr
                context["exports"] = exports
                instance.exports_json = exports
                node_instance.status = "completed"
                node_instance.output_json = exports
                node_instance.ended_at = _now()
                instance.current_node_id = None
                instance.status = "completed"
                instance.finished_at = _now()
                self._emit_audit(instance.org_id, "instance.completed", instance_id=instance.id, payload={"exports": exports})
                break

            if engine_type in {"stoperror"}:
                instance.status = "error"
                node_instance.status = "failed"
                node_instance.error_message = node.get("data", {}).get("message", "Stopped by flow")
                node_instance.ended_at = _now()
                self._emit_audit(instance.org_id, "instance.error", instance_id=instance.id, payload={"node_id": node["id"]})
                break

            # Unknown node type should fail explicitly.
            node_instance.status = "failed"
            node_instance.error_message = f"Unknown node type: {engine_type}"
            node_instance.ended_at = _now()
            instance.status = "error"
            self._emit_audit(instance.org_id, "instance.error", instance_id=instance.id, payload={"node_id": node["id"], "reason": "unknown_type"})
            break

        self._save_context(instance, context)
        self.db.add(instance)
        return instance

    def complete_task(self, task: TaskInstance, user: User, output: dict[str, Any]) -> None:
        if task.status != "pending":
            raise ValueError("Task already completed")
        task.status = "completed"
        task.completed_by = user.id
        task.completed_at = _now()

        instance = self.db.get(ProcessInstance, task.process_instance_id)
        node_instance = self.db.get(NodeInstance, task.node_instance_id)
        if not instance or not node_instance:
            raise ValueError("Task context missing")
        context = instance.variables_json or {}
        context.setdefault("form", {}).update(output)
        node_instance.status = "completed"
        node_instance.output_json = output
        node_instance.ended_at = _now()

        version = self.db.get(ProcessVersion, instance.process_version_id)
        if not version:
            raise ValueError("Version missing")
        _, edges = self._graph_index(version)
        outgoing = edges.get(node_instance.node_id, [])
        instance.current_node_id = outgoing[0]["target"] if outgoing else None
        instance.status = "running"
        instance.variables_json = context
        self._emit_audit(instance.org_id, "task.completed", instance_id=instance.id, user_id=user.id, payload={"task_id": task.id})
        self.run_until_wait(instance, actor=user)

    def decide_approval(self, approval: ApprovalInstance, user: User, decision: str, comment: str | None = None) -> None:
        if approval.status != "pending":
            raise ValueError("Approval already decided")
        approval.status = "completed"
        approval.decision = decision
        approval.comment = comment
        approval.decided_by = user.id
        approval.decided_at = _now()

        instance = self.db.get(ProcessInstance, approval.process_instance_id)
        node_instance = self.db.get(NodeInstance, approval.node_instance_id)
        if not instance or not node_instance:
            raise ValueError("Approval context missing")
        context = instance.variables_json or {}
        context.setdefault("approval", {})["decision"] = decision
        node_instance.status = "completed"
        node_instance.output_json = {"decision": decision, "comment": comment}
        node_instance.ended_at = _now()

        version = self.db.get(ProcessVersion, instance.process_version_id)
        if not version:
            raise ValueError("Version missing")
        _, edges = self._graph_index(version)
        outgoing = edges.get(node_instance.node_id, [])
        chosen = outgoing[0] if outgoing else None
        for edge in outgoing:
            cond = edge.get("data", {}).get("condition")
            if cond and bool(safe_eval(cond, context)):
                chosen = edge
                break
            if edge.get("label", "").lower().startswith("reject") and decision == "reject":
                chosen = edge
                break
        instance.current_node_id = chosen["target"] if chosen else None
        instance.status = "running"
        instance.variables_json = context
        self._emit_audit(
            instance.org_id, "approval.decided", instance_id=instance.id, user_id=user.id, payload={"approval_id": approval.id, "decision": decision}
        )
        self.run_until_wait(instance, actor=user)

    @staticmethod
    def _set_by_path(root: dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = root
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
