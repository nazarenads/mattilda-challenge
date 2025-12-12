"""Create payment and payment_allocation tables

Revision ID: 2a3b4c5d6e7f
Revises: 168e19bf0745
Create Date: 2025-12-11 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a3b4c5d6e7f'
down_revision = '168e19bf0745'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('payment_method', sa.String(length=20), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_id'), 'payment', ['id'], unique=False)
    op.create_table('payment_allocation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('payment_id', sa.Integer(), nullable=False),
    sa.Column('invoice_id', sa.Integer(), nullable=False),
    sa.Column('amount_in_cents', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ),
    sa.ForeignKeyConstraint(['invoice_id'], ['invoice.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_allocation_id'), 'payment_allocation', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_allocation_id'), table_name='payment_allocation')
    op.drop_table('payment_allocation')
    op.drop_index(op.f('ix_payment_id'), table_name='payment')
    op.drop_table('payment')
