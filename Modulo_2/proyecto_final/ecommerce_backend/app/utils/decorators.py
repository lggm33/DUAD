# app/utils/decorators.py
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError
from app.utils.exceptions import AppError, json_error


def handle_errors(operation_name: str, handle_validation: bool = False):
    """
    Decorator to handle common errors in API endpoints.
    
    Args:
        operation_name: Description of the operation for error messages
        handle_validation: Whether to handle marshmallow ValidationError
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as err:
                if handle_validation:
                    return jsonify({"errors": err.messages}), 400
                else:
                    # Re-raise if not handling validation errors
                    raise
            except AppError as err:
                return json_error(err.message, err.status)
            except Exception as e:
                print(f"Unexpected error while {operation_name}: {e}")
                return json_error(f"Unexpected error while {operation_name}", 500)
        return wrapper
    return decorator
