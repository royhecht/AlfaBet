from datetime import datetime, timedelta
from application.models import Event
from application import celery, app


@celery.task
def reminder_task():
    with app.app_context():
        now = datetime.utcnow()
        events = Event.query.filter(Event.date > now, Event.date <= now + timedelta(minutes=30)).all()
        for event in events:
            print(f"Reminder: Event '{event.title}' is starting in 30 minutes at {event.date}")
