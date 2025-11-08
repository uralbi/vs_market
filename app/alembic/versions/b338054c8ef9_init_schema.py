"""init schema

Revision ID: b338054c8ef9
Revises: 
Create Date: 2025-10-26 15:03:50.512889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b338054c8ef9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('role', postgresql.ENUM('ADMIN', 'MANAGER', 'USER', 'CREATOR', name='userrole'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # --- chat_rooms ---
    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('user1_id', sa.String(length=26), nullable=True),
        sa.Column('user2_id', sa.String(length=26), nullable=True),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_rooms_id'), 'chat_rooms', ['id'], unique=False)

    # --- entities ---
    op.create_table(
        'entities',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('creator_id', sa.String(length=26), nullable=False),
        sa.Column('entity_name', sa.String(), nullable=False),
        sa.Column('entity_phone', sa.String(length=20), nullable=False),
        sa.Column('entity_address', sa.String(), nullable=True),
        sa.Column('entity_whatsapp', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('creator_id'),
        sa.UniqueConstraint('entity_phone'),
        sa.UniqueConstraint('entity_whatsapp')
    )
    op.create_index(op.f('ix_entities_entity_name'), 'entities', ['entity_name'], unique=True)
    op.create_index(op.f('ix_entities_id'), 'entities', ['id'], unique=False)

    # --- movies ---
    op.create_table(
        'movies',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('owner_id', sa.String(length=26), nullable=False),
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')), 'A') "
                "|| setweight(to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(description, '')), 'B')",
                persisted=True
            ),
            nullable=True
        ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_movies_search', 'movies', ['search_vector'], unique=False, postgresql_using='gin')
    op.create_index(op.f('ix_movies_id'), 'movies', ['id'], unique=False)
    op.create_index(op.f('ix_movies_title'), 'movies', ['title'], unique=True)

    # --- products ---
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('is_dollar', sa.Boolean(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('activated', sa.Boolean(), nullable=False),
        sa.Column('owner_id', sa.String(length=26), nullable=False),
        sa.Column(
            'search_vector',
            postgresql.TSVECTOR(),
            sa.Computed(
                "setweight(to_tsvector('russian', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, '')), 'A') "
                "|| setweight(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, '')), 'B')",
                persisted=True
            ),
            nullable=True
        ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'owner_id', name='uix_owner_product_name')
    )

    # Enable trigram extension (needed for gin_trgm_ops)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Full-text search index on products.search_vector (kept)
    op.create_index('idx_products_search', 'products', ['search_vector'], unique=False, postgresql_using='gin')

    # Replace the broken multi-column trigram index with proper per-column trigram GIN indexes
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (name gin_trgm_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_description_trgm ON products USING gin (description gin_trgm_ops);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_category_trgm ON products USING gin (category gin_trgm_ops);")

    # Optional: functional btree indexes for case-insensitive equality/ordering
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_name_lower ON products (lower(name));")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_description_lower ON products (lower(description));")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_category_lower ON products (lower(category));")

    # Regular simple indexes
    op.create_index(op.f('ix_products_activated'), 'products', ['activated'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)

    # --- favorites ---
    op.create_table(
        'favorites',
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('product_id', sa.String(length=26), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'product_id')
    )

    # --- messages ---
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('chat_room_id', sa.String(length=26), nullable=True),
        sa.Column('sender_id', sa.String(length=26), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id']),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # --- movie_comments ---
    op.create_table(
        'movie_comments',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('movie_id', sa.String(length=26), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movie_comments_id'), 'movie_comments', ['id'], unique=False)

    # --- movie_likes ---
    op.create_table(
        'movie_likes',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('movie_id', sa.String(length=26), nullable=False),
        sa.Column('liked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movie_likes_id'), 'movie_likes', ['id'], unique=False)

    # --- movie_subtitles ---
    op.create_table(
        'movie_subtitles',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('movie_id', sa.String(length=26), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movie_subtitles_id'), 'movie_subtitles', ['id'], unique=False)

    # --- movie_views ---
    op.create_table(
        'movie_views',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('movie_id', sa.String(length=26), nullable=False),
        sa.Column('watched_at', sa.DateTime(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movie_views_id'), 'movie_views', ['id'], unique=False)

    # --- orders ---
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('user_id', sa.String(length=26), nullable=False),
        sa.Column('movie_id', sa.String(length=26), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'COMPLETED', 'FAILED', name='order_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movies.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)

    # --- product_images ---
    op.create_table(
        'product_images',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('product_id', sa.String(length=26), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_images_id'), 'product_images', ['id'], unique=False)
    op.create_index(op.f('ix_product_images_product_id'), 'product_images', ['product_id'], unique=False)


def downgrade() -> None:
    # product_images
    op.drop_index(op.f('ix_product_images_product_id'), table_name='product_images')
    op.drop_index(op.f('ix_product_images_id'), table_name='product_images')
    op.drop_table('product_images')

    # orders
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')

    # movie_views
    op.drop_index(op.f('ix_movie_views_id'), table_name='movie_views')
    op.drop_table('movie_views')

    # movie_subtitles
    op.drop_index(op.f('ix_movie_subtitles_id'), table_name='movie_subtitles')
    op.drop_table('movie_subtitles')

    # movie_likes
    op.drop_index(op.f('ix_movie_likes_id'), table_name='movie_likes')
    op.drop_table('movie_likes')

    # movie_comments
    op.drop_index(op.f('ix_movie_comments_id'), table_name='movie_comments')
    op.drop_table('movie_comments')

    # messages
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')

    # favorites
    op.drop_table('favorites')

    # products indexes (drop our new ones)
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_index(op.f('ix_products_activated'), table_name='products')
    op.execute("DROP INDEX IF EXISTS idx_products_category_lower;")
    op.execute("DROP INDEX IF EXISTS idx_products_description_lower;")
    op.execute("DROP INDEX IF EXISTS idx_products_name_lower;")
    op.execute("DROP INDEX IF EXISTS idx_products_category_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_products_description_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_products_name_trgm;")
    op.drop_index('idx_products_search', table_name='products', postgresql_using='gin')
    op.drop_table('products')

    # movies
    op.drop_index(op.f('ix_movies_title'), table_name='movies')
    op.drop_index(op.f('ix_movies_id'), table_name='movies')
    op.drop_index('idx_movies_search', table_name='movies', postgresql_using='gin')
    op.drop_table('movies')

    # entities
    op.drop_index(op.f('ix_entities_id'), table_name='entities')
    op.drop_index(op.f('ix_entities_entity_name'), table_name='entities')
    op.drop_table('entities')

    # chat_rooms
    op.drop_index(op.f('ix_chat_rooms_id'), table_name='chat_rooms')
    op.drop_table('chat_rooms')

    # users
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
