from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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

    shows = db.relationship(
        "Show", backref="venue", lazy=True, cascade="all, delete-orphan"
    )
    genres = db.relationship("Genre", secondary=venue_genres, order_by="Genre.name", lazy=True)

    @property
    def genre_names(self):
        return [genre.name for genre in self.genres]


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

    shows = db.relationship(
        "Show", backref="artist", lazy=True, cascade="all, delete-orphan"
    )
    genres = db.relationship("Genre", secondary=artist_genres, order_by="Genre.name", lazy=True)

    @property
    def genre_names(self):
        return [genre.name for genre in self.genres]


class Show(db.Model):
    __tablename__ = "Show"
    __table_args__ = (
        db.UniqueConstraint("venue_id", "artist_id", "start_time", name="uq_show_booking"),
    )

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
