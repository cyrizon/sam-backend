# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\services\ors_service.py
import os
import requests

class ORSService:
    def __init__(self):
        # Charger l'URL de base depuis les variables d'environnement
        self.base_url = os.getenv("ORS_BASE_URL", "http://localhost:8080")

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
            response = requests.get(url, params=params, timeout=10)  # Timeout de 10 secondes
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Gérer les erreurs de connexion ou de réponse
            return {"error": str(e)}