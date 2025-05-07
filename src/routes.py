# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\routes.py
from flask import jsonify
from flask_cors import CORS

def register_routes(app):
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # Autorise uniquement le frontend

    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the Flask API!"})

    @app.route('/api/hello', methods=['GET'])
    def hello_world():
        return jsonify({"message": "Hello, World!"})