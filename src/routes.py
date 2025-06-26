import json
import os
from flask import jsonify, request
from flask_cors import CORS
from pathlib import Path
from src.services.smart_route import SmartRouteService
from src.services.toll_locator import locate_tolls
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.services.ors_payload_builder import ORSPayloadBuilder

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

    @app.route('/api/tolls', methods=['POST', 'OPTIONS'])
    def retrieve_tolls():
        if request.method == 'OPTIONS':
            return jsonify({"message": "CORS preflight check successful"}), 200
        try:
            geojson_data = request.get_json(silent=True)
            if not geojson_data:
                print("Données GeoJSON manquantes ou invalides :", geojson_data)
                return jsonify({"error": "No data provided"}), 400

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
                    tolls_dict = locate_tolls(traj_data, buffer_m=1.0, veh_class="c1")
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
                tolls_dict = locate_tolls(geojson_data, buffer_m=1.0, veh_class="c1")
                return jsonify([tolls_dict["on_route"]])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/route/', methods=['POST'])
    def api_route_post():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        data = request.get_json()
        print("Received data:", data)
        if not data or 'coordinates' not in data:
            return jsonify({"error": "Missing coordinates"}), 400

        # Utilise le builder pour inclure "language": "fr" et demander GeoJSON
        payload = ORSPayloadBuilder.build_custom_payload(
            data['coordinates'],
            options=data.get('options')
        )
        # Demande explicitement GeoJSON
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/geo+json, application/json, application/gpx+xml, img/png; charset=utf-8",
        }
        # Utilise l'endpoint geojson d'ORS
        url = f"{ors_base_url}/v2/directions/driving-car/geojson"
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            ors_result = response.json()

            # --- Ajout du calcul de péages et coût ---
            # 1. Utilise directement la géométrie GeoJSON de la route principale
            route_geojson = None
            if (
                "features" in ors_result and
                isinstance(ors_result["features"], list) and
                len(ors_result["features"]) > 0 and
                "geometry" in ors_result["features"][0]
            ):
                route_geojson = {
                    "type": "FeatureCollection",
                    "features": [ors_result["features"][0]]
                }
            cost = None
            toll_count = None
            if route_geojson:
                tolls_dict = locate_tolls(route_geojson, buffer_m=1.0, veh_class="c1")
                from src.services.toll_cost import add_marginal_cost
                tolls = add_marginal_cost(tolls_dict["on_route"], veh_class="c1")
                cost = sum(t.get("cost", 0) for t in tolls)
                toll_count = len(tolls)
            # Réponse enrichie
            return jsonify({
                **ors_result,
                "cost": cost,
                "toll_count": toll_count
            })
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
    @limiter.limit("6 per minute")
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
    @limiter.limit("6 per minute")
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

    @app.route("/health", methods=["GET"])
    def health():
        return "OK", 200

