"""
BPM Engine: Lazy step-by-step execution.
Each call to advance() processes the current node and returns the next one.
"""
from __future__ import annotations
import uuid
import json
import httpx
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.engine.expression import ExpressionEngine
from app.models.instance import (
    ProcessInstance,
    NodeInstance,
    TaskInstance,
    ApprovalInstance,
    AuditEvent,
)
from app.models.flow import ProcessVersion
from app.models.user import User, ApprovalLimit


class BPMEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.expr = ExpressionEngine()

    async def start_instance(
        self,
        version_id: uuid.UUID,
        title: str,
        initial_inputs: dict,
        started_by_id: uuid.UUID | None,
        org_id: str = "default",
    ) -> ProcessInstance:
        version_result = await self.db.execute(
            select(ProcessVersion).where(ProcessVersion.id == version_id)
        )
        version = version_result.scalar_one_or_none()
        if not version:
            raise ValueError(f"ProcessVersion {version_id} not found")
        if version.status != "published":
            raise ValueError("Can only start instances from published versions")

        graph = version.graph_json
        start_node = self._find_start_node(graph)

        instance = ProcessInstance(
            org_id=org_id,
            definition_id=version.definition_id,
            version_id=version_id,
            title=title,
            status="running",
            current_node_id=start_node["id"] if start_node else None,
            variables={"form": initial_inputs, "system": {"started_by": str(started_by_id), "started_at": datetime.utcnow().isoformat()}},
            exports={},
            started_by=started_by_id,
        )
        self.db.add(instance)
        await self.db.flush()

        await self._emit_audit(instance, "instance.started", {"title": title, "version_id": str(version_id)}, started_by_id)

        if start_node:
            await self._execute_node(instance, start_node, graph)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def advance(
        self,
        instance_id: uuid.UUID,
        action: str,
        payload: dict,
        actor_id: uuid.UUID | None = None,
    ) -> ProcessInstance:
        """
        Advance the instance by completing a node/task/approval.
        action: complete_task | approve | reject | revision | retry | skip | cancel | reassign
        """
        result = await self.db.execute(select(ProcessInstance).where(ProcessInstance.id == instance_id))
        instance = result.scalar_one_or_none()
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")

        if action == "cancel":
            instance.status = "cancelled"
            instance.completed_at = datetime.utcnow()
            await self._emit_audit(instance, "instance.cancelled", payload, actor_id)
            await self.db.commit()
            return instance

        version_result = await self.db.execute(select(ProcessVersion).where(ProcessVersion.id == instance.version_id))
        version = version_result.scalar_one_or_none()
        graph = version.graph_json

        if action in ("approve", "reject", "revision"):
            await self._handle_approval_decision(instance, action, payload, actor_id, graph)
        elif action == "complete_task":
            await self._handle_task_completion(instance, payload, actor_id, graph)
        elif action == "retry":
            await self._retry_current_node(instance, graph, actor_id)
        elif action == "skip":
            await self._skip_current_node(instance, graph, actor_id)
        elif action == "reassign":
            await self._reassign_task(instance, payload, actor_id)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def _execute_node(self, instance: ProcessInstance, node: dict, graph: dict):
        node_type = node.get("type", "")
        node_id = node["id"]

        node_inst = NodeInstance(
            org_id=instance.org_id,
            process_instance_id=instance.id,
            node_id=node_id,
            node_type=node_type,
            node_label=node.get("data", {}).get("label"),
            status="running",
            input_data=dict(instance.variables),
            started_at=datetime.utcnow(),
        )
        self.db.add(node_inst)
        await self.db.flush()

        instance.current_node_id = node_id

        await self._emit_audit(instance, "node.started", {"node_id": node_id, "node_type": node_type})

        engine_type = node.get("data", {}).get("engineType", node_type)

        if engine_type in ("ManualStart", "FormSubmitTrigger", "APITrigger", "ScheduledTrigger"):
            await self._complete_node(node_inst, {})
            next_node = self._get_next_node(node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

        elif engine_type in ("HumanTask", "FormFill", "DataEntry", "ReviewComment",
                              "DocumentUpload", "DeliveryAcceptance", "ReworkTask",
                              "VendorSelection", "ManualCompensation"):
            await self._create_human_task(instance, node, node_inst)
            # stays waiting for user

        elif engine_type in ("ApprovalTask", "Approval", "MultiApproval", "ApprovalByLimitMatrix"):
            await self._create_approval(instance, node, node_inst)

        elif engine_type in ("Gateway", "IF", "Switch"):
            await self._execute_gateway(instance, node, node_inst, graph)

        elif engine_type in ("ParallelSplit", "ParallelJoin"):
            await self._execute_parallel(instance, node, node_inst, graph)

        elif engine_type in ("ServiceTask", "HTTPRequest", "EmailSend", "ERPAdapter"):
            await self._execute_service_task(instance, node, node_inst, graph)

        elif engine_type in ("ScriptTask", "Calculate", "SetFields", "Transform",
                              "Aggregate", "Compare", "NormalizeMoney"):
            await self._execute_script_task(instance, node, node_inst, graph)

        elif engine_type in ("SubprocessCall",):
            await self._execute_subprocess(instance, node, node_inst, graph)

        elif engine_type in ("End",):
            await self._execute_end(instance, node, node_inst)

        elif engine_type in ("StopError",):
            await self._execute_stop_error(instance, node, node_inst)

        elif engine_type in ("AuditEmit",):
            cfg = node.get("data", {}).get("config", {})
            msg = self.expr.resolve(cfg.get("message", "Audit emitted"), instance.variables)
            await self._emit_audit(instance, f"custom.{cfg.get('event_type','audit')}", {"message": msg})
            await self._complete_node(node_inst, {"message": msg})
            next_node = self._get_next_node(node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

        else:
            # Unknown → auto-complete and advance
            await self._complete_node(node_inst, {"note": f"auto-completed unknown type: {engine_type}"})
            next_node = self._get_next_node(node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

    async def _create_human_task(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance):
        cfg = node.get("data", {}).get("config", {})
        assigned_role = self.expr.resolve(cfg.get("assignee_role", ""), instance.variables)
        assigned_to = None

        if cfg.get("assignee_user_id"):
            try:
                assigned_to = uuid.UUID(cfg["assignee_user_id"])
            except Exception:
                pass

        task = TaskInstance(
            org_id=instance.org_id,
            process_instance_id=instance.id,
            node_instance_id=node_inst.id,
            node_id=node["id"],
            task_type=node.get("data", {}).get("engineType", "HumanTask"),
            title=self.expr.resolve(cfg.get("title", node.get("data", {}).get("label", "Task")), instance.variables),
            description=self.expr.resolve(cfg.get("description", ""), instance.variables),
            status="pending",
            assigned_to=assigned_to,
            assigned_role=assigned_role if assigned_role else None,
            form_data=self.expr.resolve_all(cfg.get("initial_data", {}), instance.variables),
        )
        self.db.add(task)
        await self._emit_audit(instance, "task.created", {"task_title": task.title, "node_id": node["id"]})

    async def _create_approval(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance):
        cfg = node.get("data", {}).get("config", {})
        engine_type = node.get("data", {}).get("engineType", "Approval")

        approver_id = None
        approver_role = cfg.get("approver_role", "approver")

        if engine_type == "ApprovalByLimitMatrix":
            approver_id, approver_role = await self._resolve_limit_matrix_approver(instance, cfg)

        amount = None
        if cfg.get("amount_field"):
            amount = self.expr.resolve(f"{{{{{cfg['amount_field']}}}}}", instance.variables)
            try:
                amount = float(amount) if amount is not None else None
            except Exception:
                amount = None

        approval = ApprovalInstance(
            org_id=instance.org_id,
            process_instance_id=instance.id,
            node_instance_id=node_inst.id,
            node_id=node["id"],
            approver_id=approver_id,
            approver_role=approver_role,
            status="pending",
            amount=amount,
        )
        self.db.add(approval)
        await self._emit_audit(instance, "approval.requested", {
            "node_id": node["id"],
            "approver_role": approver_role,
            "amount": str(amount) if amount else None,
        })

    async def _resolve_limit_matrix_approver(self, instance: ProcessInstance, cfg: dict) -> tuple:
        amount_val = self.expr.resolve(cfg.get("amount_expr", "{{ form.total_amount }}"), instance.variables)
        try:
            amount = float(amount_val or 0)
        except Exception:
            amount = 0

        result = await self.db.execute(
            select(ApprovalLimit).where(
                ApprovalLimit.org_id == instance.org_id,
                ApprovalLimit.min_amount <= amount,
            ).order_by(ApprovalLimit.min_amount.desc()).limit(1)
        )
        limit = result.scalar_one_or_none()
        if limit:
            return limit.approver_id, limit.approver_role or "approver"
        return None, "approver"

    async def _execute_gateway(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance, graph: dict):
        cfg = node.get("data", {}).get("config", {})
        engine_type = node.get("data", {}).get("engineType", "IF")

        branches = cfg.get("branches", [])
        chosen_branch = None

        for branch in branches:
            condition = branch.get("condition", {})
            if not condition or self.expr.evaluate_condition(condition, instance.variables):
                chosen_branch = branch
                break

        if chosen_branch is None and branches:
            # default branch (last)
            chosen_branch = branches[-1]

        output_data = {"chosen_branch": chosen_branch.get("label") if chosen_branch else None}
        await self._complete_node(node_inst, output_data)

        # Find the edge matching the branch handle
        if chosen_branch:
            handle_id = chosen_branch.get("handle", chosen_branch.get("label", "default"))
            next_node = self._get_next_node_by_handle(node, graph, handle_id, instance.variables)
        else:
            next_node = self._get_next_node(node, graph, instance.variables)

        if next_node:
            await self._execute_node(instance, next_node, graph)

    async def _execute_parallel(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance, graph: dict):
        # Simplified parallel: complete and advance to all outgoing edges
        await self._complete_node(node_inst, {})
        next_nodes = self._get_all_next_nodes(node, graph)
        for nn in next_nodes:
            await self._execute_node(instance, nn, graph)

    async def _execute_service_task(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance, graph: dict):
        cfg = node.get("data", {}).get("config", {})
        url = self.expr.resolve(cfg.get("url", ""), instance.variables)
        method = cfg.get("method", "POST")
        headers = self.expr.resolve_all(cfg.get("headers", {}), instance.variables)
        body = self.expr.resolve_all(cfg.get("body", {}), instance.variables)

        output_data = {"url": url, "method": method}

        if url and not cfg.get("mock", True):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.request(method, url, json=body, headers=headers)
                    output_data["status_code"] = resp.status_code
                    try:
                        output_data["response"] = resp.json()
                    except Exception:
                        output_data["response_text"] = resp.text[:500]
            except Exception as e:
                output_data["error"] = str(e)
        else:
            # mock response
            output_data["mock"] = True
            output_data["response"] = cfg.get("mock_response", {"status": "ok", "message": "mock integration called"})

        # Write to context
        output_key = cfg.get("output_key", f"gen.{node['id']}")
        self._set_nested(instance.variables, output_key, output_data["response"] if not output_data.get("error") else None)

        await self._complete_node(node_inst, output_data)
        next_node = self._get_next_node(node, graph, instance.variables)
        if next_node:
            await self._execute_node(instance, next_node, graph)

    async def _execute_script_task(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance, graph: dict):
        cfg = node.get("data", {}).get("config", {})
        engine_type = node.get("data", {}).get("engineType", "ScriptTask")

        output_data = {}

        if engine_type == "Calculate":
            for calc in cfg.get("calculations", []):
                field = calc.get("output_field", "")
                expr = calc.get("expression", "")
                value = self.expr.resolve(expr, instance.variables)
                if field:
                    self._set_nested(instance.variables, field, value)
                    output_data[field] = value

        elif engine_type in ("SetFields", "Transform"):
            for mapping in cfg.get("mappings", []):
                target = mapping.get("target", "")
                source = mapping.get("source", "")
                value = self.expr.resolve(source, instance.variables)
                if target:
                    self._set_nested(instance.variables, target, value)
                    output_data[target] = value

        elif engine_type == "NormalizeMoney":
            field = cfg.get("amount_field", "form.total_amount")
            currency_field = cfg.get("currency_field", "form.currency")
            rate_field = cfg.get("rate_field", "")
            amount = self.expr.resolve(f"{{{{{field}}}}}", instance.variables)
            rate = self.expr.resolve(f"{{{{{rate_field}}}}}", instance.variables) if rate_field else 1
            try:
                normalized = float(amount or 0) * float(rate or 1)
                self._set_nested(instance.variables, cfg.get("output_field", "calc.normalized_amount"), normalized)
                output_data["normalized_amount"] = normalized
            except Exception:
                pass

        elif engine_type == "PolicyCheck":
            flags = []
            rules = cfg.get("rules", [])
            for rule in rules:
                if self.expr.evaluate_condition(rule.get("condition", {}), instance.variables):
                    flags.append({"rule": rule.get("name", ""), "severity": rule.get("severity", "warning")})
            self._set_nested(instance.variables, "flags.policy_flags", flags)
            output_data["flags"] = flags

        elif engine_type == "ThreeWayMatch":
            po_amount = self.expr.resolve(cfg.get("po_amount", "{{ gen.po.amount }}"), instance.variables)
            inv_amount = self.expr.resolve(cfg.get("invoice_amount", "{{ form.invoice_amount }}"), instance.variables)
            tolerance = float(cfg.get("tolerance_pct", 5))
            try:
                diff_pct = abs(float(po_amount or 0) - float(inv_amount or 0)) / max(float(po_amount or 1), 0.01) * 100
                matched = diff_pct <= tolerance
                match_status = "matched" if matched else "mismatch"
            except Exception:
                match_status = "ambiguous"
                diff_pct = 0
            self._set_nested(instance.variables, "flags.match_status", match_status)
            self._set_nested(instance.variables, "flags.diff_pct", diff_pct)
            output_data = {"match_status": match_status, "diff_pct": diff_pct}

        else:
            # Generic script: execute expression mappings
            for mapping in cfg.get("mappings", []):
                target = mapping.get("target", "")
                source = mapping.get("source", "")
                value = self.expr.resolve(source, instance.variables)
                if target:
                    self._set_nested(instance.variables, target, value)
                    output_data[target] = value

        await self._complete_node(node_inst, output_data)
        next_node = self._get_next_node(node, graph, instance.variables)
        if next_node:
            await self._execute_node(instance, next_node, graph)

    async def _execute_subprocess(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance, graph: dict):
        cfg = node.get("data", {}).get("config", {})
        # Stub: record input/output mapping
        input_mapping = self.expr.resolve_all(cfg.get("input_mapping", {}), instance.variables)
        output_mapping = cfg.get("output_mapping", {})

        await self._emit_audit(instance, "subprocess.called", {
            "subprocess_flow_id": cfg.get("subprocess_flow_id"),
            "input_mapping": input_mapping,
        })

        # Stub outputs
        for target, source in output_mapping.items():
            self._set_nested(instance.variables, target, f"<subprocess_output:{source}>")

        await self._complete_node(node_inst, {"stub": True, "input_mapping": input_mapping})
        next_node = self._get_next_node(node, graph, instance.variables)
        if next_node:
            await self._execute_node(instance, next_node, graph)

    async def _execute_end(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance):
        cfg = node.get("data", {}).get("config", {})
        end_status = cfg.get("status", "completed")

        # Resolve exported outputs
        for export in cfg.get("exports", []):
            key = export.get("key", "")
            expr = export.get("expression", f"{{{{{key}}}}}")
            value = self.expr.resolve(expr, instance.variables)
            if key:
                instance.exports[key] = value

        instance.status = end_status
        instance.completed_at = datetime.utcnow()

        await self._complete_node(node_inst, {"exports": instance.exports})
        await self._emit_audit(instance, "instance.completed", {"status": end_status, "exports": instance.exports})

    async def _execute_stop_error(self, instance: ProcessInstance, node: dict, node_inst: NodeInstance):
        cfg = node.get("data", {}).get("config", {})
        error_msg = self.expr.resolve(cfg.get("error_message", "Process stopped with error"), instance.variables)
        instance.status = "failed"
        instance.completed_at = datetime.utcnow()
        node_inst.error_message = error_msg
        await self._complete_node(node_inst, {"error": error_msg})
        await self._emit_audit(instance, "instance.failed", {"error": error_msg})

    async def _handle_task_completion(self, instance: ProcessInstance, payload: dict, actor_id, graph: dict):
        node_id = instance.current_node_id

        task_result = await self.db.execute(
            select(TaskInstance).where(
                TaskInstance.process_instance_id == instance.id,
                TaskInstance.node_id == node_id,
                TaskInstance.status == "pending",
            ).order_by(TaskInstance.created_at.desc())
        )
        task = task_result.scalar_one_or_none()
        if not task:
            return

        task.status = "completed"
        task.result_data = payload.get("data", {})
        task.comment = payload.get("comment")
        task.completed_at = datetime.utcnow()

        # Merge task result into instance variables
        if task.result_data:
            for k, v in task.result_data.items():
                self._set_nested(instance.variables, f"form.{k}", v)

        # Find matching node_instance
        node_inst_result = await self.db.execute(
            select(NodeInstance).where(
                NodeInstance.process_instance_id == instance.id,
                NodeInstance.node_id == node_id,
                NodeInstance.status == "running",
            ).order_by(NodeInstance.started_at.desc())
        )
        node_inst = node_inst_result.scalar_one_or_none()
        if node_inst:
            await self._complete_node(node_inst, task.result_data)

        await self._emit_audit(instance, "task.completed", {"node_id": node_id, "actor_id": str(actor_id)}, actor_id)

        # Find the current node in graph and advance
        current_node = self._find_node_by_id(graph, node_id)
        if current_node:
            next_node = self._get_next_node(current_node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

    async def _handle_approval_decision(self, instance: ProcessInstance, action: str, payload: dict, actor_id, graph: dict):
        node_id = instance.current_node_id
        decision_map = {"approve": "approved", "reject": "rejected", "revision": "revision_requested"}
        decision = decision_map.get(action, action)

        approval_result = await self.db.execute(
            select(ApprovalInstance).where(
                ApprovalInstance.process_instance_id == instance.id,
                ApprovalInstance.node_id == node_id,
                ApprovalInstance.status == "pending",
            ).order_by(ApprovalInstance.created_at.desc())
        )
        approval = approval_result.scalar_one_or_none()
        if not approval:
            return

        approval.decision = decision
        approval.comment = payload.get("comment")
        approval.status = "decided"
        approval.decided_at = datetime.utcnow()
        if actor_id:
            approval.approver_id = actor_id

        self._set_nested(instance.variables, "approval.last_decision", decision)
        self._set_nested(instance.variables, "approval.last_comment", payload.get("comment", ""))

        node_inst_result = await self.db.execute(
            select(NodeInstance).where(
                NodeInstance.process_instance_id == instance.id,
                NodeInstance.node_id == node_id,
                NodeInstance.status == "running",
            ).order_by(NodeInstance.started_at.desc())
        )
        node_inst = node_inst_result.scalar_one_or_none()
        if node_inst:
            await self._complete_node(node_inst, {"decision": decision})

        await self._emit_audit(instance, f"approval.{decision}", {
            "node_id": node_id,
            "decision": decision,
            "comment": payload.get("comment"),
        }, actor_id)

        current_node = self._find_node_by_id(graph, node_id)
        if current_node:
            if decision == "revision_requested":
                # Go back to previous human task if configured
                cfg = current_node.get("data", {}).get("config", {})
                revision_target = cfg.get("revision_target_node")
                if revision_target:
                    rev_node = self._find_node_by_id(graph, revision_target)
                    if rev_node:
                        await self._execute_node(instance, rev_node, graph)
                        return
            next_node = self._get_next_node_by_handle(current_node, graph, decision, instance.variables)
            if not next_node:
                next_node = self._get_next_node(current_node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

    async def _retry_current_node(self, instance: ProcessInstance, graph: dict, actor_id):
        node_id = instance.current_node_id
        if not node_id:
            return
        current_node = self._find_node_by_id(graph, node_id)
        if current_node:
            await self._emit_audit(instance, "node.retry", {"node_id": node_id}, actor_id)
            await self._execute_node(instance, current_node, graph)

    async def _skip_current_node(self, instance: ProcessInstance, graph: dict, actor_id):
        node_id = instance.current_node_id
        current_node = self._find_node_by_id(graph, node_id)
        if current_node:
            node_inst_result = await self.db.execute(
                select(NodeInstance).where(
                    NodeInstance.process_instance_id == instance.id,
                    NodeInstance.node_id == node_id,
                    NodeInstance.status == "running",
                )
            )
            node_inst = node_inst_result.scalar_one_or_none()
            if node_inst:
                node_inst.status = "skipped"
            await self._emit_audit(instance, "node.skipped", {"node_id": node_id}, actor_id)
            next_node = self._get_next_node(current_node, graph, instance.variables)
            if next_node:
                await self._execute_node(instance, next_node, graph)

    async def _reassign_task(self, instance: ProcessInstance, payload: dict, actor_id):
        node_id = instance.current_node_id
        task_result = await self.db.execute(
            select(TaskInstance).where(
                TaskInstance.process_instance_id == instance.id,
                TaskInstance.node_id == node_id,
                TaskInstance.status == "pending",
            )
        )
        task = task_result.scalar_one_or_none()
        if task and payload.get("new_assignee_id"):
            try:
                task.assigned_to = uuid.UUID(payload["new_assignee_id"])
                await self._emit_audit(instance, "task.reassigned", {
                    "node_id": node_id,
                    "new_assignee": payload["new_assignee_id"],
                }, actor_id)
            except Exception:
                pass

    async def _complete_node(self, node_inst: NodeInstance, output_data: dict):
        node_inst.status = "completed"
        node_inst.output_data = output_data
        node_inst.completed_at = datetime.utcnow()
        if node_inst.started_at:
            node_inst.duration_ms = int((node_inst.completed_at - node_inst.started_at).total_seconds() * 1000)

    async def _emit_audit(self, instance: ProcessInstance, event_type: str, payload: dict, actor_id=None):
        event = AuditEvent(
            org_id=instance.org_id,
            process_instance_id=instance.id,
            event_type=event_type,
            actor_id=actor_id,
            entity_type="process_instance",
            entity_id=str(instance.id),
            payload=payload,
        )
        self.db.add(event)

    def _find_start_node(self, graph: dict) -> dict | None:
        nodes = graph.get("nodes", [])
        for node in nodes:
            engine_type = node.get("data", {}).get("engineType", "")
            if engine_type in ("ManualStart", "FormSubmitTrigger", "APITrigger", "Start"):
                return node
        return nodes[0] if nodes else None

    def _find_node_by_id(self, graph: dict, node_id: str) -> dict | None:
        for node in graph.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None

    def _get_next_node(self, node: dict, graph: dict, variables: dict) -> dict | None:
        edges = graph.get("edges", [])
        for edge in edges:
            if edge.get("source") == node["id"]:
                next_node = self._find_node_by_id(graph, edge.get("target", ""))
                if next_node:
                    return next_node
        return None

    def _get_next_node_by_handle(self, node: dict, graph: dict, handle_id: str, variables: dict) -> dict | None:
        edges = graph.get("edges", [])
        for edge in edges:
            if edge.get("source") == node["id"] and (
                edge.get("sourceHandle") == handle_id or
                edge.get("label") == handle_id or
                handle_id in str(edge.get("sourceHandle", ""))
            ):
                return self._find_node_by_id(graph, edge.get("target", ""))
        return None

    def _get_all_next_nodes(self, node: dict, graph: dict) -> list[dict]:
        edges = graph.get("edges", [])
        result = []
        for edge in edges:
            if edge.get("source") == node["id"]:
                n = self._find_node_by_id(graph, edge.get("target", ""))
                if n:
                    result.append(n)
        return result

    def _set_nested(self, d: dict, key: str, value: Any):
        parts = key.split(".")
        current = d
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
