"""household contact optional

Revision ID: b2677a8ecb66
Revises: dc12f28c2e06
Create Date: 2026-09-29 14:50:36.114378

Not every household has a reachable phone number. Requiring one made household
creation and CSV/GeoJSON import fail with an opaque NOT NULL constraint error.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2677a8ecb66"
down_revision: str | None = "dc12f28c2e06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite cannot ALTER a column in place; batch mode rebuilds the table.
    with op.batch_alter_table("households") as batch_op:
        batch_op.alter_column("contact", existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("households") as batch_op:
        batch_op.alter_column("contact", existing_type=sa.VARCHAR(), nullable=False)
