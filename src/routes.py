from flask import Blueprint

api_routes = Blueprint("api", __name__)

@api_routes.route("/health")
def health_check():
    return {"status": "Backend Case Study API Running"}
