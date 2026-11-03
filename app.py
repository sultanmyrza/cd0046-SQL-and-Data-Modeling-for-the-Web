#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
from models import db, Venue, Artist, Show, Genre
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
# Helpers.
#----------------------------------------------------------------------------#

def populate_with_genres(form, obj):
  # Genres are Genre rows, not plain strings, so they are set separately
  for field in form:
    if field.name != 'genres':
      field.populate_obj(obj, field.name)
  obj.genres = Genre.from_names(form.genres.data)

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
  data = {}
  for venue, num_upcoming_shows in Venue.list_with_upcoming_show_counts():
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
  rows = Venue.search(search_term)
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

  upcoming = venue.upcoming_shows()
  past = venue.past_shows()

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
    'genres': venue.genre_names,
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
      genres=Genre.from_names(form.genres.data),
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

  if not error:
    flash('Venue ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)

  error = False
  try:
    db.session.delete(venue)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    app.logger.exception("Failed to delete venue")
  finally:
    db.session.close()
  
  if error:
    return jsonify({'success': False}), 500
  return jsonify({'success': True})
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = [
    {'id': artist.id, 'name': artist.name}
    for artist in Artist.list_by_name()
  ]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  rows = Artist.search(search_term)
  response={
    "count": len(rows),
    "data": [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
    } for artist, num_upcoming_shows in rows]
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)

  upcoming = artist.upcoming_shows()
  past = artist.past_shows()

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
    'genres': artist.genre_names,
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
  form.genres.data = artist.genre_names
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/edit_artist.html', form=form, artist=artist)

  error = False
  try:
    populate_with_genres(form, artist)
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
  form.genres.data = venue.genre_names
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/edit_venue.html', form=form, venue=venue)

  error = False
  try:
    populate_with_genres(form, venue)
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
      genres=Genre.from_names(form.genres.data),
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
    flash('Artist ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = [{
    'venue_id': venue.id,
    'venue_name': venue.name,
    'artist_id': artist.id,
    'artist_name': artist.name,
    'artist_image_link': artist.image_link,
    'start_time': str(show.start_time),
  } for show, venue, artist in Show.list_with_details()]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
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
