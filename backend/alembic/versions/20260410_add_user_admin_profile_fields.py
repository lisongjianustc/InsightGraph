"""Add user admin/profile fields

Revision ID: 20260410_add_user_admin_profile_fields
Revises: 1a2b3c4d5e6f
Create Date: 2026-04-10 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "20260410_add_user_admin_profile_fields"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    try:
        op.add_column("users", sa.Column("display_name", sa.String(), nullable=True))
        conn.commit()
    except Exception:
        conn.rollback()
    try:
        op.add_column("users", sa.Column("email", sa.String(), nullable=True))
        conn.commit()
    except Exception:
        conn.rollback()
    try:
        op.add_column("users", sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=True))
        conn.commit()
    except Exception:
        conn.rollback()
    try:
        op.add_column("users", sa.Column("must_change_password", sa.Boolean(), server_default=sa.text("false"), nullable=True))
        conn.commit()
    except Exception:
        conn.rollback()
    try:
        op.add_column("users", sa.Column("token_version", sa.Integer(), server_default="0", nullable=True))
        conn.commit()
    except Exception:
        conn.rollback()

    try:
        op.execute(sa.text("UPDATE users SET is_admin = CASE WHEN username = 'admin' THEN TRUE ELSE FALSE END"))
        op.execute(sa.text("UPDATE users SET token_version = 0 WHERE token_version IS NULL"))
        op.execute(sa.text("UPDATE users SET must_change_password = FALSE WHERE must_change_password IS NULL"))
        conn.commit()
    except Exception:
        conn.rollback()


def downgrade() -> None:
    conn = op.get_bind()
    for col in ["token_version", "must_change_password", "is_admin", "email", "display_name"]:
        try:
            op.drop_column("users", col)
            conn.commit()
        except Exception:
            conn.rollback()
