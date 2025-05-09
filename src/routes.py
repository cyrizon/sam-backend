# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\routes.py
from flask import jsonify
from flask_cors import CORS
import json
import os

def register_routes(app):
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # Autorise uniquement le frontend

    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the Flask API!"})

    @app.route('/api/hello', methods=['GET'])
    def hello_world():
        return jsonify({"message": "Hello, World!"})
    
    @app.route('/api/mokeroute', methods=['GET'])
    def moke_route():
        # Récupérer selestat_lyon.json et le renvoyer
        file_path = os.path.join(os.path.dirname(__file__), "../data/selestat_lyon.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
            return jsonify(data)
        else:
            return jsonify({"error": "File not found"}), 404