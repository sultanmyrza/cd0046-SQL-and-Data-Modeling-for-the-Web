from datetime import datetime

from extensions import db


# Many-to-many links between venues/artists and genres
venue_genres = db.Table(
    "venue_genres",
    db.Column("venue_id", db.Integer, db.ForeignKey("Venue.id", ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("Genre.id", ondelete="CASCADE"), primary_key=True),
)

artist_genres = db.Table(
    "artist_genres",
    db.Column("artist_id", db.Integer, db.ForeignKey("Artist.id", ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("Genre.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(db.Model):
    __tablename__ = "Genre"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    @classmethod
    def from_names(cls, names):
        """Return Genre rows for the given names, creating the ones that don't exist yet."""
        names = list(dict.fromkeys(names))  # drop duplicates, keep order
        existing = {genre.name: genre for genre in cls.query.filter(cls.name.in_(names))}
        return [existing.get(name) or cls(name=name) for name in names]


class Venue(db.Model):
    __tablename__ = "Venue"
    __table_args__ = (
        db.UniqueConstraint("name", "city", "state", "address", name="uq_venue_identity"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # deleting a venue also deletes its shows
    shows = db.relationship(
        "Show", backref="venue", lazy=True, cascade="all, delete-orphan"
    )
    genres = db.relationship("Genre", secondary=venue_genres, order_by="Genre.name", lazy=True)

    @property
    def genre_names(self):
        return [genre.name for genre in self.genres]

    @classmethod
    def _with_upcoming_show_counts(cls):
        """(venue, number of upcoming shows) pairs; venues without upcoming shows count 0."""
        return (
            db.session.query(cls, db.func.count(Show.id))
            .outerjoin(Show, db.and_(Show.venue_id == cls.id, Show.is_upcoming()))
            .group_by(cls.id)
        )

    @classmethod
    def list_with_upcoming_show_counts(cls):
        """All venues with upcoming show counts, ordered by state, city and name."""
        return cls._with_upcoming_show_counts().order_by(cls.state, cls.city, cls.name).all()

    @classmethod
    def search(cls, term):
        """Venues whose name contains term (case-insensitive), with upcoming show counts."""
        return (
            cls._with_upcoming_show_counts()
            .filter(cls.name.ilike(f"%{term}%"))
            .order_by(cls.name)
            .all()
        )

    def _shows_with_artists(self):
        return db.session.query(Show, Artist).join(Artist).filter(Show.venue_id == self.id)

    def upcoming_shows(self):
        """(show, artist) pairs for upcoming shows at this venue, soonest first."""
        return self._shows_with_artists().filter(Show.is_upcoming()).order_by(Show.start_time).all()

    def past_shows(self):
        """(show, artist) pairs for past shows at this venue, most recent first."""
        return self._shows_with_artists().filter(Show.is_past()).order_by(Show.start_time.desc()).all()


class Artist(db.Model):
    __tablename__ = "Artist"
    __table_args__ = (
        db.UniqueConstraint("name", "city", "state", name="uq_artist_identity"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # deleting an artist also deletes its shows
    shows = db.relationship(
        "Show", backref="artist", lazy=True, cascade="all, delete-orphan"
    )
    genres = db.relationship("Genre", secondary=artist_genres, order_by="Genre.name", lazy=True)

    @property
    def genre_names(self):
        return [genre.name for genre in self.genres]

    @classmethod
    def list_by_name(cls):
        return cls.query.order_by(cls.name).all()

    @classmethod
    def search(cls, term):
        """Artists whose name contains term (case-insensitive), with upcoming show counts."""
        return (
            db.session.query(cls, db.func.count(Show.id))
            .outerjoin(Show, db.and_(Show.artist_id == cls.id, Show.is_upcoming()))
            .filter(cls.name.ilike(f"%{term}%"))
            .group_by(cls.id)
            .order_by(cls.name)
            .all()
        )

    def _shows_with_venues(self):
        return db.session.query(Show, Venue).join(Venue).filter(Show.artist_id == self.id)

    def upcoming_shows(self):
        """(show, venue) pairs for this artist's upcoming shows, soonest first."""
        return self._shows_with_venues().filter(Show.is_upcoming()).order_by(Show.start_time).all()

    def past_shows(self):
        """(show, venue) pairs for this artist's past shows, most recent first."""
        return self._shows_with_venues().filter(Show.is_past()).order_by(Show.start_time.desc()).all()


class Show(db.Model):
    """An artist playing at a venue at a given time. Links Venue and Artist (many-to-many)."""

    __tablename__ = "Show"
    __table_args__ = (
        db.UniqueConstraint("venue_id", "artist_id", "start_time", name="uq_show_booking"),
    )

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    @classmethod
    def is_upcoming(cls):
        """SQL condition for shows that haven't started yet."""
        return cls.start_time > datetime.now()

    @classmethod
    def is_past(cls):
        return cls.start_time <= datetime.now()

    @classmethod
    def list_with_details(cls):
        """(show, venue, artist) for every show, oldest first."""
        return (
            db.session.query(cls, Venue, Artist)
            .join(Venue)
            .join(Artist)
            .order_by(cls.start_time)
            .all()
        )
