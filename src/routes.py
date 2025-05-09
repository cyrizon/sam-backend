# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\routes.py
import json
import os
from flask import jsonify, request
from flask_cors import CORS
from pathlib import Path
from src.services.tolls_finder import find_tolls_on_route

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

    @app.route('/api/tolls', methods=['POST', 'OPTIONS'])
    def retrieve_tolls():
        if request.method == 'OPTIONS':
            return jsonify({"message": "CORS preflight check successful"}), 200
        try:
            # Récupérer les données GeoJSON envoyées par le frontend
            geojson_data = request.get_json()
            if not geojson_data:
                print("Données GeoJSON manquantes ou invalides :", geojson_data)
                return jsonify({"error": "No data provided"}), 400

            # Chemin vers le fichier CSV des péages
            csv_path = os.path.join(os.path.dirname(__file__), "../data/gares-peage-2024-with-id.csv")
            if not os.path.exists(csv_path):
                print("Fichier CSV des péages introuvable :", csv_path)
                return jsonify({"error": "CSV file not found"}), 404

            # Utiliser l'algorithme pour trouver les péages
            tolls = find_tolls_on_route(geojson_data, csv_path, distance_threshold=100)

            # Retourner les péages trouvés
            return jsonify(tolls)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

