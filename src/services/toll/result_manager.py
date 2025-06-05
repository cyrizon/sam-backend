"""
result_manager.py
----------------

Gestionnaire pour comparer et sélectionner les meilleurs itinéraires.
Responsabilité unique : gérer les critères d'optimisation (coût, durée, nombre de péages).
"""

from src.services.common.result_formatter import ResultFormatter
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.common.toll_messages import TollMessages


class RouteResultManager:
    """
    Gestionnaire pour les résultats d'optimisation d'itinéraires.
    Maintient et met à jour les meilleures solutions selon différents critères.
    """
    
    def __init__(self):
        """Initialise le gestionnaire avec des résultats vides."""
        self.reset()
    
    def reset(self):
        """Remet à zéro tous les résultats suivis."""
        self.best_cheap = self._create_empty_result()
        self.best_fast = self._create_empty_result()
        self.best_min_tolls = self._create_empty_result()
    
    def _create_empty_result(self):
        """Crée une structure de résultat vide."""
        return {
            "route": None,
            "cost": float('inf'),
            "duration": float('inf'),
            "toll_count": float('inf')
        }
    
    def initialize_with_base_route(self, base_route, base_cost, base_duration, base_toll_count, max_tolls):
        """
        Initialise les résultats avec la route de base si elle respecte les contraintes.
        
        Args:
            base_route: Route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base
            base_toll_count: Nombre de péages de la route de base
            max_tolls: Nombre maximum de péages autorisés
        """
        if base_toll_count <= max_tolls:
            base_result = ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
            self.best_cheap = base_result.copy()
            self.best_fast = base_result.copy()
            self.best_min_tolls = base_result.copy()
    
    def update_with_route(self, route_data, base_cost):
        """
        Met à jour les meilleurs résultats avec un nouveau candidat d'itinéraire.
        
        Args:
            route_data: Données de l'itinéraire (doit contenir cost, duration, toll_count)
            base_cost: Coût de la route de base pour comparaison
            
        Returns:
            bool: True si au moins un résultat a été mis à jour
        """
        cost = route_data["cost"]
        duration = route_data["duration"]
        toll_count = route_data["toll_count"]
        
        updated = False
        
        # Mise à jour de l'itinéraire avec le moins de péages
        if toll_count < self.best_min_tolls["toll_count"]:
            self.best_min_tolls = route_data.copy()
            updated = True
        
        # Mise à jour de l'itinéraire le moins cher
        if cost < self.best_cheap["cost"]:
            self.best_cheap = route_data.copy()
            updated = True
          # Mise à jour du plus rapide (priorité à la durée plus faible, puis au coût)
        if (duration < self.best_fast["duration"] or 
            (duration == self.best_fast["duration"] and cost < self.best_fast["cost"]) or
            self.best_fast["route"] is None):
            self.best_fast = route_data.copy()
            updated = True
        
        return updated
    
    def apply_fallback_if_needed(self, base_route, base_cost, base_duration, base_toll_count, max_tolls):
        """
        Applique la route de base comme solution de repli si nécessaire.
        
        Args:
            base_route: Route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base
            base_toll_count: Nombre de péages de la route de base
            max_tolls: Nombre maximum de péages autorisés
        """
        if base_toll_count <= max_tolls:
            base_result = ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
            
            if self.best_fast["route"] is None:
                self.best_fast = base_result.copy()
                
            if self.best_cheap["route"] is None:
                self.best_cheap = base_result.copy()
                
            if self.best_min_tolls["route"] is None:
                self.best_min_tolls = base_result.copy()
    
    def get_results(self):
        """
        Retourne les résultats finaux dans le format attendu.
        
        Returns:
            dict: Dictionnaire avec fastest, cheapest, min_tolls
        """
        # CORRECTION: Retourner des copies pour éviter les modifications accidentelles
        return {
            "fastest": self.best_fast.copy() if self.best_fast["route"] is not None else None,
            "cheapest": self.best_cheap.copy() if self.best_cheap["route"] is not None else None,
            "min_tolls": self.best_min_tolls.copy() if self.best_min_tolls["route"] is not None else None
        }
    
    def has_valid_results(self):
        """
        Vérifie si au moins un résultat valide a été trouvé.
        
        Returns:
            bool: True si au moins une solution existe
        """
        return (self.best_fast["route"] is not None or 
                self.best_cheap["route"] is not None or 
                self.best_min_tolls["route"] is not None)
    
    def log_results(self, base_toll_count, base_cost, base_duration):
        """
        Affiche un résumé des résultats finaux.
        
        Args:
            base_toll_count: Nombre de péages de la route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base        """
        print(TollMessages.RESULT_BASE.format(
            toll_count=base_toll_count, 
            cost=base_cost, 
            duration=base_duration/60
        ))
        
        if self.best_cheap["route"]:            print(TollMessages.RESULT_CHEAPEST.format(
                toll_count=self.best_cheap['toll_count'], 
                cost=self.best_cheap['cost'], 
                duration=self.best_cheap['duration']/60
            ))
        else:
            print(TollMessages.NO_ECONOMIC_ROUTE)
            
        if self.best_fast["route"]:            print(TollMessages.RESULT_FASTEST.format(
                toll_count=self.best_fast['toll_count'], 
                cost=self.best_fast['cost'], 
                duration=self.best_fast['duration']/60
            ))
        else:
            print(TollMessages.NO_FAST_ROUTE)
            
        if self.best_min_tolls["route"]:            print(TollMessages.RESULT_MIN_TOLLS.format(
                toll_count=self.best_min_tolls['toll_count'], 
                cost=self.best_min_tolls['cost'], 
                duration=self.best_min_tolls['duration']/60
            ))
        else:
            print(TollMessages.NO_MIN_TOLLS_ROUTE)
    
    @classmethod
    def create_uniform_result(cls, route_result, status):
        """
        Crée un résultat uniforme à partir d'une seule route.
        Utile pour les stratégies qui n'ont qu'une solution.
        
        Args:
            route_result: Résultat d'une route formatée
            status: Statut à attacher
            
        Returns:
            dict: Résultat uniforme avec status
        """
        return ResultFormatter.format_uniform_result(route_result, status)