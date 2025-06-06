"""
common_validator.py
------------------

Validateur commun pour les contraintes de routes (toll et budget).
Responsabilité unique : centraliser les validations communes.
"""

from src.services.common.base_constants import BaseOptimizationConfig as Config
from src.services.common.common_messages import CommonMessages


class CommonRouteValidator:
    """Validateur commun pour les contraintes de routes."""
    
    @staticmethod
    def validate_coordinates(coordinates):
        """
        Valide le format et la validité des coordonnées.
        
        Args:
            coordinates: Liste de coordonnées [[lon, lat], [lon, lat]]
            
        Returns:
            bool: True si valides
            
        Raises:
            ValueError: Si les coordonnées sont invalides
        """
        if not coordinates or len(coordinates) < 2:
            raise ValueError("Au moins 2 coordonnées requises (départ et arrivée)")
        
        for i, coord in enumerate(coordinates):
            if not isinstance(coord, (list, tuple)) or len(coord) != 2:
                raise ValueError(f"Coordonnée {i}: {CommonMessages.INVALID_COORDINATE_FORMAT}")
            
            lon, lat = coord
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError(f"Coordonnée {i}: longitude et latitude doivent être numériques")
            
            # Validation des limites géographiques (approximatives)
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError(f"Coordonnée {i}: {CommonMessages.COORDINATE_OUT_OF_BOUNDS}")
        
        return True
    
    @staticmethod
    def validate_vehicle_class(veh_class):
        """
        Valide la classe de véhicule.
        
        Args:
            veh_class: Classe de véhicule (c1, c2, etc.)
            
        Returns:
            bool: True si valide
            
        Raises:
            ValueError: Si la classe est invalide
        """
        valid_classes = ["c1", "c2", "c3", "c4", "c5"]
        if veh_class not in valid_classes:
            raise ValueError(f"Classe de véhicule invalide: {veh_class}. Valides: {valid_classes}")
        return True
    
    @staticmethod
    def validate_route_data(route_data):
        """
        Valide qu'une route contient les données essentielles.
        
        Args:
            route_data: Données de route à valider
            
        Returns:
            bool: True si valides
            
        Raises:
            ValueError: Si les données sont invalides
        """
        if not route_data:
            raise ValueError("Données de route manquantes")
        
        required_fields = ["geometry", "summary"]
        for field in required_fields:
            if field not in route_data:
                raise ValueError(f"Champ requis manquant dans route_data: {field}")
        
        # Validation du résumé
        summary = route_data["summary"]
        if "distance" not in summary or "duration" not in summary:
            raise ValueError("Distance et durée requises dans le résumé de route")
        
        return True
    
    @staticmethod
    def validate_toll_count(toll_count, max_tolls=None):
        """
        Valide le nombre de péages.
        
        Args:
            toll_count: Nombre de péages
            max_tolls: Limite maximale (optionnel)
            
        Returns:
            bool: True si respecte les contraintes
        """
        if not isinstance(toll_count, int) or toll_count < 0:
            raise ValueError("Le nombre de péages doit être un entier positif ou nul")
        
        if max_tolls is not None and toll_count > max_tolls:
            return False
        
        return True
    
    @staticmethod
    def validate_cost(cost):
        """
        Valide un coût.
        
        Args:
            cost: Coût à valider
            
        Returns:
            bool: True si valide
            
        Raises:
            ValueError: Si le coût est invalide
        """
        if not isinstance(cost, (int, float)):
            raise ValueError("Le coût doit être numérique")
        
        if cost < 0:
            raise ValueError("Le coût ne peut pas être négatif")
        
        return True
    
    @staticmethod
    def validate_duration(duration):
        """
        Valide une durée.
        
        Args:
            duration: Durée à valider (en secondes)
            
        Returns:
            bool: True si valide
            
        Raises:
            ValueError: Si la durée est invalide
        """
        if not isinstance(duration, (int, float)):
            raise ValueError("La durée doit être numérique")
        
        if duration <= 0:
            raise ValueError("La durée doit être positive")
        
        return True
    
    @staticmethod
    def validate_optimization_params(max_tolls=None, max_price=None, max_price_percent=None):
        """
        Valide les paramètres d'optimisation globaux.
        
        Args:
            max_tolls: Nombre maximum de péages
            max_price: Budget maximum en euros
            max_price_percent: Budget en pourcentage
            
        Returns:
            bool: True si valides
            
        Raises:
            ValueError: Si les paramètres sont invalides
        """
        if max_tolls is not None:
            if not isinstance(max_tolls, int) or max_tolls < 0:
                raise ValueError("max_tolls doit être un entier positif ou nul")
        
        if max_price is not None:
            if not isinstance(max_price, (int, float)) or max_price < 0:
                raise ValueError("max_price doit être numérique et positif")
        
        if max_price_percent is not None:
            if not isinstance(max_price_percent, (int, float)):
                raise ValueError("max_price_percent doit être numérique")
            if not (0 <= max_price_percent <= 1):
                raise ValueError("max_price_percent doit être entre 0 et 1")
        
        return True
