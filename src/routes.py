import json
import os
from flask import jsonify, request
from flask_cors import CORS
from pathlib import Path
from src.services.tolls_finder import find_tolls_on_route
from src.services.smart_route import SmartRouteService
from src.services.toll_locator import locate_tolls
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


load_dotenv()

# Initialisation du service de routage intelligent
smart_route_service = SmartRouteService()

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
            geojson_data = request.get_json(silent=True)
            if not geojson_data:
                print("Données GeoJSON manquantes ou invalides :", geojson_data)
                return jsonify({"error": "No data provided"}), 400

            csv_path = os.path.join(os.path.dirname(__file__), "../data/barriers.csv")
            if not os.path.exists(csv_path):
                print("Fichier CSV des péages introuvable :", csv_path)
                return jsonify({"error": "CSV file not found"}), 404

            # Si c'est une liste, on traite chaque trajet séparément
            if isinstance(geojson_data, list):
                results = []
                for traj in geojson_data:
                    # Normalisation du format
                    if traj.get("type") == "FeatureCollection":
                        traj_data = traj
                    elif traj.get("type") == "Feature":
                        traj_data = {"type": "FeatureCollection", "features": [traj]}
                    else:
                        continue  # Ignore format inconnu
                    tolls_dict = locate_tolls(traj_data, csv_path, buffer_m=120)
                    # Tu peux choisir de retourner on_route ou les deux listes
                    results.append(tolls_dict["on_route"])
                return jsonify(results)
            else:
                # Cas unique
                if geojson_data.get("type") == "FeatureCollection":
                    geojson_data = geojson_data
                elif geojson_data.get("type") == "Feature":
                    geojson_data = {"type": "FeatureCollection", "features": [geojson_data]}
                else:
                    return jsonify({"error": "Invalid GeoJSON format"}), 400
                tolls_dict = locate_tolls(geojson_data, csv_path, buffer_m=120)
                return jsonify([tolls_dict["on_route"]])
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
        
    @app.route('/api/test-ors-post', methods=['POST'])
    def test_ors_post():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        url = f"{ors_base_url}/v2/directions/driving-car"
        # Exemple de données pour tester l'API ORS en POST
        data = {
            "coordinates": [
            [7.448595, 48.262004],  # Sélestat
            [5.037793, 47.317743]   # Dijon
            ],
            "options": {
                "avoid_polygons": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [6.980495693677426, 47.67687393097131],
                        [6.980495693677426, 47.675166068437846],
                        [6.982838471592885, 47.675166068437846],
                        [6.982838471592885, 47.67687393097131],
                        [6.980495693677426, 47.67687393097131]
                    ]
                    ]
                }
            }
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500    
        
    @app.route('/api/smart-route/tolls', methods=['POST'])
    def smart_route_tolls():
        data = request.get_json()
        coords = data.get("coordinates")
        max_tolls = int(data.get("max_tolls", 99))
        veh_class = data.get("vehicle_class", "c1")
        try:
            res = smart_route_service.compute_route_with_toll_limit(coords, max_tolls, veh_class)
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500    
        
    @app.route('/api/smart-route/budget', methods=['POST'])
    def smart_route_budget():
        data = request.get_json()
        coords = data.get("coordinates")
        veh_class = data.get("vehicle_class", "c1")
        max_price = data.get("max_price")
        max_price_percent = data.get("max_price_percent")
        try:
            res = smart_route_service.compute_route_with_budget_limit(
                coords,
                max_price=max_price,
                max_price_percent=max_price_percent,
                veh_class=veh_class
            )
            return jsonify(res)
        except Exception as e:
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

