"""Initial schema.

Tables are created from the SQLAlchemy metadata so the migration and the
application models stay on one definition for this first revision.
"""

from __future__ import annotations

from alembic import op

from app.models import Base

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
