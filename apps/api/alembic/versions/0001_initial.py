"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-12
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Tables are also created at app startup for MVP ergonomics.
    pass


def downgrade() -> None:
    pass
