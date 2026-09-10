"""initial schema: documents + files

Revision ID: 0001
Revises:
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("collection", sa.String(length=64), primary_key=True),
        sa.Column("id", sa.String(length=255), primary_key=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_documents_collection_user_id", "documents", ["collection", "user_id"]
    )

    op.create_table(
        "files",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("namespace", sa.String(length=64), nullable=False, server_default="files"),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("relative_path", sa.String(length=1000), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("files")
    op.drop_index("ix_documents_collection_user_id", table_name="documents")
    op.drop_table("documents")
