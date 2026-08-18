"""Initial Nyaya Setu tables.

Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '0001_initial'; down_revision = None; branch_labels = None; depends_on = None
def upgrade():
    role = sa.Enum('citizen','csc_operator','paralegal','admin', name='role'); input_type = sa.Enum('text','voice','image', name='inputtype'); status = sa.Enum('collecting','ready','generated', name='draftstatus')
    op.create_table('users', sa.Column('id',sa.Integer,primary_key=True),sa.Column('email',sa.String(320),nullable=False,unique=True),sa.Column('hashed_password',sa.String(255),nullable=False),sa.Column('role',role,nullable=False),sa.Column('preferred_language',sa.String(32),nullable=False),sa.Column('consent_given',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('sessions',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id')),sa.Column('started_at',sa.DateTime,nullable=False),sa.Column('sensitive_mode',sa.Boolean,nullable=False)); op.create_index('ix_sessions_user_id','sessions',['user_id'])
    op.create_table('queries',sa.Column('id',sa.Integer,primary_key=True),sa.Column('session_id',sa.Integer,sa.ForeignKey('sessions.id'),nullable=False),sa.Column('raw_input_type',input_type,nullable=False),sa.Column('raw_input_ref',sa.Text,nullable=False),sa.Column('detected_language',sa.String(32)),sa.Column('intent',sa.String(100)),sa.Column('beneficiary_context',sa.String(100))); op.create_index('ix_queries_session_id','queries',['session_id'])
    op.create_table('responses',sa.Column('id',sa.Integer,primary_key=True),sa.Column('query_id',sa.Integer,sa.ForeignKey('queries.id'),nullable=False),sa.Column('answer_payload',postgresql.JSONB,nullable=False),sa.Column('confidence_score',sa.Float),sa.Column('fallback_used',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False)); op.create_index('ix_responses_query_id','responses',['query_id'])
    op.create_table('documents_uploaded',sa.Column('id',sa.Integer,primary_key=True),sa.Column('session_id',sa.Integer,sa.ForeignKey('sessions.id'),nullable=False),sa.Column('original_filename',sa.String(255),nullable=False),sa.Column('storage_ref',sa.String(500),nullable=False),sa.Column('doc_type',sa.String(100)),sa.Column('extracted_fields',postgresql.JSONB),sa.Column('created_at',sa.DateTime,nullable=False)); op.create_index('ix_documents_uploaded_session_id','documents_uploaded',['session_id'])
    op.create_table('drafted_documents',sa.Column('id',sa.Integer,primary_key=True),sa.Column('session_id',sa.Integer,sa.ForeignKey('sessions.id'),nullable=False),sa.Column('doc_type',sa.String(100),nullable=False),sa.Column('collected_fields',postgresql.JSONB,nullable=False),sa.Column('draft_status',status,nullable=False),sa.Column('final_file_ref',sa.String(500)),sa.Column('created_at',sa.DateTime,nullable=False)); op.create_index('ix_drafted_documents_session_id','drafted_documents',['session_id'])
    op.create_table('timelines',sa.Column('id',sa.Integer,primary_key=True),sa.Column('session_id',sa.Integer,sa.ForeignKey('sessions.id'),nullable=False),sa.Column('events',postgresql.JSONB,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False)); op.create_index('ix_timelines_session_id','timelines',['session_id'])
    op.create_table('audit_log',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id')),sa.Column('action',sa.String(100),nullable=False),sa.Column('resource_type',sa.String(100),nullable=False),sa.Column('resource_id',sa.String(100),nullable=False),sa.Column('timestamp',sa.DateTime,nullable=False)); op.create_index('ix_audit_log_user_id','audit_log',['user_id'])
def downgrade():
    for table in ['audit_log','timelines','drafted_documents','documents_uploaded','responses','queries','sessions','users']: op.drop_table(table)
