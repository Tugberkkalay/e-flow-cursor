from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ApprovalLimit, FormDefinition, ProcessDefinition, ProcessVersion, User
from app.security import hash_password
from app.templates import build_form_catalog, build_template_catalog

settings = get_settings()


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return

    users = [
        User(
            org_id=settings.org_id,
            email="admin@eflow.local",
            full_name="Aylin Admin",
            password_hash=hash_password("admin123"),
            role="admin",
            department="Operations",
            cost_center="OPS",
        ),
        User(
            org_id=settings.org_id,
            email="procurement@eflow.local",
            full_name="Bora Procurement",
            password_hash=hash_password("admin123"),
            role="approver",
            department="Procurement",
            cost_center="PROC",
        ),
        User(
            org_id=settings.org_id,
            email="finance@eflow.local",
            full_name="Cem Finance",
            password_hash=hash_password("admin123"),
            role="approver",
            department="Finance",
            cost_center="FIN",
        ),
        User(
            org_id=settings.org_id,
            email="legal@eflow.local",
            full_name="Defne Legal",
            password_hash=hash_password("admin123"),
            role="approver",
            department="Legal",
            cost_center="LEGAL",
        ),
    ]
    db.add_all(users)
    db.flush()

    for form in build_form_catalog():
        db.add(
            FormDefinition(
                org_id=settings.org_id,
                key=form["key"],
                name=form["name"],
                version=form["version"],
                status=form["status"],
                schema_json=form["schema_json"],
            )
        )

    procurement = _get_user_by_email(db, "procurement@eflow.local")
    finance = _get_user_by_email(db, "finance@eflow.local")
    admin = _get_user_by_email(db, "admin@eflow.local")

    approval_limits = [
        ApprovalLimit(
            org_id=settings.org_id,
            department="Operations",
            budget_type="default",
            currency="TRY",
            min_amount=0,
            max_amount=50000,
            approver_role="dept_manager",
            approver_user_id=procurement.id if procurement else None,
        ),
        ApprovalLimit(
            org_id=settings.org_id,
            department="Operations",
            budget_type="default",
            currency="TRY",
            min_amount=50000,
            max_amount=250000,
            approver_role="director",
            approver_user_id=finance.id if finance else None,
        ),
        ApprovalLimit(
            org_id=settings.org_id,
            department="Operations",
            budget_type="default",
            currency="TRY",
            min_amount=250000,
            max_amount=9_999_999_999,
            approver_role="cfo",
            approver_user_id=admin.id if admin else None,
        ),
    ]
    db.add_all(approval_limits)

    for template in build_template_catalog():
        definition = ProcessDefinition(
            org_id=settings.org_id,
            key=template["key"],
            name=template["name"],
            description=template["description"],
            status="published",
            latest_version=1,
            is_template=True,
            template_key=template["template_key"],
        )
        db.add(definition)
        db.flush()
        db.add(
            ProcessVersion(
                org_id=settings.org_id,
                definition_id=definition.id,
                version=1,
                status="published",
                graph_json=template["graph_json"],
                exported_outputs=template["graph_json"].get("exports", {}),
                legacy_adapter={"strategy": "compatibility_stub", "enabled": True},
            )
        )

    db.commit()
