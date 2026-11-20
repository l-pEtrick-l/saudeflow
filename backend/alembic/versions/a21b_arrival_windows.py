"""Optional arrival windows; existing requests remain unchanged."""
from alembic import op
import sqlalchemy as sa

revision = "a21b_arrival_windows"
down_revision = "41793deadc80"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("care_requests", sa.Column("arrival_window_start", sa.DateTime(timezone=True)))
    op.add_column("care_requests", sa.Column("arrival_window_end", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_column("care_requests", "arrival_window_end")
    op.drop_column("care_requests", "arrival_window_start")
