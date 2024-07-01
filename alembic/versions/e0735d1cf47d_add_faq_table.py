"""add faq table

Revision ID: e0735d1cf47d
Revises: 6b13660ef537
Create Date: 2024-06-28 17:11:38.712686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0735d1cf47d'
down_revision: Union[str, None] = '6b13660ef537'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('FAQ',
    sa.Column('faq_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('faq_id')
    )
    op.create_index(op.f('ix_FAQ_faq_id'), 'FAQ', ['faq_id'], unique=False)
    op.create_table('country',
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.Column('country', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('country_id')
    )
    op.create_index(op.f('ix_country_country_id'), 'country', ['country_id'], unique=False)
    op.create_table('email_auth',
    sa.Column('emailAuth_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('verify_number', sa.String(length=10), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('emailAuth_id')
    )
    op.create_index(op.f('ix_email_auth_email'), 'email_auth', ['email'], unique=True)
    op.create_index(op.f('ix_email_auth_emailAuth_id'), 'email_auth', ['emailAuth_id'], unique=False)
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    op.create_table('board',
    sa.Column('board_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['email'], ['users.email'], ),
    sa.PrimaryKeyConstraint('board_id')
    )
    op.create_index(op.f('ix_board_board_id'), 'board', ['board_id'], unique=False)
    op.create_table('chat',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('Field6', sa.String(length=255), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['email'], ['users.email'], ),
    sa.PrimaryKeyConstraint('chat_id')
    )
    op.create_index(op.f('ix_chat_chat_id'), 'chat', ['chat_id'], unique=False)
    op.create_table('keyword',
    sa.Column('keyword_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('keyword', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['email'], ['users.email'], ),
    sa.PrimaryKeyConstraint('keyword_id')
    )
    op.create_index(op.f('ix_keyword_keyword_id'), 'keyword', ['keyword_id'], unique=False)
    op.create_table('state',
    sa.Column('state_id', sa.Integer(), nullable=False),
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['country_id'], ['country.country_id'], ),
    sa.PrimaryKeyConstraint('state_id')
    )
    op.create_index(op.f('ix_state_state_id'), 'state', ['state_id'], unique=False)
    op.create_table('user_info',
    sa.Column('user_info_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('corporation', sa.String(length=255), nullable=True),
    sa.Column('business_number', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['email'], ['users.email'], ),
    sa.PrimaryKeyConstraint('user_info_id')
    )
    op.create_index(op.f('ix_user_info_email'), 'user_info', ['email'], unique=True)
    op.create_index(op.f('ix_user_info_name'), 'user_info', ['name'], unique=False)
    op.create_index(op.f('ix_user_info_user_info_id'), 'user_info', ['user_info_id'], unique=False)
    op.create_table('comment',
    sa.Column('reply_id', sa.Integer(), nullable=False),
    sa.Column('board_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['board_id'], ['board.board_id'], ),
    sa.ForeignKeyConstraint(['email'], ['users.email'], ),
    sa.PrimaryKeyConstraint('reply_id')
    )
    op.create_index(op.f('ix_comment_reply_id'), 'comment', ['reply_id'], unique=False)
    op.create_table('news',
    sa.Column('news_id', sa.Integer(), nullable=False),
    sa.Column('state_id', sa.Integer(), nullable=False),
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('content', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['country_id'], ['country.country_id'], ),
    sa.ForeignKeyConstraint(['state_id'], ['state.state_id'], ),
    sa.PrimaryKeyConstraint('news_id')
    )
    op.create_index(op.f('ix_news_news_id'), 'news', ['news_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_news_news_id'), table_name='news')
    op.drop_table('news')
    op.drop_index(op.f('ix_comment_reply_id'), table_name='comment')
    op.drop_table('comment')
    op.drop_index(op.f('ix_user_info_user_info_id'), table_name='user_info')
    op.drop_index(op.f('ix_user_info_name'), table_name='user_info')
    op.drop_index(op.f('ix_user_info_email'), table_name='user_info')
    op.drop_table('user_info')
    op.drop_index(op.f('ix_state_state_id'), table_name='state')
    op.drop_table('state')
    op.drop_index(op.f('ix_keyword_keyword_id'), table_name='keyword')
    op.drop_table('keyword')
    op.drop_index(op.f('ix_chat_chat_id'), table_name='chat')
    op.drop_table('chat')
    op.drop_index(op.f('ix_board_board_id'), table_name='board')
    op.drop_table('board')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_email_auth_emailAuth_id'), table_name='email_auth')
    op.drop_index(op.f('ix_email_auth_email'), table_name='email_auth')
    op.drop_table('email_auth')
    op.drop_index(op.f('ix_country_country_id'), table_name='country')
    op.drop_table('country')
    op.drop_index(op.f('ix_FAQ_faq_id'), table_name='FAQ')
    op.drop_table('FAQ')
    # ### end Alembic commands ###