"""
toll_strategies.py
-----------------

Stratégies pour calculer des itinéraires avec des contraintes sur le nombre de péages.
Utilise la stratégie intelligente de segmentation V2 avec OSM.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.new_segmentation.advanced_toll_optimizer import TollOptimizerFactory
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler


class TollRouteOptimizer:
    """
    Optimiseur d'itinéraires avec contraintes sur le nombre de péages.
    Utilise la stratégie intelligente de segmentation V2 avec OSM.
    """
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        # Utiliser la stratégie intelligente avec OSM
        self.advanced_optimizer = TollOptimizerFactory.create_optimizer(ors_service)
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE, force_segmentation=False):
        """
        Calcule un itinéraire avec une limite sur le nombre de péages.
        
        Utilise la stratégie intelligente de segmentation V2 avec OSM.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Paramètre maintenu pour compatibilité (non utilisé)
            force_segmentation: Paramètre maintenu pour compatibilité (non utilisé)
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        # Utiliser la stratégie intelligente avec OSM
        return self.advanced_optimizer.optimize_route_with_exact_tolls(
            coordinates, 
            target_tolls=max_tolls, 
            veh_class=veh_class,
            use_intelligent_strategy=True
        )