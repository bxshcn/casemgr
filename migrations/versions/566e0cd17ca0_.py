"""empty message

Revision ID: 566e0cd17ca0
Revises: 
Create Date: 2018-10-17 21:24:11.305000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '566e0cd17ca0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.Column('permissions', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_roles_default'), 'roles', ['default'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('confirmed', sa.Boolean(), nullable=True),
    sa.Column('member_since', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('last_informed', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('scenarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('remark', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('edit_userid', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['edit_userid'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('cases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('remark', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('scenario_id', sa.Integer(), nullable=True),
    sa.Column('edit_userid', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['edit_userid'], ['users.id'], ),
    sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_timestamp'), 'cases', ['timestamp'], unique=False)
    op.create_table('follows',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('scenario_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'scenario_id')
    )
    op.create_table('relies',
    sa.Column('relier_id', sa.Integer(), nullable=False),
    sa.Column('relied_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['relied_id'], ['scenarios.id'], ),
    sa.ForeignKeyConstraint(['relier_id'], ['scenarios.id'], ),
    sa.PrimaryKeyConstraint('relier_id', 'relied_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('relies')
    op.drop_table('follows')
    op.drop_index(op.f('ix_cases_timestamp'), table_name='cases')
    op.drop_table('cases')
    op.drop_table('scenarios')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_default'), table_name='roles')
    op.drop_table('roles')
    # ### end Alembic commands ###
