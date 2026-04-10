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
    # 1. Create users table
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
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Insert a default Admin user (password: Admin@123)
    op.execute("""
        INSERT INTO users (username, hashed_password) 
        VALUES ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
    """)

    # 2. Add owner_id and visibility to all existing tables
    tables = ['capsules', 'daily_notes', 'feed_items', 'source_configs', 'graph_nodes', 'graph_edges', 'global_conversations']
    
    for table in tables:
        # Add columns
        op.add_column(table, sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
        op.add_column(table, sa.Column('visibility', sa.String(), nullable=True))
        
        # Update existing records to belong to Admin (id=1) and be private
        op.execute(f"UPDATE {table} SET owner_id = 1, visibility = 'private'")
        
        # Create indices
        op.create_index(op.f(f'ix_{table}_owner_id'), table, ['owner_id'], unique=False)
        op.create_index(op.f(f'ix_{table}_visibility'), table, ['visibility'], unique=False)


def downgrade() -> None:
    tables = ['global_conversations', 'graph_edges', 'graph_nodes', 'source_configs', 'feed_items', 'daily_notes', 'capsules']
    
    for table in tables:
        op.drop_constraint(f"fk_{table}_owner_id", table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_visibility'), table_name=table)
        op.drop_index(op.f(f'ix_{table}_owner_id'), table_name=table)
        op.drop_column(table, 'visibility')
        op.drop_column(table, 'owner_id')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
