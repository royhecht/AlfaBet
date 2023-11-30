from base64 import b64decode
from functools import wraps
from typing import Optional

from flask import request, jsonify

from application import limiter
from application.models import User


def auth_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not is_valid_login(auth_header):
            return jsonify({"error": "Unauthorized"}), 401

        return func(*args, **kwargs)

    return decorated_function


def is_valid_login(auth_header) -> bool:
    return get_user_id(auth_header) is not None


def get_user_id(auth_header) -> Optional[int]:
    if auth_header:
        encoded_credentials = auth_header[len('Basic '):]
        decoded_credentials = b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
        user = User.query.filter_by(username=username, password=password).first()
        return user.id if user else None


@limiter.request_filter
def rate_limit_by_api_key() -> bool:
    auth_header = request.headers.get('Authorization')
    return is_valid_login(auth_header)
