from flask import Blueprint

# Create blueprint for basic endpoints
basic_bp = Blueprint('basic', __name__)

@basic_bp.route("/")
def root():
    return "<h1>Hello, World!</h1>"

@basic_bp.route("/liveness")
def liveness():
    return "<p>Hello, World!</p>"
