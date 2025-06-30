"""
ors_service.py
-------------

Service pour les appels à l'API OpenRouteService.
"""
import os
import requests
import copy
from src.services.ors_payload_builder import ORSPayloadBuilder
from src.services.ors_config_manager import ORSConfigManager
from benchmark.performance_tracker import performance_tracker

class ORSService:
    def __init__(self):
        # Charger l'URL de base depuis les variables d'environnement
        self.base_url = os.getenv("ORS_BASE_URL")
        self.directions_url = f"{self.base_url}/v2/directions/driving-car/geojson" if self.base_url else None
    
    def test_all_set(self):
        """
        Vérifie si l'URL de base est correctement configurée.
        :return: True si l'URL est configurée, sinon False
        """
        return self.base_url is not None

    def get_route(self, start, end):
        """
        Récupère un itinéraire entre deux points via ORS.
        :param start: Coordonnées de départ (ex: [longitude, latitude])
        :param end: Coordonnées d'arrivée (ex: [longitude, latitude])
        :return: JSON contenant les informations de l'itinéraire
        """
        url = f"{self.base_url}/v2/directions/driving-car"
        params = {
            "start": f"{start[0]},{start[1]}",
            "end": f"{end[0]},{end[1]}"
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
    
    def call_ors(self, payload):
        """
        Appelle l'API ORS avec un payload personnalisé complet.
        
        Args:
            payload: Dictionnaire contenant toutes les options de requête (coordinates, options, etc.)
            
        Returns:
            dict: Résultat GeoJSON de l'itinéraire
            
        Raises:
            requests.HTTPError: Si ORS retourne une erreur HTTP
        """
        if not self.directions_url:
            raise ValueError("ORS_BASE_URL n'est pas défini dans les variables d'environnement")
        
        # Calculer le timeout optimal
        timeout = ORSConfigManager.calculate_timeout(payload)
        
        # Tracking et métadonnées
        operation_name = ORSConfigManager.get_operation_name(payload)
        with performance_tracker.measure_operation(operation_name):
            performance_tracker.count_api_call(operation_name)
            
            r = requests.post(
                self.directions_url, 
                json=payload, 
                headers=ORSConfigManager.STANDARD_HEADERS, 
                timeout=timeout
            )
            r.raise_for_status()
            return r.json()
    
    def get_base_route(self, coordinates, include_tollways=True):
        """
        Récupère un itinéraire de base entre les points spécifiés.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            include_tollways: Si True, inclut l'information sur les péages
            
        Returns:
            dict: Résultat GeoJSON de l'itinéraire
        """
        payload = ORSPayloadBuilder.build_base_payload(coordinates, include_tollways)
        return self.call_ors(payload)
    
    def get_route_avoid_tollways(self, coordinates):
        """
        Récupère un itinéraire en évitant les autoroutes à péage.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            
        Returns:
            dict: Résultat GeoJSON de l'itinéraire
        """
        payload = ORSPayloadBuilder.build_avoid_tollways_payload(coordinates)
        return self.call_ors(payload)