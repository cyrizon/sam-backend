# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\services\ors_service.py
import os
import requests

class ORSService:
    def __init__(self):
        # Charger l'URL de base depuis les variables d'environnement
        self.base_url = os.getenv("ORS_BASE_URL")
    
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