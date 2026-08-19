"""Conversations, messages, lawyers, feedback.

Revision ID: 0002_conversations_lawyers
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_conversations_lawyers"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("legal_domain", sa.String(64)),
        sa.Column("state_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("conversation_id", sa.String(64), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_table(
        "lawyers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("specialization", sa.String(100), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=False),
        sa.Column("state", sa.String(80)),
        sa.Column("district", sa.String(80)),
        sa.Column("languages", sa.JSON, nullable=False),
        sa.Column("years_experience", sa.Integer, nullable=False),
        sa.Column("fee_min", sa.Integer),
        sa.Column("fee_max", sa.Integer),
        sa.Column("legal_aid", sa.Boolean, nullable=False),
        sa.Column("pro_bono", sa.Boolean, nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False),
        sa.Column("contact", sa.String(200)),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("conversation_id", sa.String(64)),
        sa.Column("rating", sa.Integer),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table("feedback")
    op.drop_table("lawyers")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
