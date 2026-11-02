#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Venue, Artist, Show
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  rows = (
    db.session.query(Venue, db.func.count(Show.id))
    .outerjoin(Show, db.and_(Show.venue_id == Venue.id, Show.start_time > datetime.now()))
    .group_by(Venue.id)
    .order_by(Venue.state, Venue.city, Venue.name)
    .all()
  )
  data = {}
  for venue, num_upcoming_shows in rows:
    area = data.setdefault(
      (venue.city, venue.state),
      {'city': venue.city, 'state': venue.state, 'venues': []}
    )
    area['venues'].append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': num_upcoming_shows
    })
  data = list(data.values())
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  rows = (
    db.session.query(Venue, db.func.count(Show.id))
    .outerjoin(Show, db.and_(Show.venue_id == Venue.id, Show.start_time > datetime.now()))
    .filter(Venue.name.ilike(f'%{search_term}%'))
    .group_by(Venue.id)
    .order_by(Venue.name)
    .all()
  )
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": len(rows),
    "data": [{
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows,
    } for venue, num_upcoming_shows in rows]
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get_or_404(venue_id)

  now = datetime.now()
  shows = db.session.query(Show, Artist).join(Artist).filter(Show.venue_id == venue_id)
  upcoming = shows.filter(Show.start_time > now).order_by(Show.start_time).all()
  past = shows.filter(Show.start_time <= now).order_by(Show.start_time.desc()).all()

  def show_data(show, artist):
    return {
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time),
    }
  
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': [show_data(show, artist) for show, artist in past],
    'upcoming_shows': [show_data(show, artist) for show, artist in upcoming],
    'past_shows_count': len(past),
    'upcoming_shows_count': len(upcoming),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/new_venue.html', form=form)
  
  error = False
  try:
    venue = Venue(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      address=form.address.data,
      phone=form.phone.data,
      genres=form.genres.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      website_link=form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data,
    )
    db.session.add(venue)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception('Failed to create venue')
  finally:
    db.session.close()


  # on successful db insert, flash success
  if not error:
    flash('Venue ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = [
    {'id': artist.id, 'name': artist.name}
    for artist in Artist.query.order_by(Artist.name).all()
  ]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  rows = (
    db.session.query(Artist, db.func.count(Show.id))
    .outerjoin(Show, db.and_(Show.artist_id == Artist.id, Show.start_time > datetime.now()))
    .filter(Artist.name.ilike(f'%{search_term}%'))
    .group_by(Artist.id)
    .order_by(Artist.name)
    .all()
  )
  response={
    "count": len(rows),
    "data": [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
    } for artist, num_upcoming_shows in rows]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.get_or_404(artist_id)

  now = datetime.now()
  shows = db.session.query(Show, Venue).join(Venue).filter(Show.artist_id == artist_id)
  upcoming = shows.filter(Show.start_time > now).order_by(Show.start_time).all()
  past = shows.filter(Show.start_time <= now).order_by(Show.start_time.desc()).all()

  def show_data(show, venue):
    return {
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(show.start_time),
    }
  
  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': [show_data(show, venue) for show, venue in past],
    'upcoming_shows': [show_data(show, venue) for show, venue in upcoming],
    'past_shows_count': len(past),
    'upcoming_shows_count': len(upcoming),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/edit_artist.html', form=form, artist=artist)

  error = False
  try:
    form.populate_obj(artist)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception('Failed to update artist')
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist could not be updated.')
  else:
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))
  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/edit_venue.html', form=form, venue=venue)

  error = False
  try:
    form.populate_obj(venue)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception('Failed to update venue')
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue could not be updated.')
  else:
    flash('Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/new_artist.html', form=form)

  error = False
  try:
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      genres=form.genres.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      website_link=form.website_link.data,
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data,
    )
    db.session.add(artist)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception('Failed to create artist')   
  finally:
    db.session.close()

  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  rows = (
    db.session.query(Show, Venue, Artist)
    .join(Venue)
    .join(Artist)
    .order_by(Show.start_time)
    .all()
  )
  data = [{
    'venue_id': venue.id,
    'venue_name': venue.name,
    'artist_id': artist.id,
    'artist_name': artist.name,
    'artist_image_link': artist.image_link,
    'start_time': str(show.start_time),
  } for show, venue, artist in rows]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/new_show.html', form=form)

  error = False
  try:
    show = Show(
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data,
    )
    db.session.add(show)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception('Failed to create show')
  finally:
    db.session.close()

  if not error:
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
