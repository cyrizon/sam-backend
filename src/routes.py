import json
import os
from flask import jsonify, request, current_app
from flask_cors import CORS
from pathlib import Path
from src.services.smart_route import SmartRouteService
from src.services.optimization.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.optimization.route_optimization.utils.cache_accessor import CacheAccessor
import requests
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.services.ors_payload_builder import ORSPayloadBuilder

load_dotenv()

# Initialisation du service de routage intelligent
smart_route_service = SmartRouteService()

def calculate_route_cost(tolls_on_route):
    """
    Calcule le coût total d'une route en utilisant les péages identifiés.
    
    Args:
        tolls_on_route: Liste des péages sur la route
        
    Returns:
        Coût total en euros
    """
    try:
        if not tolls_on_route:
            return 0.0
        
        # Extraire les objets TollBoothStation
        toll_stations = []
        for toll_data in tolls_on_route:
            if isinstance(toll_data, dict) and 'toll' in toll_data:
                toll_station = toll_data['toll']
                if hasattr(toll_station, 'osm_id') and hasattr(toll_station, 'name'):
                    toll_stations.append(toll_station)
        
        if len(toll_stations) < 2:
            print(f"   ⚠️ Moins de 2 péages ({len(toll_stations)}) - pas de calcul possible")
            return 0.0
        
        # Calcul par binômes consécutifs
        total_cost = 0.0
        vehicle_category = "1"  # Catégorie standard
        
        for i in range(len(toll_stations) - 1):
            toll_from = toll_stations[i]
            toll_to = toll_stations[i + 1]
            
            cost = CacheAccessor.calculate_toll_cost(toll_from, toll_to, vehicle_category)
            if cost is not None:
                total_cost += cost
                print(f"   💳 {toll_from.name} → {toll_to.name}: {cost}€")
            else:
                print(f"   ⚠️ Coût non trouvé: {toll_from.name} → {toll_to.name}")
        
        return round(total_cost, 2)
        
    except Exception as e:
        print(f"   ❌ Erreur calcul coût route: {e}")
        return 0.0

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

            # Cas spécial : le frontend envoie souvent [FeatureCollection] (array avec un seul élément)
            if isinstance(geojson_data, list) and len(geojson_data) == 1:
                geojson_data = geojson_data[0]  # Extraire le FeatureCollection du tableau

            # Si c'est encore une liste (vraiment plusieurs trajets), traiter séparément
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
                    
                    # Extraire les coordonnées et utiliser TollIdentifier comme dans intelligent_optimizer
                    coordinates = []
                    if traj_data.get("features") and traj_data["features"][0].get("geometry", {}).get("type") == "LineString":
                        coordinates = traj_data["features"][0]["geometry"]["coordinates"]
                    
                    if coordinates:
                        toll_identifier = TollIdentifier()
                        identification_result = toll_identifier.identify_tolls_on_route(coordinates)
                        tolls_on_route = identification_result.get('tolls_on_route', [])
                        
                        # Formater les péages pour ce trajet
                        formatted_tolls = []
                        for toll_data in tolls_on_route:
                            toll_station = toll_data.get('toll')
                            if toll_station:
                                toll_info = {
                                    'id': toll_station.osm_id,
                                    'nom': toll_station.display_name,
                                    'operator': toll_station.operator or "Inconnu",
                                    'autoroute': toll_station.highway_ref or "",
                                    'latitude': toll_station.coordinates[1],
                                    'longitude': toll_station.coordinates[0],
                                    'type': 'ouvert' if toll_station.is_open_toll else 'fermé',
                                    'distance_route': toll_data.get('distance', 0)
                                }
                                formatted_tolls.append(toll_info)
                        results.append(formatted_tolls)
                    else:
                        results.append([])
                return jsonify(results)
            else:
                # Cas unique
                if geojson_data.get("type") == "FeatureCollection":
                    geojson_data = geojson_data
                elif geojson_data.get("type") == "Feature":
                    geojson_data = {"type": "FeatureCollection", "features": [geojson_data]}
                else:
                    return jsonify({"error": "Invalid GeoJSON format"}), 400
                
                # Extraire les coordonnées et utiliser TollIdentifier
                coordinates = []
                if geojson_data.get("features") and geojson_data["features"][0].get("geometry", {}).get("type") == "LineString":
                    coordinates = geojson_data["features"][0]["geometry"]["coordinates"]
                
                if coordinates:
                    toll_identifier = TollIdentifier()
                    identification_result = toll_identifier.identify_tolls_on_route(coordinates)
                    tolls_on_route = identification_result.get('tolls_on_route', [])
                    
                    # Extraire et formater les données des péages pour le frontend
                    result = []
                    for toll_data in tolls_on_route:
                        toll_station = toll_data.get('toll')  # L'objet TollBoothStation
                        if toll_station:
                            toll_info = {
                                'id': toll_station.osm_id,
                                'nom': toll_station.display_name,
                                'operator': toll_station.operator or "Inconnu",
                                'autoroute': toll_station.highway_ref or "",
                                'latitude': toll_station.coordinates[1],  # lat
                                'longitude': toll_station.coordinates[0], # lon
                                'type': 'ouvert' if toll_station.is_open_toll else 'fermé',
                                'distance_route': toll_data.get('distance', 0)  # Distance à la route
                            }
                            result.append(toll_info)
                    
                    for toll in result:
                        print(f"Formatted toll: {toll}")
                else:
                    result = []

                print("Tolls identified:", result)
                
                return jsonify(result)  # Retourner directement la liste des péages
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/route/', methods=['POST'])
    def api_route_post():
        ors_base_url = os.environ.get("ORS_BASE_URL")
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "No data provided"}), 410
        print("Received data:", data)
        if not data['coordinates']:
            return jsonify({"error": "Missing coordinates"}), 411

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
            
            cost = 0.0
            toll_count = 0
            
            if route_geojson:
                # Extraire les coordonnées et utiliser TollIdentifier
                coordinates = []
                if route_geojson.get("features") and route_geojson["features"][0].get("geometry", {}).get("type") == "LineString":
                    coordinates = route_geojson["features"][0]["geometry"]["coordinates"]
                
                if coordinates:
                    toll_identifier = TollIdentifier()
                    identification_result = toll_identifier.identify_tolls_on_route(coordinates)
                    tolls_on_route = identification_result.get('tolls_on_route', [])
                    toll_count = len(tolls_on_route)
                    
                    # Calculer le coût réel en utilisant CacheAccessor
                    if toll_count >= 2:
                        # Pour 2 péages ou plus, calculer le coût entre les couples
                        cost = calculate_route_cost(tolls_on_route)
                        print(f"✅ Route de base - Péages: {toll_count}, Coût: {cost}€")
                    elif toll_count == 1:
                        # Pour 1 seul péage, le coût est 0 (pas de segment fermé)
                        cost = 0.0
                        print(f"✅ Route de base - 1 péage unique, Coût: 0€")
                    else:
                        # Aucun péage
                        cost = 0.0
                        print(f"✅ Route de base - Aucun péage, Coût: 0€")
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

