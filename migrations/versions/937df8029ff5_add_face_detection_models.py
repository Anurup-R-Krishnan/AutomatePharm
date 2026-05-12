"""add face detection models

Revision ID: 937df8029ff5
Revises: e37895a1a06d
Create Date: 2026-05-10 22:26:59.403528

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '937df8029ff5'
down_revision = 'e37895a1a06d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ai_face_logs',
    sa.Column('log_id', sa.BigInteger(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('camera_id', sa.String(length=50), nullable=False),
    sa.Column('detected_at', sa.DateTime(), nullable=False),
    sa.Column('confidence_score', sa.Float(), nullable=True),
    sa.Column('action_triggered', sa.String(length=100), nullable=True),
    sa.Column('is_fraud_alert', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], ),
    sa.PrimaryKeyConstraint('log_id')
    )
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('face_image_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('face_embedding', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('last_face_scan_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_column('last_face_scan_at')
        batch_op.drop_column('face_embedding')
        batch_op.drop_column('face_image_url')

    op.drop_table('ai_face_logs')
    op.drop_table('ai_face_logs')
    # ### end Alembic commands ###
