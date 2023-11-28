from datetime import timedelta

from celery import Celery
from flasgger import Swagger
from flask import Flask
from flask_limiter import Limiter
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
swagger = Swagger(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

app.config['CELERYBEAT_SCHEDULE'] = {
    'run-reminder-task': {
        'task': 'celery_tasks.reminder_task',
        'schedule': timedelta(minutes=0.2),
    },
}
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

limiter = Limiter(app)
limiter.key_func = lambda: request.headers.get('Authorization')
socketio = SocketIO(app)

from application.models import User, Subscription, Event
from application.celery_tasks import reminder_task
from application.auth import auth_required, is_valid_login
from application.routes import *

with app.app_context():
    db.create_all()
