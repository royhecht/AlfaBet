from datetime import datetime

from flask import request, jsonify

from application import app, db
from application import socketio
from application.auth import auth_required, get_user_id
from application.models import User, Subscription, Event


@app.route('/events', methods=['POST'])
@auth_required
def schedule_event():
    """
    Schedule a new event.

    Schedule a new event with the provided details.

    ---
    parameters:
      - name: title
        in: formData
        type: string
        required: true
        description: The title of the event
      - name: location
        in: formData
        type: string
        required: true
        description: The location of the event
      - name: date
        in: formData
        type: string
        required: true
        description: The date and time of the event in ISO format (e.g., "2023-12-01T12:00:00")
      - name: participants
        in: formData
        type: int
        required: true
        description: The Number of participants

    responses:
      200:
        description: Event scheduled successfully
    """
    data = request.form
    new_event = Event(title=data['title'], location=data['location'], date=datetime.fromisoformat(data['date']),
                      participants=data['participants'])
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Event scheduled successfully"})


@app.route('/events', methods=['GET'])
@auth_required
def get_all_events():
    """
    Retrieve a list of all scheduled events.

    Get a list of all events with their details.

    ---
    responses:
      200:
        description: List of all scheduled events
    """
    events = Event.query.all()
    event_list = [{"id": event.id, "title": event.title, "location": event.location,
                   "date": event.date, "participants": event.participants}
                  for event in events]
    return jsonify(event_list)


@app.route('/events/<int:event_id>', methods=['GET'])
@auth_required
def get_event(event_id):
    """
    Retrieve details of a specific event.

    Get details of a specific event using its ID.

    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event

    responses:
      200:
        description: Details of the specified event
    """
    event = Event.query.get_or_404(event_id)
    return jsonify({"id": event.id, "title": event.title, "location": event.location, "date": event.date,
                    "participants": event.participants})


@app.route('/events/<int:event_id>', methods=['PUT'])
@auth_required
def update_event(event_id):
    """
    Update details of a specific event.

    Update the title, location, and date of a specific event.

    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event
      - name: title
        in: formData
        type: string
        required: true
        description: The updated title of the event
      - name: location
        in: formData
        type: string
        required: true
        description: The updated location of the event
      - name: date
        in: formData
        type: string
        required: true
        description: The updated date and time of the event in ISO format (e.g., "2023-12-01T12:00:00")
      - name: participants
        in: formData
        type: int
        required: true
        description: The Number of participants

    responses:
      200:
        description: Event updated successfully
    """
    event = Event.query.get_or_404(event_id)
    data = request.form
    event.title = data['title']
    event.location = data['location']
    event.date = datetime.fromisoformat(data['date'])
    event.participants = data['participants']
    db.session.commit()
    return jsonify({"message": "Event updated successfully"})


@app.route('/events/<int:event_id>', methods=['DELETE'])
@auth_required
def delete_event(event_id):
    """
    Delete a specific event.

    Delete a specific event using its ID.

    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: The ID of the event

    responses:
      200:
        description: Event deleted successfully
    """
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"})


@app.route('/events/location/<string:location>', methods=['GET'])
@auth_required
def get_events_by_location(location):
    """
    Retrieve events based on location.

    Get a list of events that match the specified location.

    ---
    parameters:
      - name: location
        in: path
        type: string
        required: true
        description: The location to filter events

    responses:
      200:
        description: List of events based on location
    """
    events = Event.query.filter_by(location=location).all()
    event_list = [{"id": event.id, "title": event.title, "location": event.location, "date": event.date,
                   "participants": event.participants} for event in events]
    return jsonify(event_list)


@app.route('/events/sort/<string:sort_by>', methods=['GET'])
@auth_required
def get_sorted_events(sort_by):
    """
    Retrieve sorted events.

    Get a list of events sorted by date, popularity, or creation time.

    ---
    parameters:
      - name: sort_by
        in: path
        type: string
        required: true
        enum: ["date", "popularity", "creation_time"]
        description: The criteria to sort events

    responses:
      200:
        description: List of sorted events
    """
    if sort_by == "date":
        events = Event.query.order_by(Event.date).all()
    elif sort_by == "popularity":
        events = Event.query.order_by(Event.participants.desc()).all()
    elif sort_by == "creation_time":
        events = Event.query.order_by(Event.id).all()
    else:
        return jsonify({"error": "Invalid sort criteria"}), 400

    event_list = [{"id": event.id, "title": event.title, "location": event.location, "date": event.date,
                   "participants": event.participants} for event in events]
    return jsonify(event_list)


@app.route('/events/batch', methods=['POST'])
@auth_required
def schedule_batch_events():
    """
    Schedule multiple events.

    Schedule multiple events with the provided details.

    ---
    parameters:
      - name: events
        in: body
        type: array
        required: true
        description: List of events to be scheduled
    responses:
      200:
        description: Events scheduled successfully
    """
    data = request.json
    for event_data in data['events']:
        new_event = Event(title=event_data['title'], location=event_data['location'],
                          date=datetime.fromisoformat(event_data['date']), participants=event_data['participants'])
        db.session.add(new_event)

    db.session.commit()
    return jsonify({"message": "Events scheduled successfully"})


@app.route('/events/subscribe/<int:event_id>', methods=['POST'])
@auth_required
def subscribe_to_event(event_id):
    """
    Subscribe to an event.

    Subscribe a user to receive notifications for a specific event.

    ---
    parameters:
      - name: event_id
        in: path
        type: string
        required: true
        description: ID of the event to subscribe to
    responses:
      200:
        description: Subscription successful
      404:
        description: Event or user not found
    """
    event = Event.query.get_or_404(event_id)
    user_id = get_user_id(request.headers.get('Authorization'))

    subscription = Subscription(event_id=event.id, user_id=user_id)
    db.session.add(subscription)
    db.session.commit()

    return jsonify({"message": "Subscribed successfully"})


@app.route('/events/notify/<int:event_id>', methods=['POST'])
@auth_required
def notify_subscribers(event_id):
    """
    Notify subscribers of an event.

    Send notifications to all subscribers of a specific event.

    ---
    parameters:
      - name: event_id
        in: path
        type: string
        required: true
        description: ID of the event to notify subscribers
    responses:
      200:
        description: Notifications sent successfully
      404:
        description: Event not found
      500:
        description: Internal server error
    """
    event = Event.query.get_or_404(event_id)

    socketio.emit('event_notification', {'message': 'Event updated or canceled', 'event_id': event_id})

    return jsonify({"message": "Notification sent successfully"})


@app.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user.

    Create a new user with the provided username and password.

    ---
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: The username of the new user
      - name: password
        in: formData
        type: string
        required: true
        description: The password of the new user

    responses:
      200:
        description: User created successfully
    """
    data = request.form

    # Check if the username is already taken
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"})
