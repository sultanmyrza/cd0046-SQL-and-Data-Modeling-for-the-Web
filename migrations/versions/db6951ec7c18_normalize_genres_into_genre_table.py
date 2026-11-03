"""normalize genres into genre table

Revision ID: db6951ec7c18
Revises: 37ae2b1701ac
Create Date: 2026-11-03 10:52:38.719607

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'db6951ec7c18'
down_revision = '37ae2b1701ac'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('Genre',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('artist_genres',
    sa.Column('artist_id', sa.Integer(), nullable=False),
    sa.Column('genre_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('artist_id', 'genre_id')
    )
    op.create_table('venue_genres',
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.Column('genre_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['genre_id'], ['Genre.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['venue_id'], ['Venue.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('venue_id', 'genre_id')
    )

    # Copy the existing array values into the new tables before dropping the columns
    op.execute("""
        INSERT INTO "Genre" (name)
        SELECT unnest(genres) FROM "Venue"
        UNION
        SELECT unnest(genres) FROM "Artist"
    """)
    op.execute("""
        INSERT INTO venue_genres (venue_id, genre_id)
        SELECT DISTINCT v.id, g.id
        FROM "Venue" v
        CROSS JOIN LATERAL unnest(v.genres) AS u(name)
        JOIN "Genre" g ON g.name = u.name
    """)
    op.execute("""
        INSERT INTO artist_genres (artist_id, genre_id)
        SELECT DISTINCT a.id, g.id
        FROM "Artist" a
        CROSS JOIN LATERAL unnest(a.genres) AS u(name)
        JOIN "Genre" g ON g.name = u.name
    """)

    op.drop_column('Artist', 'genres')
    op.drop_column('Venue', 'genres')


def downgrade():
    # Add the columns back as nullable, refill them from the link tables, then require them
    op.add_column('Venue', sa.Column('genres', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.add_column('Artist', sa.Column('genres', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.execute("""
        UPDATE "Venue" v SET genres = ARRAY(
            SELECT g.name FROM venue_genres vg JOIN "Genre" g ON g.id = vg.genre_id
            WHERE vg.venue_id = v.id ORDER BY g.name
        )
    """)
    op.execute("""
        UPDATE "Artist" a SET genres = ARRAY(
            SELECT g.name FROM artist_genres ag JOIN "Genre" g ON g.id = ag.genre_id
            WHERE ag.artist_id = a.id ORDER BY g.name
        )
    """)
    op.alter_column('Venue', 'genres', nullable=False)
    op.alter_column('Artist', 'genres', nullable=False)

    op.drop_table('venue_genres')
    op.drop_table('artist_genres')
    op.drop_table('Genre')
