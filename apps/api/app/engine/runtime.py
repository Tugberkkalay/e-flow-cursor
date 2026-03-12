"""BPM Runtime Engine - Lazy step-by-step execution."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import (
    ProcessInstance, ProcessVersion, NodeInstance, TaskInstance,
    ApprovalInstance, AuditEvent, ApprovalLimit, User, Document,
)
from app.engine.expressions import resolve, resolve_deep, safe_eval


class BPMRuntime:
    """Lazy execution engine: processes one node at a time, computing next node at runtime."""

    def __init__(self, db: Session):
        self.db = db

    def start_instance(
        self,
        flow_id: str,
        version_id: str,
        requester_id: str,
        initial_inputs: dict | None = None,
    ) -> ProcessInstance:
        version = self.db.query(ProcessVersion).get(version_id)
        if not version:
            raise ValueError("Version not found")

        graph = version.graph_json
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        start_node = self._find_start_node(nodes)
        if not start_node:
            raise ValueError("No start node found in flow")

        requester = self.db.query(User).get(requester_id)

        variables = {
            "form": initial_inputs or {},
            "docs": {},
            "extract": {},
            "selection": {},
            "approval": {},
            "gen": {},
            "calc": {},
            "flags": {},
            "system": {
                "requester_id": requester_id,
                "requester_name": requester.name if requester else "Unknown",
                "requester_email": requester.email if requester else "",
                "instance_id": "",
                "now": datetime.utcnow().isoformat(),
                "org_id": requester.org_id if requester else "org_1",
                "year": str(datetime.utcnow().year),
                "seq": str(uuid.uuid4().hex[:6].upper()),
            },
        }

        instance = ProcessInstance(
            id=str(uuid.uuid4()),
            flow_id=flow_id,
            flow_name=version.definition.name if version.definition else None,
            version_id=version_id,
            status="running",
            variables=variables,
            current_node_id=start_node["id"],
            current_node_label=start_node["data"].get("label", "Start"),
            requester_id=requester_id,
            requester_name=requester.name if requester else "Unknown",
            org_id=requester.org_id if requester else "org_1",
        )
        variables["system"]["instance_id"] = instance.id
        instance.variables = variables

        self.db.add(instance)
        self._emit_audit(instance.id, requester_id, "instance_started", {
            "flow_id": flow_id, "version_id": version_id
        })

        self._execute_node(instance, graph, start_node)
        self.db.commit()

        return instance

    def advance_instance(self, instance: ProcessInstance) -> ProcessInstance:
        """Advance instance to next step (lazy evaluation)."""
        version = self.db.query(ProcessVersion).get(instance.version_id)
        graph = version.graph_json
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        current_node = self._find_node(nodes, instance.current_node_id)
        if not current_node:
            return instance

        next_node = self._compute_next_node(instance, graph, current_node)
        if next_node:
            self._execute_node(instance, graph, next_node)

        self.db.commit()
        return instance

    def complete_task(self, task: TaskInstance, form_data: dict | None = None) -> ProcessInstance:
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        if form_data:
            task.form_data = form_data

        instance = self.db.query(ProcessInstance).get(task.instance_id)
        node_inst = self.db.query(NodeInstance).get(task.node_instance_id)

        if form_data:
            variables = dict(instance.variables)
            variables["form"].update(form_data)
            instance.variables = variables

        node_inst.status = "completed"
        node_inst.completed_at = datetime.utcnow()
        node_inst.output_data = form_data

        self._emit_audit(instance.id, task.assignee_id, "task_completed", {
            "task_id": task.id, "task_type": task.task_type
        })

        instance = self.advance_instance(instance)
        return instance

    def decide_approval(self, approval: ApprovalInstance, decision: str, comment: str = None) -> ProcessInstance:
        approval.decision = decision
        approval.comment = comment
        approval.decided_at = datetime.utcnow()

        instance = self.db.query(ProcessInstance).get(approval.instance_id)
        node_inst = self.db.query(NodeInstance).get(approval.node_instance_id)

        variables = dict(instance.variables)
        variables["approval"] = {
            "decision": decision,
            "comment": comment,
            "approver_id": approval.approver_id,
            "approver_name": approval.approver_name,
            "amount": approval.amount,
        }
        instance.variables = variables

        node_inst.status = "completed"
        node_inst.completed_at = datetime.utcnow()
        node_inst.output_data = {"decision": decision}

        self._emit_audit(instance.id, approval.approver_id, "approval_decided", {
            "decision": decision, "comment": comment, "amount": approval.amount
        })

        instance = self.advance_instance(instance)
        return instance

    def retry_node(self, instance: ProcessInstance, node_id: str) -> ProcessInstance:
        version = self.db.query(ProcessVersion).get(instance.version_id)
        graph = version.graph_json
        node = self._find_node(graph.get("nodes", []), node_id)
        if node:
            instance.current_node_id = node_id
            self._execute_node(instance, graph, node)
            self.db.commit()
        return instance

    def skip_node(self, instance: ProcessInstance) -> ProcessInstance:
        """Admin action: skip current node."""
        version = self.db.query(ProcessVersion).get(instance.version_id)
        graph = version.graph_json
        current = self._find_node(graph["nodes"], instance.current_node_id)

        pending_node_insts = self.db.query(NodeInstance).filter(
            NodeInstance.instance_id == instance.id,
            NodeInstance.node_id == instance.current_node_id,
            NodeInstance.status.in_(["pending", "running"])
        ).all()
        for ni in pending_node_insts:
            ni.status = "skipped"

        self._emit_audit(instance.id, None, "node_skipped", {"node_id": instance.current_node_id})

        next_node = self._compute_next_node(instance, graph, current, force_default=True)
        if next_node:
            self._execute_node(instance, graph, next_node)
        self.db.commit()
        return instance

    def cancel_instance(self, instance: ProcessInstance, user_id: str) -> ProcessInstance:
        instance.status = "cancelled"
        instance.completed_at = datetime.utcnow()
        self._emit_audit(instance.id, user_id, "instance_cancelled", {})
        self.db.commit()
        return instance

    def _execute_node(self, instance: ProcessInstance, graph: dict, node: dict):
        """Execute a single node. May auto-advance for non-blocking nodes."""
        node_data = node["data"]
        engine_type = node_data.get("engineType", "")
        node_type = node_data.get("nodeType", "")
        config = node_data.get("config", {})

        instance.current_node_id = node["id"]
        instance.current_node_label = node_data.get("label", "")

        node_inst = NodeInstance(
            id=str(uuid.uuid4()),
            instance_id=instance.id,
            node_id=node["id"],
            node_type=node_type,
            node_label=node_data.get("label"),
            status="running",
            started_at=datetime.utcnow(),
            input_data=config,
            org_id=instance.org_id,
        )
        self.db.add(node_inst)

        self._emit_audit(instance.id, None, "node_started", {
            "node_id": node["id"], "node_type": node_type, "label": node_data.get("label")
        })

        if engine_type == "Event" and node_type in ("manual_start", "form_submit", "api_trigger", "scheduled_trigger"):
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()
            next_node = self._compute_next_node(instance, graph, node)
            if next_node:
                self._execute_node(instance, graph, next_node)

        elif engine_type == "Gateway":
            result = self._evaluate_gateway(instance, node, config)
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()
            node_inst.output_data = {"result": str(result)}

            self._emit_audit(instance.id, None, "gateway_evaluated", {
                "node_id": node["id"], "result": str(result)
            })

            next_node = self._compute_next_node(instance, graph, node, gateway_result=result)
            if next_node:
                self._execute_node(instance, graph, next_node)

        elif engine_type == "ScriptTask":
            output = self._execute_script(instance, node, config)
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()
            node_inst.output_data = output

            next_node = self._compute_next_node(instance, graph, node)
            if next_node:
                self._execute_node(instance, graph, next_node)

        elif engine_type == "ServiceTask":
            output = self._execute_service(instance, node, config)
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()
            node_inst.output_data = output

            next_node = self._compute_next_node(instance, graph, node)
            if next_node:
                self._execute_node(instance, graph, next_node)

        elif engine_type == "HumanTask":
            task = TaskInstance(
                id=str(uuid.uuid4()),
                instance_id=instance.id,
                node_instance_id=node_inst.id,
                task_type=node_type,
                title=node_data.get("label", "Task"),
                description=node_data.get("description", ""),
                assignee_id=self._resolve_assignee(instance, config),
                assignee_name="",
                status="pending",
                flow_name=instance.flow_name,
                instance_title=f"{instance.flow_name}-{instance.id[:8]}",
                org_id=instance.org_id,
            )
            self.db.add(task)
            self._emit_audit(instance.id, None, "task_created", {
                "task_id": task.id, "task_type": node_type, "assignee": task.assignee_id
            })

        elif engine_type == "ApprovalTask":
            approver_id = self._resolve_approver(instance, config)
            approval = ApprovalInstance(
                id=str(uuid.uuid4()),
                instance_id=instance.id,
                node_instance_id=node_inst.id,
                approver_id=approver_id,
                approver_name="",
                amount=self._get_amount(instance, config),
                flow_name=instance.flow_name,
                instance_title=f"{instance.flow_name}-{instance.id[:8]}",
                org_id=instance.org_id,
            )
            self.db.add(approval)
            self._emit_audit(instance.id, None, "approval_requested", {
                "approval_id": approval.id, "approver": approver_id
            })

        elif engine_type == "End":
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()

            exports = config.get("exports", {})
            if exports:
                resolved = resolve_deep(exports, instance.variables)
                variables = dict(instance.variables)
                variables["exports"] = resolved
                instance.variables = variables
                node_inst.output_data = resolved

            instance.status = "completed"
            instance.completed_at = datetime.utcnow()
            self._emit_audit(instance.id, None, "instance_completed", {
                "exports": instance.variables.get("exports", {})
            })

        elif engine_type == "SubprocessCall":
            node_inst.status = "completed"
            node_inst.completed_at = datetime.utcnow()
            node_inst.output_data = {"stub": "subprocess_not_yet_implemented"}
            next_node = self._compute_next_node(instance, graph, node)
            if next_node:
                self._execute_node(instance, graph, next_node)

    def _evaluate_gateway(self, instance: ProcessInstance, node: dict, config: dict) -> str:
        """Evaluate gateway conditions. Returns handle name."""
        node_type = node["data"].get("nodeType", "")
        ctx = self._flat_context(instance.variables)

        if node_type == "if_condition":
            condition = config.get("condition", "")
            try:
                result = resolve(condition, ctx)
                return "true" if result else "false"
            except Exception:
                return "false"

        elif node_type == "switch":
            field = config.get("field", "")
            try:
                value = resolve(f"{{{{ {field} }}}}", ctx)
                return str(value) if value else "default"
            except Exception:
                return "default"

        return "default"

    def _execute_script(self, instance: ProcessInstance, node: dict, config: dict) -> dict:
        """Execute script/data nodes."""
        ctx = self._flat_context(instance.variables)
        node_type = node["data"].get("nodeType", "")
        output = {}

        if node_type == "calculate":
            expr = config.get("expression", "")
            if expr:
                result = resolve(expr, ctx)
                output["result"] = result
                variables = dict(instance.variables)
                variables["calc"]["total_amount"] = result
                instance.variables = variables

        elif node_type == "set_fields":
            mappings = config.get("mappings", [])
            variables = dict(instance.variables)
            for m in mappings:
                key = m.get("key", "")
                value = resolve(m.get("value", ""), ctx)
                parts = key.split(".")
                if len(parts) == 2 and parts[0] in variables:
                    variables[parts[0]][parts[1]] = value
                output[key] = value
            instance.variables = variables

        elif node_type == "normalize_money":
            variables = dict(instance.variables)
            variables["calc"]["currency_normalized"] = True
            instance.variables = variables
            output["normalized"] = True

        elif node_type == "policy_check":
            output["result"] = "pass"
            variables = dict(instance.variables)
            variables["flags"]["policy_check"] = "pass"
            instance.variables = variables

        elif node_type == "audit_emit":
            event_type = config.get("event_type", "custom_audit")
            self._emit_audit(instance.id, None, event_type, config.get("event_data_template", {}))
            output["emitted"] = True

        return output

    def _execute_service(self, instance: ProcessInstance, node: dict, config: dict) -> dict:
        """Execute service tasks (stubs for now)."""
        node_type = node["data"].get("nodeType", "")
        ctx = self._flat_context(instance.variables)
        output = {}

        if node_type == "http_request":
            url = resolve(config.get("url", ""), ctx)
            output = {"status": 200, "url": url, "response": {"ok": True, "message": "Mock response"}}

        elif node_type in ("ai_extract", "ocr_extract"):
            extract_type = config.get("extract_type", "generic")
            stub_data = self._stub_extraction(extract_type)
            output = stub_data
            variables = dict(instance.variables)
            variables["extract"].update(stub_data)
            instance.variables = variables

        elif node_type == "three_way_match":
            output = {"status": "matched", "confidence": 0.95, "mismatch_flags": []}
            variables = dict(instance.variables)
            variables["flags"]["match_status"] = "matched"
            instance.variables = variables

        elif node_type == "email_send":
            to = resolve(config.get("to", ""), ctx)
            output = {"sent": True, "to": to}

        elif node_type == "storage_node":
            output = {"stored": True, "key": f"docs/{instance.id}/{uuid.uuid4().hex[:8]}"}

        elif node_type == "document_classify":
            output = {"classification": "invoice", "confidence": 0.92}

        elif node_type == "erp_adapter":
            output = {"erp_response": {"status": "success", "ref": f"ERP-{uuid.uuid4().hex[:6].upper()}"}}

        return output

    def _stub_extraction(self, extract_type: str) -> dict:
        """Return stub extracted data based on type."""
        if extract_type == "offer":
            return {
                "vendor_name": "Stub Vendor A",
                "vendor_vkn": "1234567890",
                "amount": 150000,
                "currency": "TRY",
                "items": [{"desc": "Dizüstü Bilgisayar", "qty": 10, "unit_price": 15000}],
            }
        elif extract_type == "invoice":
            return {
                "invoice_no": f"INV-{uuid.uuid4().hex[:6].upper()}",
                "vendor_name": "Stub Vendor",
                "vendor_vkn": "1234567890",
                "amount": 156000,
                "currency": "TRY",
                "date": "2024-03-12",
            }
        elif extract_type == "contract":
            return {
                "contract_type": "Software License",
                "parties": ["e-Flow Corp", "Vendor X"],
                "contract_amount": 1200000,
                "currency": "TRY",
                "start_date": "2024-04-01",
                "contract_end_date": "2025-03-31",
                "dates": {"start": "2024-04-01", "end": "2025-03-31"},
            }
        return {"raw_text": "Stub extracted content", "fields": {}}

    def _compute_next_node(
        self, instance: ProcessInstance, graph: dict, current_node: dict,
        gateway_result: str = None, force_default: bool = False,
    ) -> dict | None:
        """Compute the next node based on edges from current node."""
        edges = graph.get("edges", [])
        nodes = graph.get("nodes", [])
        current_id = current_node["id"]

        outgoing = [e for e in edges if e["source"] == current_id]
        if not outgoing:
            return None

        if gateway_result and not force_default:
            for edge in outgoing:
                handle = edge.get("sourceHandle", "")
                if handle == gateway_result:
                    return self._find_node(nodes, edge["target"])
            for edge in outgoing:
                if not edge.get("sourceHandle"):
                    return self._find_node(nodes, edge["target"])

        if len(outgoing) == 1:
            return self._find_node(nodes, outgoing[0]["target"])

        for edge in outgoing:
            handle = edge.get("sourceHandle", "")
            if handle in ("default", ""):
                return self._find_node(nodes, edge["target"])

        return self._find_node(nodes, outgoing[0]["target"])

    def _find_start_node(self, nodes: list) -> dict | None:
        for node in nodes:
            ntype = node.get("data", {}).get("nodeType", "")
            if ntype in ("manual_start", "form_submit", "api_trigger", "scheduled_trigger"):
                return node
        return nodes[0] if nodes else None

    def _find_node(self, nodes: list, node_id: str) -> dict | None:
        for node in nodes:
            if node["id"] == node_id:
                return node
        return None

    def _resolve_assignee(self, instance: ProcessInstance, config: dict) -> str:
        assignee_type = config.get("assignee_type", "requester")
        if assignee_type == "requester":
            return instance.requester_id
        return instance.requester_id

    def _resolve_approver(self, instance: ProcessInstance, config: dict) -> str:
        approver_type = config.get("approver_type", "manager")
        if approver_type == "manager":
            requester = self.db.query(User).get(instance.requester_id)
            if requester and requester.manager_id:
                return requester.manager_id

        if approver_type == "limit_matrix":
            amount = self._get_amount(instance, config)
            limits = self.db.query(ApprovalLimit).filter(
                ApprovalLimit.org_id == instance.org_id,
                ApprovalLimit.min_amount <= amount,
                ApprovalLimit.max_amount >= amount,
            ).first()
            if limits:
                user = self.db.query(User).filter(
                    User.role == "approver",
                    User.org_id == instance.org_id,
                ).first()
                if user:
                    return user.id

        admin = self.db.query(User).filter(
            User.role == "admin",
            User.org_id == instance.org_id,
        ).first()
        return admin.id if admin else instance.requester_id

    def _get_amount(self, instance: ProcessInstance, config: dict) -> float:
        amount_field = config.get("amount_field", "form.total_amount")
        ctx = self._flat_context(instance.variables)
        try:
            return float(resolve(f"{{{{ {amount_field} }}}}", ctx) or 0)
        except (ValueError, TypeError):
            return 0

    def _flat_context(self, variables: dict) -> dict:
        """Return context suitable for expression resolution."""
        return variables

    def _emit_audit(self, instance_id: str, user_id: str | None, event_type: str, data: dict):
        user = self.db.query(User).get(user_id) if user_id else None
        event = AuditEvent(
            id=str(uuid.uuid4()),
            instance_id=instance_id,
            user_id=user_id,
            user_name=user.name if user else "Sistem",
            event_type=event_type,
            event_data=data,
            org_id="org_1",
        )
        self.db.add(event)
