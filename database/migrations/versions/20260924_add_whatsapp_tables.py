"""Add isolated Meta WhatsApp Cloud API tables.

Revision ID: 20260924_add_whatsapp_tables
Revises:
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260924_add_whatsapp_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_configuration",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("phone_number_id", sa.String(length=128), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("app_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("verify_token_encrypted", sa.Text(), nullable=True),
        sa.Column("public_api_url", sa.String(length=512), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "whatsapp_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("phone_number", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_account_id", sa.String(length=128), nullable=False),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "provider_account_id", name="uq_whatsapp_account_provider"),
    )
    op.create_index("ix_whatsapp_accounts_workspace_id", "whatsapp_accounts", ["workspace_id"])
    op.create_table(
        "whatsapp_conversations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("whatsapp_account_id", sa.String(length=36), sa.ForeignKey("whatsapp_accounts.id"), nullable=False),
        sa.Column("external_conversation_id", sa.String(length=128), nullable=False),
        sa.Column("contact_phone", sa.String(length=64), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_message_preview", sa.Text(), nullable=True),
        sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "external_conversation_id", name="uq_whatsapp_conversation_external"),
    )
    op.create_index("ix_whatsapp_conversations_workspace_id", "whatsapp_conversations", ["workspace_id"])
    op.create_index("ix_whatsapp_conversations_whatsapp_account_id", "whatsapp_conversations", ["whatsapp_account_id"])
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False),
        sa.Column("whatsapp_conversation_id", sa.String(length=36), sa.ForeignKey("whatsapp_conversations.id"), nullable=False),
        sa.Column("external_message_id", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("sender_phone", sa.String(length=64), nullable=True),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("provider_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("media_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "external_message_id", name="uq_whatsapp_message_external"),
    )
    op.create_index("ix_whatsapp_messages_workspace_id", "whatsapp_messages", ["workspace_id"])
    op.create_index("ix_whatsapp_messages_whatsapp_conversation_id", "whatsapp_messages", ["whatsapp_conversation_id"])


def downgrade() -> None:
    op.drop_table("whatsapp_configuration")
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_conversations")
    op.drop_table("whatsapp_accounts")
