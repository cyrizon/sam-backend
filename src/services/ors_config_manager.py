"""
ors_config_manager.py
--------------------

Gestionnaire centralisé pour la configuration des appels ORS.
Responsabilité unique : valider et optimiser les paramètres des requêtes ORS.
"""

from src.services.optimization.constants import TollOptimizationConfig as Config


class ORSConfigManager:
    """Gestionnaire centralisé pour la configuration ORS."""
    
    # Timeouts adaptatifs selon la complexité
    BASE_TIMEOUT = 10       # Timeout pour routes simples
    COMPLEX_TIMEOUT = 20    # Timeout pour routes avec évitement
    MAX_TIMEOUT = 30        # Timeout maximum
    
    # Headers standards pour tous les appels
    STANDARD_HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
    }
    
    @staticmethod
    def validate_coordinates(coordinates):
        """
        Valide les coordonnées avant l'appel ORS.
        
        Args:
            coordinates: Liste de coordonnées [[lon1, lat1], [lon2, lat2], ...]
            
        Returns:
            bool: True si valides, False sinon
            
        Raises:
            ValueError: Si les coordonnées sont invalides
        """
        if not coordinates or len(coordinates) < 2:
            raise ValueError("Au moins 2 coordonnées sont requises (départ et arrivée)")
        
        for i, coord in enumerate(coordinates):
            if not isinstance(coord, (list, tuple)) or len(coord) != 2:
                raise ValueError(f"Coordonnée {i} invalide: format attendu [longitude, latitude]")
            
            lon, lat = coord
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError(f"Coordonnée {i} invalide: longitude et latitude doivent être numériques")
            
            # Validation des plages géographiques
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude {lon} hors limites [-180, 180]")
            
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} hors limites [-90, 90]")
        
        return True
    
    @staticmethod
    def calculate_timeout(payload):
        """
        Calcule le timeout optimal selon la complexité de la requête.
        
        Args:
            payload: Payload de la requête ORS
            
        Returns:
            int: Timeout en secondes
        """
        timeout = ORSConfigManager.BASE_TIMEOUT
        
        # Route simple avec plus de 2 points
        coord_count = len(payload.get("coordinates", []))
        if coord_count > 2:
            timeout += (coord_count - 2) * 2
        
        # Évitement de polygones (plus complexe)
        options = payload.get("options", {})
        
        # Évitement de features (moyennement complexe)
        if "avoid_features" in options:
            timeout += 5
        
        # Extra info demandées
        extra_info = payload.get("extra_info", [])
        if extra_info:
            timeout += len(extra_info) * 2
        
        # Cap au maximum
        return min(timeout, ORSConfigManager.MAX_TIMEOUT)
    
    @staticmethod
    def get_operation_name(payload):
        """
        Détermine le nom de l'opération selon le payload.
        
        Args:
            payload: Payload de la requête ORS
            
        Returns:
            str: Nom de l'opération pour le tracking
        """
        options = payload.get("options", {})
        
        if "avoid_features" in options:
            return "ORS_avoid_tollways"
        else:
            return "ORS_base_route"
    
    @staticmethod
    def optimize_payload(payload):
        """
        Optimise le payload pour de meilleures performances.
        
        Args:
            payload: Payload original
            
        Returns:
            dict: Payload optimisé
        """
        optimized = payload.copy()

        # Désactiver l'élévation pour optimiser la performance
        optimized["elevation"] = False
        
        # Assurer que extra_info est présent pour les péages
        if "extra_info" not in optimized:
            optimized["extra_info"] = ["tollways"]
        elif "tollways" not in optimized["extra_info"]:
            optimized["extra_info"].append("tollways")
        
        # Optimisation des options
        if "options" in optimized:
            options = optimized["options"]
            
            # Nettoyer les options vides
            if not options:
                del optimized["options"]
            else:
                # Supprimer les clés avec des valeurs vides/nulles
                optimized["options"] = {k: v for k, v in options.items() if v}
        
        return optimized
    
    @staticmethod
    def get_request_priority(payload):
        """
        Détermine la priorité de la requête pour l'ordonnancement.
        
        Args:
            payload: Payload de la requête
            
        Returns:
            str: 'high', 'medium', 'low'
        """
        options = payload.get("options", {})
        
        # Routes simples = priorité haute
        if not options:
            return "high"
        
        # Évitement de features = priorité moyenne
        if "avoid_features" in options and len(options) == 1:
            return "medium"
        
        # Évitement de polygones = priorité basse (plus complexe)
        return "low"