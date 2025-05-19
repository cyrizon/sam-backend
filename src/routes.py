# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\routes.py
import json
import os
from flask import jsonify, request
from flask_cors import CORS
from pathlib import Path
from src.services.tolls_finder import find_tolls_on_route
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

def register_routes(app):
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # Autorise uniquement le frontend

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[]
    )

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

    @app.route('/api/route', methods=['GET'])
    def api_route_get():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        url = f"{ors_base_url}/v2/directions/driving-car"
        start = request.args.get('start')
        end = request.args.get('end')
        if not start or not end:
            return jsonify({"error": "Missing start or end parameter"}), 400
        params = {"start": start, "end": end}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/route/', methods=['POST'])
    def api_route_post():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        url = f"{ors_base_url}/v2/directions/driving-car"
        data = request.get_json()
        print("Received data:", data)
        if not data or 'coordinates' not in data:
            return jsonify({"error": "Missing coordinates"}), 400

        payload = {
            "coordinates": data['coordinates']
        }
        if 'options' in data:
            payload["options"] = data['options']

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/test-ors', methods=['GET'])
    def test_ors():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        url = f"{ors_base_url}/v2/directions/driving-car"
        params = {
            # "start": "8.68149,49.4141",
            # "end": "8.68787,49.42031"
            "start": "7.448595,48.262004", #Selestat
            # "end": "7.330118,47.750059", #Mulhouse
            # "start": "7.330118,47.750059", #Mulhouse
            # "end": "7.758374,48.570721" #Strasbourg
            # "end" : "6.17963,49.115164" #Metz
            "end": "5.037793,47.317743" #Dijon
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/geocode/search', methods=['GET'])
    @limiter.limit("3 per minute")
    def geocode_search():
        api_key = os.environ.get("ORS_API_KEY")
        text = request.args.get('text')
        if not api_key or not text:
            return jsonify({"error": "Missing ORS_API_KEY or text parameter"}), 400
        url = "https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": api_key,
            "text": text,
            "boundary.country": "FR"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/geocode/autocomplete', methods=['GET'])
    @limiter.limit("3 per minute")
    def geocode_autocomplete():
        api_key = os.environ.get("ORS_API_KEY")
        text = request.args.get('text')
        if not api_key or not text:
            return jsonify({"error": "Missing ORS_API_KEY or text parameter"}), 400
        url = "https://api.openrouteservice.org/geocode/autocomplete"
        params = {
            "api_key": api_key,
            "text": text,
            "boundary.country": "FR"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500

