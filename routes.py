from flask import current_app, render_template, request, flash, redirect, url_for, jsonify
from forms import VenueForm, ArtistForm, ShowForm
from models import db, Venue, Artist, Show, Genre

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

def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

def venues():
  # one entry per city/state, each with its list of venues
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
  return render_template('pages/venues.html', areas=data)

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

def show_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)

  upcoming = venue.upcoming_shows()
  past = venue.past_shows()

  def show_data(show, artist):
    return {
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': str(show.start_time),  # the template's datetime filter expects a string
    }
  
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genre_names,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,  # template reads 'website'
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

def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

def create_venue_submission():
  form = VenueForm(request.form)
  if not form.validate():
    for field, errors in form.errors.items():
      flash(f'{field}: {", ".join(errors)}')
    return render_template('forms/new_venue.html', form=form)
  
  # rollback on failure (e.g. duplicate venue) so the session isn't left broken
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
    current_app.logger.exception('Failed to create venue')
  finally:
    db.session.close()

  if not error:
    flash('Venue ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')

def delete_venue(venue_id):
  # called with fetch() from the Delete button on the venue page, so it returns JSON
  venue = Venue.query.get_or_404(venue_id)

  error = False
  try:
    db.session.delete(venue)
    db.session.commit()
  except Exception:
    error = True
    db.session.rollback()
    current_app.logger.exception("Failed to delete venue")
  finally:
    db.session.close()
  
  if error:
    return jsonify({'success': False}), 500
  return jsonify({'success': True})
  

#  Artists
#  ----------------------------------------------------------------
def artists():
  data = [
    {'id': artist.id, 'name': artist.name}
    for artist in Artist.list_by_name()
  ]
  return render_template('pages/artists.html', artists=data)

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

def show_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)

  upcoming = artist.upcoming_shows()
  past = artist.past_shows()

  def show_data(show, venue):
    return {
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': str(show.start_time),  # the template's datetime filter expects a string
    }
  
  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genre_names,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,  # template reads 'website'
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
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)
  form.genres.data = artist.genre_names  # obj= fills in Genre objects, the select needs names
  return render_template('forms/edit_artist.html', form=form, artist=artist)

def edit_artist_submission(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(request.form)
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
    current_app.logger.exception('Failed to update artist')
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist could not be updated.')
  else:
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))
  

def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)
  form.genres.data = venue.genre_names  # obj= fills in Genre objects, the select needs names
  return render_template('forms/edit_venue.html', form=form, venue=venue)

def edit_venue_submission(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(request.form)
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
    current_app.logger.exception('Failed to update venue')
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue could not be updated.')
  else:
    flash('Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

def create_artist_submission():
  form = ArtistForm(request.form)
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
    current_app.logger.exception('Failed to create artist')   
  finally:
    db.session.close()

  if not error:
    flash('Artist ' + form.name.data + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

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

def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

def create_show_submission():
  form = ShowForm(request.form)
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
    current_app.logger.exception('Failed to create show')
  finally:
    db.session.close()

  if not error:
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  return render_template('pages/home.html')

def not_found_error(error):
    return render_template('errors/404.html'), 404

def server_error(error):
    return render_template('errors/500.html'), 500


#----------------------------------------------------------------------------#
# URL rules.
#----------------------------------------------------------------------------#

def register_routes(app):
  # Plain add_url_rule (not a blueprint) keeps endpoint names like 'venues',
  # which the templates use in url_for() and request.endpoint
  app.add_url_rule('/', view_func=index)
  app.add_url_rule('/venues', view_func=venues)
  app.add_url_rule('/venues/search', view_func=search_venues, methods=['POST'])
  app.add_url_rule('/venues/<int:venue_id>', view_func=show_venue)
  app.add_url_rule('/venues/create', view_func=create_venue_form, methods=['GET'])
  app.add_url_rule('/venues/create', view_func=create_venue_submission, methods=['POST'])
  app.add_url_rule('/venues/<int:venue_id>', view_func=delete_venue, methods=['DELETE'])
  app.add_url_rule('/artists', view_func=artists)
  app.add_url_rule('/artists/search', view_func=search_artists, methods=['POST'])
  app.add_url_rule('/artists/<int:artist_id>', view_func=show_artist)
  app.add_url_rule('/artists/<int:artist_id>/edit', view_func=edit_artist, methods=['GET'])
  app.add_url_rule('/artists/<int:artist_id>/edit', view_func=edit_artist_submission, methods=['POST'])
  app.add_url_rule('/venues/<int:venue_id>/edit', view_func=edit_venue, methods=['GET'])
  app.add_url_rule('/venues/<int:venue_id>/edit', view_func=edit_venue_submission, methods=['POST'])
  app.add_url_rule('/artists/create', view_func=create_artist_form, methods=['GET'])
  app.add_url_rule('/artists/create', view_func=create_artist_submission, methods=['POST'])
  app.add_url_rule('/shows', view_func=shows)
  app.add_url_rule('/shows/create', view_func=create_shows)
  app.add_url_rule('/shows/create', view_func=create_show_submission, methods=['POST'])
  app.register_error_handler(404, not_found_error)
  app.register_error_handler(500, server_error)
