"""Add User model and multitenant fields

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-04-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Check if users table exists
    has_users = False
    try:
        conn.execute(sa.text("SELECT 1 FROM users LIMIT 1"))
        has_users = True
    except Exception:
        # In postgres, failed query aborts transaction. Must rollback.
        conn.rollback()

    if not has_users:
        # 1. Create users table
        try:
            op.create_table('users',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('username', sa.String(), nullable=False),
                sa.Column('hashed_password', sa.String(), nullable=False),
                sa.Column('dify_private_dataset_id', sa.String(), nullable=True),
                sa.Column('is_active', sa.Boolean(), nullable=True),
                sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
                sa.PrimaryKeyConstraint('id')
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
            conn.commit()
        except Exception:
            conn.rollback()
    
        # Insert a default Admin user (password: Admin@123)
        try:
            op.execute(sa.text("""
                INSERT INTO users (username, hashed_password) 
                VALUES (:username, :password)
            """).bindparams(username='admin', password='$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'))
            conn.commit()
        except Exception:
            conn.rollback()

    # 2. Add owner_id and visibility to all existing tables
    tables = ['capsules', 'daily_notes', 'feed_items', 'source_configs', 'graph_nodes', 'graph_edges', 'global_conversations']
    
    for table in tables:
        # Check if columns exist
        has_owner = False
        try:
            conn.execute(sa.text(f"SELECT owner_id FROM {table} LIMIT 1"))
            has_owner = True
        except Exception:
            conn.rollback()

        if not has_owner:
            # Add columns
            try:
                op.add_column(table, sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
                conn.commit()
            except Exception:
                conn.rollback()
            try:
                op.add_column(table, sa.Column('visibility', sa.String(), nullable=True))
                conn.commit()
            except Exception:
                conn.rollback()
            
            # Update existing records to belong to Admin (id=1) and be private
            try:
                op.execute(sa.text(f"UPDATE {table} SET owner_id = :owner_id, visibility = :visibility").bindparams(owner_id=1, visibility='private'))
                conn.commit()
            except Exception:
                conn.rollback()
            
            # Create indices
            try:
                op.create_index(op.f(f'ix_{table}_owner_id'), table, ['owner_id'], unique=False)
                conn.commit()
            except Exception:
                conn.rollback()
            try:
                op.create_index(op.f(f'ix_{table}_visibility'), table, ['visibility'], unique=False)
                conn.commit()
            except Exception:
                conn.rollback()


def downgrade() -> None:
    tables = ['global_conversations', 'graph_edges', 'graph_nodes', 'source_configs', 'feed_items', 'daily_notes', 'capsules']
    
    for table in tables:
        try:
            op.drop_constraint(f"fk_{table}_owner_id", table, type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_index(op.f(f'ix_{table}_visibility'), table_name=table)
        except Exception:
            pass
        try:
            op.drop_index(op.f(f'ix_{table}_owner_id'), table_name=table)
        except Exception:
            pass
        try:
            op.drop_column(table, 'visibility')
        except Exception:
            pass
        try:
            op.drop_column(table, 'owner_id')
        except Exception:
            pass

    try:
        op.drop_index(op.f('ix_users_username'), table_name='users')
    except Exception:
        pass
    try:
        op.drop_index(op.f('ix_users_id'), table_name='users')
    except Exception:
        pass
    try:
        op.drop_table('users')
    except Exception:
        pass
