"""Remove session_id from chat_messages

Revision ID: 001
Revises: 
Create Date: 2025-08-08 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop session_id column from chat_messages table
    op.drop_column('chat_messages', 'session_id')
    
    # Drop chat_sessions table if it exists
    op.drop_table('chat_sessions')


def downgrade() -> None:
    # Recreate chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate session_id column in chat_messages
    op.add_column('chat_messages', sa.Column('session_id', postgresql.UUID(as_uuid=False), nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key(None, 'chat_messages', 'chat_sessions', ['session_id'], ['id'])
