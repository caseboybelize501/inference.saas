from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
dependencies = None
branch_labels = None


def upgrade():
    op.create_table(
        'clusters',
        sa.Column('cluster_id', sa.String(), nullable=False),
        sa.Column('gpus', postgresql.JSONB(), nullable=True),
        sa.Column('system_ram', sa.Float(), nullable=True),
        sa.Column('servers', postgresql.JSONB(), nullable=True),
        sa.Column('models', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('cluster_id')
    )
    op.create_table(
        'optimizations',
        sa.Column('optimization_id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=True),
        sa.Column('model_sha256', sa.String(), nullable=True),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('predicted_tps_gain_pct', sa.Float(), nullable=True),
        sa.Column('validation_required', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('optimization_id')
    )
    op.create_table(
        'telemetry',
        sa.Column('snapshot_id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=True),
        sa.Column('gpus', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('snapshot_id')
    )
    op.create_table(
        'benchmarks',
        sa.Column('benchmark_id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=True),
        sa.Column('model_sha256', sa.String(), nullable=True),
        sa.Column('quant_format', sa.String(), nullable=True),
        sa.Column('quant_level', sa.Integer(), nullable=True),
        sa.Column('backend', sa.String(), nullable=True),
        sa.Column('attention_kernel', sa.String(), nullable=True),
        sa.Column('batch_size', sa.Integer(), nullable=True),
        sa.Column('context_len', sa.Integer(), nullable=True),
        sa.Column('decode_tps', sa.Float(), nullable=True),
        sa.Column('prefill_tps', sa.Float(), nullable=True),
        sa.Column('ttft_ms', sa.Integer(), nullable=True),
        sa.Column('vram_used_gb', sa.Float(), nullable=True),
        sa.Column('power_w', sa.Float(), nullable=True),
        sa.Column('ppl_delta_vs_fp16', sa.Float(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('benchmark_id')
    )
    op.create_table(
        'tenants',
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('subscription_tier', sa.String(), nullable=True),
        sa.Column('billing_info', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('tenant_id')
    )

def downgrade():
    op.drop_table('tenants')
    op.drop_table('benchmarks')
    op.drop_table('telemetry')
    op.drop_table('optimizations')
    op.drop_table('clusters')