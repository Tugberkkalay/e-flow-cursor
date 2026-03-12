from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.expression import context_schema_from_sample, resolve_template
from app.legacy import adapt_legacy_node
from app.models import (
    ApprovalInstance,
    ApprovalLimit,
    AuditEvent,
    Delegation,
    Document,
    NodeInstance,
    ProcessInstance,
    ProcessVersion,
    TaskInstance,
    User,
    utcnow,
)
from app.templates import default_context_sample

settings = get_settings()


def append_audit(
    db: Session,
    *,
    org_id: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    actor_user_id: str | None = None,
    process_instance_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        org_id=org_id,
        actor_user_id=actor_user_id,
        process_instance_id=process_instance_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        payload_json=payload or {},
    )
    db.add(event)
    db.flush()
    return event


def build_context(instance: ProcessInstance, actor: User | None = None) -> dict[str, Any]:
    variables = dict(instance.variables_json or {})
    variables.setdefault("form", {})
    variables.setdefault("docs", {})
    variables.setdefault("extract", {})
    variables.setdefault("selection", {})
    variables.setdefault("approval", {})
    variables.setdefault("gen", {})
    variables.setdefault("calc", {})
    variables.setdefault("flags", {})
    system = variables.setdefault("system", {})
    system.setdefault("instance_id", instance.id)
    system["now"] = datetime.now(UTC).isoformat()
    if actor:
        system["actor"] = {
            "id": actor.id,
            "name": actor.full_name,
            "email": actor.email,
            "role": actor.role,
        }
    return variables


def graph_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["id"]: adapt_legacy_node(node) for node in graph.get("nodes", [])}


def outgoing_edges(graph: dict[str, Any], node_id: str) -> list[dict[str, Any]]:
    return [edge for edge in graph.get("edges", []) if edge["source"] == node_id]


def incoming_edges(graph: dict[str, Any], node_id: str) -> list[dict[str, Any]]:
    return [edge for edge in graph.get("edges", []) if edge["target"] == node_id]


def get_start_node(graph: dict[str, Any]) -> dict[str, Any]:
    for node in graph.get("nodes", []):
        if node.get("config", {}).get("start"):
            return node
    for node in graph.get("nodes", []):
        if not incoming_edges(graph, node["id"]):
            return node
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Flow has no start node")


def choose_next_nodes(graph: dict[str, Any], node_id: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    next_nodes: list[dict[str, Any]] = []
    nodes = graph_nodes(graph)
    for edge in outgoing_edges(graph, node_id):
        condition = edge.get("condition")
        if condition is None or bool(resolve_template(condition, context)):
            next_nodes.append(nodes[edge["target"]])
    return next_nodes


def first_pending_runtime_node(instance: ProcessInstance) -> str | None:
    runtime = instance.variables_json.setdefault("_runtime", {})
    pending_nodes = runtime.setdefault("pending_nodes", [])
    if instance.current_node_id:
        return instance.current_node_id
    if pending_nodes:
        return pending_nodes.pop(0)
    return None


def _apply_parallel_pending(instance: ProcessInstance, next_nodes: list[dict[str, Any]]) -> str | None:
    runtime = instance.variables_json.setdefault("_runtime", {})
    pending_nodes = runtime.setdefault("pending_nodes", [])
    if not next_nodes:
        return None
    if len(next_nodes) > 1:
        pending_nodes.extend(node["id"] for node in next_nodes[1:])
    return next_nodes[0]["id"]


def _resolve_delegation(db: Session, user_id: str | None, role: str | None) -> tuple[str | None, dict[str, Any]]:
    if not user_id:
        return None, {}
    today = date.today()
    delegations = db.scalars(
        select(Delegation).where(
            Delegation.delegator_id == user_id,
            Delegation.is_active.is_(True),
            Delegation.start_date <= today,
            Delegation.end_date >= today,
        )
    ).all()
    delegation = next((item for item in delegations if not item.role_scope or role in item.role_scope), None)
    if delegation:
        return delegation.delegate_id, {"delegated_from": user_id, "delegation_id": delegation.id}
    return user_id, {}


def _find_user_for_assignment(db: Session, *, role: str | None, department: str | None) -> User | None:
    stmt = select(User).where(User.org_id == settings.org_id, User.is_active.is_(True))
    if department:
        stmt = stmt.where(User.department == department)
    if role:
        stmt = stmt.where(User.role == role)
    return db.scalar(stmt.order_by(User.created_at))


def _resolve_limit_matrix(db: Session, context: dict[str, Any]) -> tuple[str | None, str | None]:
    department = context["form"].get("department") or "Operations"
    budget_type = context["form"].get("budget_type") or "default"
    currency = context["form"].get("currency") or "TRY"
    amount = float(context["calc"].get("total_amount") or context["form"].get("total_amount") or 0)
    limit = db.scalar(
        select(ApprovalLimit).where(
            ApprovalLimit.org_id == settings.org_id,
            ApprovalLimit.department == department,
            ApprovalLimit.budget_type == budget_type,
            ApprovalLimit.currency == currency,
            ApprovalLimit.min_amount <= amount,
            ApprovalLimit.max_amount >= amount,
        )
    )
    if limit is None:
        limit = db.scalar(select(ApprovalLimit).order_by(ApprovalLimit.min_amount))
    return (limit.approver_user_id if limit else None, limit.approver_role if limit else None)


def _create_task(db: Session, instance: ProcessInstance, node_instance: NodeInstance, node: dict[str, Any], actor: User | None) -> TaskInstance:
    config = node.get("config", {})
    target_department = config.get("target_department")
    assignee_role = config.get("assignee_role")
    if node.get("preset") == "vendor_selection" and not target_department:
        target_department = "Procurement"
    assignee_user = _find_user_for_assignment(db, role=assignee_role, department=target_department)
    assignee_user_id = config.get("assignee_user_id") or (assignee_user.id if assignee_user else actor.id if actor else None)
    assignee_user_id, delegation_meta = _resolve_delegation(db, assignee_user_id, assignee_role)

    task = TaskInstance(
        org_id=instance.org_id,
        process_instance_id=instance.id,
        node_instance_id=node_instance.id,
        node_id=node["id"],
        title=node["label"],
        assignee_user_id=assignee_user_id,
        assignee_role=assignee_role,
        payload_json={**config, **delegation_meta},
    )
    db.add(task)
    db.flush()
    node_instance.status = "waiting"
    instance.status = "waiting_task"
    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="task",
        entity_id=task.id,
        event_type="task.created",
        actor_user_id=actor.id if actor else None,
        process_instance_id=instance.id,
        payload={"node_id": node["id"], "assignee_user_id": assignee_user_id},
    )
    return task


def _create_approval(db: Session, instance: ProcessInstance, node_instance: NodeInstance, node: dict[str, Any], actor: User | None) -> ApprovalInstance:
    config = node.get("config", {})
    approver_user_id = config.get("approver_user_id")
    approver_role = config.get("assignee_role")

    if config.get("strategy") == "limit_matrix":
        approver_user_id, approver_role = _resolve_limit_matrix(db, build_context(instance, actor))
    elif config.get("target_department"):
        user = _find_user_for_assignment(db, role=approver_role, department=config["target_department"])
        approver_user_id = user.id if user else approver_user_id

    approver_user_id, delegation_meta = _resolve_delegation(db, approver_user_id, approver_role)
    approval = ApprovalInstance(
        org_id=instance.org_id,
        process_instance_id=instance.id,
        node_instance_id=node_instance.id,
        node_id=node["id"],
        approver_user_id=approver_user_id,
        approver_role=approver_role,
        limit_bucket=approver_role,
        payload_json={**config, **delegation_meta},
    )
    db.add(approval)
    db.flush()
    node_instance.status = "waiting"
    instance.status = "waiting_approval"
    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="approval",
        entity_id=approval.id,
        event_type="approval.created",
        actor_user_id=actor.id if actor else None,
        process_instance_id=instance.id,
        payload={"node_id": node["id"], "approver_user_id": approver_user_id, "approver_role": approver_role},
    )
    return approval


def _document_extract_stub(document: Document) -> dict[str, Any]:
    base_name = Path(document.file_name).stem.lower()
    return {
        "source_file": document.file_name,
        "supplier_vkn": "1234567890",
        "amount": 12500 if "invoice" in base_name else 50000,
        "contract_dates": {"start": "2026-01-01", "end": "2026-12-31"},
    }


def upload_document(
    db: Session,
    *,
    instance: ProcessInstance,
    actor: User,
    file: UploadFile,
    document_type: str,
    metadata: dict[str, Any] | None = None,
) -> Document:
    storage_root = Path(settings.storage_dir)
    storage_root.mkdir(parents=True, exist_ok=True)
    instance_dir = storage_root / instance.id
    instance_dir.mkdir(parents=True, exist_ok=True)
    existing_version = db.scalar(
        select(Document)
        .where(Document.process_instance_id == instance.id, Document.document_type == document_type)
        .order_by(Document.version.desc())
    )
    version = (existing_version.version + 1) if existing_version else 1
    file_name = file.filename or f"{document_type}-{version}.bin"
    storage_path = instance_dir / f"v{version}-{file_name}"
    file_bytes = file.file.read()
    storage_path.write_bytes(file_bytes)

    document = Document(
        org_id=instance.org_id,
        process_instance_id=instance.id,
        document_type=document_type,
        version=version,
        file_name=file_name,
        storage_path=str(storage_path),
        extracted_json=_document_extract_stub(
            Document(
                org_id=instance.org_id,
                process_instance_id=instance.id,
                document_type=document_type,
                version=version,
                file_name=file_name,
                storage_path=str(storage_path),
                created_by_id=actor.id,
            )
        ),
        metadata_json=metadata or {},
        created_by_id=actor.id,
    )
    db.add(document)
    db.flush()
    docs = instance.variables_json.setdefault("docs", {})
    docs["latest"] = {"id": document.id, "file_name": file_name, "document_type": document_type, "version": version}
    docs[f"{document_type}_latest"] = document.extracted_json
    docs["offers_count"] = db.query(Document).filter(
        Document.process_instance_id == instance.id,
        Document.document_type == "offer",
    ).count()
    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="document",
        entity_id=document.id,
        event_type="document.uploaded",
        actor_user_id=actor.id,
        process_instance_id=instance.id,
        payload={"document_type": document_type, "version": version, "file_name": file_name},
    )
    return document


def _execute_service_action(db: Session, instance: ProcessInstance, node: dict[str, Any], actor: User | None) -> dict[str, Any]:
    context = build_context(instance, actor)
    action = node.get("config", {}).get("action")
    result: dict[str, Any] = {"action": action, "status": "ok"}

    if action == "calculate_pr_totals":
        line_items = context["form"].get("line_items") or []
        subtotal = 0.0
        for item in line_items:
            quantity = float(item.get("quantity") or 1)
            unit_price = float(item.get("unit_price") or item.get("amount") or 0)
            amount = float(item.get("amount") or quantity * unit_price)
            item["amount"] = amount
            subtotal += amount
        vat_rate = float(context["form"].get("vat_rate") or 0)
        vat_amount = subtotal * vat_rate / 100
        total = subtotal + vat_amount
        context["calc"].update({"subtotal": subtotal, "vat_amount": vat_amount, "total_amount": total})
        context["form"]["subtotal"] = subtotal
        context["form"]["total_amount"] = total
        result["calc"] = context["calc"]
    elif action == "extract_offers":
        docs = db.scalars(
            select(Document).where(Document.process_instance_id == instance.id, Document.document_type == "offer").order_by(Document.created_at)
        ).all()
        extracted = [
            {
                "supplier": f"Supplier {index + 1}",
                "supplier_vkn": "1234567890",
                "amount": doc.extracted_json.get("amount", 10000 + (index * 5000)),
                "document_id": doc.id,
            }
            for index, doc in enumerate(docs)
        ]
        context["extract"]["offers"] = extracted
        context["docs"]["offers_count"] = len(docs)
        result["offers_count"] = len(docs)
    elif action == "normalize_offers":
        offers = context["extract"].get("offers", [])
        context["selection"]["normalized_offers"] = sorted(offers, key=lambda item: item.get("amount", 0))
        context["docs"]["offers_count"] = len(offers)
        result["normalized"] = len(offers)
    elif action == "policy_check":
        flags = []
        if (context["calc"].get("total_amount") or 0) >= 50000 and (context["docs"].get("offers_count") or 0) < 2:
            flags.append("offers_below_policy")
        if context["form"].get("request_type") == "Abonelik":
            flags.append("subscription_review")
        context["flags"]["policy_flags"] = flags
        result["flags"] = flags
    elif action == "generate_po_number":
        po_no = f"PO-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        context["gen"]["po_no"] = po_no
        result["po_no"] = po_no
    elif action == "mock_http":
        endpoint = node.get("config", {}).get("endpoint", "mock://service")
        response = {"endpoint": endpoint, "status": 200, "message": "Mock integration executed"}
        context["gen"]["http_response"] = response
        result["response"] = response
    elif action == "mock_email":
        context["gen"]["email_status"] = "sent"
        result["email_status"] = "sent"
    elif action == "extract_contract":
        latest_contract = db.scalar(
            select(Document)
            .where(Document.process_instance_id == instance.id, Document.document_type.in_(["contract_draft", "contract_revision"]))
            .order_by(Document.version.desc())
        )
        if latest_contract:
            context["extract"]["contract_amount"] = latest_contract.extracted_json.get("amount", 250000)
            context["extract"]["contract_dates"] = latest_contract.extracted_json.get("contract_dates", {})
        result["contract"] = context["extract"]
    elif action == "signature_stub":
        signed_url = f"https://storage.local/{instance.id}/signed-contract.pdf"
        context["gen"]["signed_url"] = signed_url
        result["signed_url"] = signed_url
    elif action == "archive_stub":
        context["gen"]["archive_status"] = "archived"
        result["archive_status"] = "archived"
    elif action == "extract_invoice":
        latest_invoice = db.scalar(
            select(Document)
            .where(Document.process_instance_id == instance.id, Document.document_type == "invoice")
            .order_by(Document.version.desc())
        )
        if latest_invoice:
            context["extract"]["invoice"] = latest_invoice.extracted_json
            context["extract"]["supplier_vkn"] = latest_invoice.extracted_json.get("supplier_vkn")
            context["form"]["invoice_amount"] = latest_invoice.extracted_json.get("amount")
        result["invoice"] = context["extract"].get("invoice", {})
    elif action == "match_invoice":
        invoice_amount = float(context["form"].get("invoice_amount") or context["extract"].get("invoice", {}).get("amount") or 0)
        expected_amount = float(
            context["selection"].get("expected_amount")
            or context["calc"].get("total_amount")
            or context["form"].get("expected_amount")
            or invoice_amount
        )
        tolerance = max(expected_amount * 0.05, 100)
        supplier_vkn = context["extract"].get("supplier_vkn") or context["form"].get("supplier_vkn")
        expected_vkn = context["selection"].get("supplier_vkn") or supplier_vkn
        status_value = "matched" if abs(invoice_amount - expected_amount) <= tolerance and supplier_vkn == expected_vkn else "mismatch"
        context["selection"]["match_status"] = status_value
        context["flags"]["mismatch_flags"] = [] if status_value == "matched" else ["amount_or_supplier_mismatch"]
        result["match_status"] = status_value
    elif action == "mock_payment":
        context["gen"]["payment_status"] = "submitted"
        result["payment_status"] = "submitted"
    elif action == "subprocess_stub":
        config = node.get("config", {})
        inputs = {
            key: resolve_template(expr, context)
            for key, expr in (config.get("input_mapping") or {}).items()
        }
        context["gen"]["subprocess_call"] = {"status": "stubbed", "inputs": inputs}
        outputs = config.get("output_mapping") or {}
        for output_key, expr in outputs.items():
            context["gen"][output_key] = resolve_template(expr, context)
        result["subprocess"] = context["gen"]["subprocess_call"]
    else:
        result["note"] = "No-op service action"

    instance.variables_json = context
    return result


def _complete_auto_node(
    db: Session,
    instance: ProcessInstance,
    version: ProcessVersion,
    node: dict[str, Any],
    node_instance: NodeInstance,
    actor: User | None,
) -> None:
    primitive = node["primitive"]
    context = build_context(instance, actor)

    if primitive == "ServiceTask" or primitive == "ScriptTask" or primitive == "SubprocessCall":
        node_instance.output_json = _execute_service_action(db, instance, node, actor)
        node_instance.status = "completed"
    elif primitive == "Gateway":
        node_instance.output_json = {"evaluated": True}
        node_instance.status = "completed"
    elif primitive == "Event":
        if node.get("config", {}).get("kind") == "timer":
            context["gen"]["timer_status"] = "scheduled"
            node_instance.output_json = {"timer_status": "scheduled"}
            node_instance.status = "completed"
        else:
            node_instance.output_json = {"event": "triggered"}
            node_instance.status = "completed"
    elif primitive == "End":
        exports = {
            key: resolve_template(expr, context)
            for key, expr in (node.get("config", {}).get("mappings") or {}).items()
        }
        instance.exports_json = exports
        instance.status = node.get("config", {}).get("status", "completed")
        instance.current_node_id = None
        instance.completed_at = utcnow()
        node_instance.output_json = exports
        node_instance.status = "completed"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported auto node primitive '{primitive}'")

    node_instance.completed_at = utcnow()
    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="node",
        entity_id=node_instance.id,
        event_type="node.completed",
        actor_user_id=actor.id if actor else None,
        process_instance_id=instance.id,
        payload={"node_id": node["id"], "primitive": primitive, "output": node_instance.output_json},
    )

    if primitive != "End":
        context = build_context(instance, actor)
        next_nodes = choose_next_nodes(version.graph_json, node["id"], context)
        instance.current_node_id = _apply_parallel_pending(instance, next_nodes)
        if instance.current_node_id is None:
            instance.status = "completed"
            instance.completed_at = utcnow()


def execute_ready_path(db: Session, instance: ProcessInstance, actor: User | None = None) -> ProcessInstance:
    version = db.get(ProcessVersion, instance.version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Process version not found")
    nodes = graph_nodes(version.graph_json)

    while True:
        current_node_id = first_pending_runtime_node(instance)
        instance.current_node_id = current_node_id
        if current_node_id is None:
            break
        node = nodes[current_node_id]
        node_instance = NodeInstance(
            org_id=instance.org_id,
            process_instance_id=instance.id,
            node_id=node["id"],
            node_type=node["preset"],
            node_version=node.get("version", 1),
            input_json=build_context(instance, actor),
        )
        db.add(node_instance)
        db.flush()
        append_audit(
            db,
            org_id=instance.org_id,
            entity_type="node",
            entity_id=node_instance.id,
            event_type="node.started",
            actor_user_id=actor.id if actor else None,
            process_instance_id=instance.id,
            payload={"node_id": node["id"], "primitive": node["primitive"]},
        )

        if node["primitive"] == "HumanTask":
            _create_task(db, instance, node_instance, node, actor)
            break
        if node["primitive"] == "ApprovalTask":
            _create_approval(db, instance, node_instance, node, actor)
            break

        try:
            _complete_auto_node(db, instance, version, node, node_instance, actor)
            if node["primitive"] == "End" or instance.status in {"completed", "rejected", "cancelled"} and instance.current_node_id is None:
                break
        except Exception as exc:  # pragma: no cover - defensive branch
            node_instance.status = "error"
            node_instance.error_message = str(exc)
            node_instance.completed_at = utcnow()
            instance.status = "error"
            append_audit(
                db,
                org_id=instance.org_id,
                entity_type="node",
                entity_id=node_instance.id,
                event_type="node.failed",
                actor_user_id=actor.id if actor else None,
                process_instance_id=instance.id,
                payload={"node_id": node["id"], "error": str(exc)},
            )
            raise

    db.flush()
    return instance


def start_instance(
    db: Session,
    *,
    version: ProcessVersion,
    definition_name: str,
    actor: User,
    initial_inputs: dict[str, Any] | None = None,
) -> ProcessInstance:
    graph = version.graph_json
    start = get_start_node(graph)
    form_inputs = initial_inputs or {}
    title = (
        form_inputs.get("request_title")
        or form_inputs.get("invoice_no")
        or form_inputs.get("contract_title")
        or definition_name
    )
    instance = ProcessInstance(
        org_id=actor.org_id,
        definition_id=version.definition_id,
        version_id=version.id,
        title=title,
        status="running",
        current_node_id=start["id"],
        variables_json={
            "form": form_inputs,
            "docs": {"offers_count": 0},
            "extract": {},
            "selection": {},
            "approval": {},
            "gen": {},
            "calc": {},
            "flags": {},
            "system": {
                "requester": {"id": actor.id, "name": actor.full_name, "email": actor.email},
                "roles": [actor.role],
                "org": {"id": actor.org_id},
                "instance_id": "pending",
            },
            "_runtime": {"pending_nodes": []},
        },
        exports_json={},
        started_by_id=actor.id,
    )
    db.add(instance)
    db.flush()
    instance.variables_json["system"]["instance_id"] = instance.id
    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="instance",
        entity_id=instance.id,
        event_type="instance.started",
        actor_user_id=actor.id,
        process_instance_id=instance.id,
        payload={"version_id": version.id, "definition": definition_name},
    )
    execute_ready_path(db, instance, actor)
    db.commit()
    db.refresh(instance)
    return instance


def complete_task(
    db: Session,
    *,
    task: TaskInstance,
    actor: User,
    payload: dict[str, Any] | None = None,
    outcome: str | None = None,
    comment: str | None = None,
) -> ProcessInstance:
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task is not pending")
    node_instance = db.get(NodeInstance, task.node_instance_id)
    instance = db.get(ProcessInstance, task.process_instance_id)
    version = db.get(ProcessVersion, instance.version_id) if instance else None
    if not node_instance or not instance or not version:
        raise HTTPException(status_code=404, detail="Task runtime context not found")

    nodes = graph_nodes(version.graph_json)
    node = nodes[task.node_id]
    context = build_context(instance, actor)
    namespace = node.get("config", {}).get("outcome_namespace") or "form"
    namespace_payload = payload or {}
    context.setdefault(namespace, {})
    if namespace == "form":
        context["form"].update(namespace_payload)
    else:
        if isinstance(context[namespace], dict):
            context[namespace].update(namespace_payload)
        else:
            context[namespace] = namespace_payload

    if node.get("preset") == "document_upload":
        context["docs"]["last_upload_status"] = outcome or "uploaded"
        if namespace_payload.get("offers_count"):
            context["docs"]["offers_count"] = namespace_payload["offers_count"]
    if node.get("preset") == "vendor_selection":
        context["selection"].setdefault("supplier_vkn", namespace_payload.get("supplier_vkn", "1234567890"))
    if node.get("preset") == "review_comment":
        context["flags"]["dispute_outcome"] = outcome or "reject"
    if node.get("preset") == "delivery_acceptance":
        context["selection"]["delivery_status"] = outcome or "accepted"

    context["system"]["last_outcome"] = outcome or "completed"
    instance.variables_json = context
    task.status = "completed"
    task.outcome = outcome or "completed"
    task.comments = comment
    task.payload_json = payload or {}
    task.completed_at = utcnow()
    node_instance.status = "completed"
    node_instance.output_json = {"outcome": task.outcome, "payload": task.payload_json}
    node_instance.completed_at = utcnow()
    instance.status = "running"

    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="task",
        entity_id=task.id,
        event_type="task.completed",
        actor_user_id=actor.id,
        process_instance_id=instance.id,
        payload={"outcome": task.outcome, "node_id": task.node_id},
    )

    next_nodes = choose_next_nodes(version.graph_json, task.node_id, build_context(instance, actor))
    instance.current_node_id = _apply_parallel_pending(instance, next_nodes)
    execute_ready_path(db, instance, actor)
    db.commit()
    db.refresh(instance)
    return instance


def decide_approval(
    db: Session,
    *,
    approval: ApprovalInstance,
    actor: User,
    decision: str,
    comment: str | None = None,
) -> ProcessInstance:
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is not pending")
    node_instance = db.get(NodeInstance, approval.node_instance_id)
    instance = db.get(ProcessInstance, approval.process_instance_id)
    version = db.get(ProcessVersion, instance.version_id) if instance else None
    if not node_instance or not instance or not version:
        raise HTTPException(status_code=404, detail="Approval runtime context not found")

    context = build_context(instance, actor)
    context["approval"]["decision"] = decision
    context["approval"]["summary"] = f"{actor.full_name} -> {decision}"
    instance.variables_json = context
    approval.status = "decided"
    approval.decision = decision
    approval.comments = comment
    approval.decided_at = utcnow()
    node_instance.status = "completed"
    node_instance.output_json = {"decision": decision, "comment": comment}
    node_instance.completed_at = utcnow()
    instance.status = "running"

    append_audit(
        db,
        org_id=instance.org_id,
        entity_type="approval",
        entity_id=approval.id,
        event_type="approval.decided",
        actor_user_id=actor.id,
        process_instance_id=instance.id,
        payload={"decision": decision, "node_id": approval.node_id},
    )

    next_nodes = choose_next_nodes(version.graph_json, approval.node_id, build_context(instance, actor))
    instance.current_node_id = _apply_parallel_pending(instance, next_nodes)
    execute_ready_path(db, instance, actor)
    db.commit()
    db.refresh(instance)
    return instance


def instance_context_schema() -> dict[str, Any]:
    return context_schema_from_sample(default_context_sample())
