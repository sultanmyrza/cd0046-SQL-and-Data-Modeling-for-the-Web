from datetime import datetime

from app import create_app
from models import Artist, Genre, Show, Venue, db

app = create_app()

with app.app_context():
    # Empty all tables and restart ids at 1 so re-runnings are idempotent
    db.session.execute(
        'TRUNCATE "Show", "Venue", "Artist", "Genre", venue_genres, artist_genres RESTART IDENTITY CASCADE'
    )

    # One Genre row per name, shared by every venue and artist that uses it
    genre_rows = {}

    def genres(*names):
        return [genre_rows.setdefault(name, Genre(name=name)) for name in names]

    musical_hop = Venue(
        name="The Musical Hop",
        genres=genres("Jazz", "Reggae", "Swing", "Classical", "Folk"),
        address="1015 Folsom Street",
        city="San Francisco",
        state="CA",
        phone="123-123-1234",
        website_link="https://www.themusicalhop.com",
        facebook_link="https://www.facebook.com/TheMusicalHop",
        seeking_talent=True,
        seeking_description="We are on the lookout for a local artist to play every two weeks. Please call us.",
        image_link="https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    )
    dueling_pianos = Venue(
        name="The Dueling Pianos Bar",
        genres=genres("Classical", "R&B", "Hip-Hop"),
        address="335 Delancey Street",
        city="New York",
        state="NY",
        phone="914-003-1132",
        website_link="https://www.theduelingpianos.com",
        facebook_link="https://www.facebook.com/theduelingpianos",
        seeking_talent=False,
        image_link="https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    )
    park_square = Venue(
        name="Park Square Live Music & Coffee",
        genres=genres("Rock n Roll", "Jazz", "Classical", "Folk"),
        address="34 Whiskey Moore Ave",
        city="San Francisco",
        state="CA",
        phone="415-000-1234",
        website_link="https://www.parksquarelivemusicandcoffee.com",
        facebook_link="https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
        seeking_talent=False,
        image_link="https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    )

    guns_n_petals = Artist(
        name="Guns N Petals",
        genres=genres("Rock n Roll"),
        city="San Francisco",
        state="CA",
        phone="326-123-5000",
        website_link="https://www.gunsnpetalsband.com",
        facebook_link="https://www.facebook.com/GunsNPetals",
        seeking_venue=True,
        seeking_description="Looking for shows to perform at in the San Francisco Bay Area!",
        image_link="https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    )
    matt_quevedo = Artist(
        name="Matt Quevedo",
        genres=genres("Jazz"),
        city="New York",
        state="NY",
        phone="300-400-5000",
        facebook_link="https://www.facebook.com/mattquevedo923251523",
        seeking_venue=False,
        image_link="https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    )
    wild_sax_band = Artist(
        name="The Wild Sax Band",
        genres=genres("Jazz", "Classical"),
        city="San Francisco",
        state="CA",
        phone="432-325-5432",
        seeking_venue=False,
        image_link="https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    )

    shows = [
        Show(venue=musical_hop, artist=guns_n_petals, start_time=datetime(2019, 5, 21, 21, 30)),
        Show(venue=park_square, artist=matt_quevedo, start_time=datetime(2019, 6, 15, 23, 0)),
        Show(venue=park_square, artist=wild_sax_band, start_time=datetime(2035, 4, 1, 20, 0)),
        Show(venue=park_square, artist=wild_sax_band, start_time=datetime(2035, 4, 8, 20, 0)),
        Show(venue=park_square, artist=wild_sax_band, start_time=datetime(2035, 4, 15, 20, 0)),
    ]

    db.session.add_all([musical_hop, dueling_pianos, park_square])
    db.session.add_all([guns_n_petals, matt_quevedo, wild_sax_band])
    db.session.add_all(shows)
    db.session.commit()

    print(
        f"Seeded: {Venue.query.count()} venues, "
        f"{Artist.query.count()} artists, {Show.query.count()} shows"
    )
