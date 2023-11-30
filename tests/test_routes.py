import json
from datetime import datetime
from unittest.mock import patch

import pytest

from application import app, db

TEST_DATA = {'title': 'Test Event', 'location': 'Test Location', 'date': '2023-12-01T12:00:00', 'participants': 10}


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def convert_date(original_date_string):
    original_date = datetime.strptime(original_date_string, '%a, %d %b %Y %H:%M:%S %Z')
    return original_date.strftime('%Y-%m-%dT%H:%M:%S')


def convert_date_for_row(result: dict):
    result["date"] = convert_date(result["date"])
    return result


def test_schedule_event_with_mocked_auth_required(client):
    with patch('application.auth.is_valid_login', return_value=True):
        response = client.post('/events', data=TEST_DATA)
        assert response.status_code == 200
        assert json.loads(response.data) == {"message": "Event scheduled successfully"}


def test_get_event(client):
    with patch('application.auth.is_valid_login', return_value=True):
        client.post('/events', data=TEST_DATA)
        response = client.get('/events/1')
        assert response.status_code == 200
        result = convert_date_for_row(json.loads(response.data))
        assert result == {"id": 1, **TEST_DATA}


def test_update_event(client):
    with patch('application.auth.is_valid_login', return_value=True):
        client.post('/events', data=TEST_DATA)
        response = client.put('/events/1',
                              data={'title': 'Updated Event', 'location': 'Updated Location',
                                    'date': '2023-12-02T14:00:00',
                                    'participants': 15})
        assert response.status_code == 200
        assert json.loads(response.data) == {"message": "Event updated successfully"}
        updated_event_response = client.get('/events/1')
        result = convert_date_for_row(json.loads(updated_event_response.data))
        assert result == {"id": 1, "title": "Updated Event",
                          "location": "Updated Location", "date": "2023-12-02T14:00:00",
                          "participants": 15}


def test_delete_event(client):
    with patch('application.auth.is_valid_login', return_value=True):
        client.post('/events', data=TEST_DATA)
        response = client.delete('/events/1')
        assert response.status_code == 200
        assert json.loads(response.data) == {"message": "Event deleted successfully"}
        deleted_event_response = client.get('/events/1')
        assert deleted_event_response.status_code == 404


def test_get_events_by_location(client):
    with patch('application.auth.is_valid_login', return_value=True):
        client.post('/events', data=TEST_DATA)
        response = client.get('/events/location/Test Location')
        assert response.status_code == 200
        result = [convert_date_for_row(x) for x in json.loads(response.data)]
        assert result == [{"id": 1, **TEST_DATA}]


def test_get_sorted_events(client):
    with patch('application.auth.is_valid_login', return_value=True):
        test_events = [{"id": 1, "title": "Event 1", "location": "Location 1", "date": "2023-12-02T14:00:00",
                        "participants": 15},
                       {"id": 2, "title": "Event 2", "location": "Location 2", "date": "2023-12-01T12:00:00",
                        "participants": 10},
                       {"id": 3, "title": "Event 3", "location": "Location 3", "date": "2023-12-03T16:00:00",
                        "participants": 20}]
        events_data = {"events": test_events}
        client.post('/events/batch', json=events_data)
        response = client.get('/events/sort/date')
        assert response.status_code == 200

        expected_sorted_events = sorted(test_events, key=lambda x: x['date'])

        sorted_events = [convert_date_for_row(x) for x in json.loads(response.data)]
        assert sorted_events == expected_sorted_events


def test_schedule_batch_events(client):
    with patch('application.auth.is_valid_login', return_value=True):
        test_events = [{"title": "Batch Event 1", "location": "Batch Location 1", "date": "2023-12-03T10:00:00",
                        "participants": 20},
                       {"title": "Batch Event 2", "location": "Batch Location 2", "date": "2023-12-04T15:00:00",
                        "participants": 25}]
        events_data = {"events": test_events}
        response = client.post('/events/batch', json=events_data)
        assert response.status_code == 200
        assert json.loads(response.data) == {"message": "Events scheduled successfully"}
