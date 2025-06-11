"""
toll_strategies.py
-----------------

Stratégies simplifiées pour calculer des itinéraires avec des contraintes sur le nombre de péages.
Nouvelle approche : respect des contraintes plutôt qu'optimisation de coût.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.simple_toll_optimizer import SimpleTollOptimizer
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler


class TollRouteOptimizer:
    """
    Optimiseur d'itinéraires simplifié avec contraintes sur le nombre de péages.
    Nouvelle approche : respect des contraintes plutôt qu'optimisation complexe de coût.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.simple_optimizer = SimpleTollOptimizer(ors_service)
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
        """
        Calcule un itinéraire avec une limite sur le nombre de péages.
        
        Nouvelle approche simplifiée :
        1. Respecter la contrainte exacte (≤ max_tolls)
        2. Si pas trouvé, essayer backup (max_tolls + 1)
        3. Si toujours rien, fallback
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Paramètre maintenu pour compatibilité (non utilisé)
            
        Returns:
            dict: Résultats simplifiés (fastest, cheapest, min_tolls, status)
        """
        
        # Déléguer directement à l'optimiseur simplifié
        return self.simple_optimizer.compute_route_with_toll_limit(
            coordinates, max_tolls, veh_class
        )