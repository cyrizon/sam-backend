"""
ors_payload_builder.py
---------------------

Constructeur centralisé pour les payloads ORS.
Responsabilité unique : assembler les requêtes ORS de manière uniforme.
"""

from src.services.ors_config_manager import ORSConfigManager


class ORSPayloadBuilder:
    """Constructeur centralisé pour les payloads ORS."""
    
    @staticmethod
    def build_base_payload(coordinates, include_tollways=True):
        """
        Construit un payload pour une route de base.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            include_tollways: Inclure les informations de péages (défaut: True)
            
        Returns:
            dict: Payload ORS
        """
        ORSConfigManager.validate_coordinates(coordinates)
        
        payload = {
            "coordinates": coordinates,
            "language": "fr"
        }
        
        if include_tollways:
            payload["extra_info"] = ["tollways"]
        
        return ORSConfigManager.optimize_payload(payload)
    
    @staticmethod
    def build_avoid_tollways_payload(coordinates):
        """
        Construit un payload pour éviter les péages.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            
        Returns:
            dict: Payload ORS
        """
        ORSConfigManager.validate_coordinates(coordinates)
        
        payload = {
            "coordinates": coordinates,
            "options": {"avoid_features": ["tollways"]},
            "extra_info": ["tollways"],
            "language": "fr"
        }
        
        return ORSConfigManager.optimize_payload(payload)
    
    @staticmethod
    def build_custom_payload(coordinates, options=None, extra_info=None):
        """
        Construit un payload personnalisé.
        
        Args:
            coordinates: Liste de coordonnées
            options: Options ORS (avoid_features, avoid_polygons, etc.)
            extra_info: Informations supplémentaires à inclure
            
        Returns:
            dict: Payload ORS
        """
        ORSConfigManager.validate_coordinates(coordinates)
        
        payload = {
            "coordinates": coordinates,
            "language": "fr"
        }
        
        if options:
            payload["options"] = options
        
        if extra_info:
            payload["extra_info"] = extra_info
        elif "tollways" not in payload.get("extra_info", []):
            # Assurer que tollways est toujours présent par défaut
            payload["extra_info"] = ["tollways"]
        
        return ORSConfigManager.optimize_payload(payload)
    
    @staticmethod
    def enhance_payload_for_tracking(payload, operation_context=None):
        """
        Enrichit un payload avec des métadonnées pour le tracking.
        
        Args:
            payload: Payload ORS de base
            operation_context: Contexte de l'opération (optionnel)
            
        Returns:
            tuple: (payload, metadata)
        """
        metadata = {
            "operation_name": ORSConfigManager.get_operation_name(payload),
            "timeout": ORSConfigManager.calculate_timeout(payload),
            "priority": ORSConfigManager.get_request_priority(payload),
            "coordinate_count": len(payload.get("coordinates", [])),
            "has_avoidance": "options" in payload
        }
        
        if operation_context:
            metadata["context"] = operation_context
        
        return payload, metadata