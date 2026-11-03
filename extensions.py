from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
moment = Moment()
migrate = Migrate()
