"""
toll_strategies.py
-----------------

Stratégies pour calculer des itinéraires avec des contraintes sur le nombre de péages.
Intègre le système de mesure des performances pour optimiser les appels.
"""

import copy
import requests
from itertools import combinations
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from src.utils.route_utils import is_toll_open_system, merge_routes, format_route_result
from benchmark.performance_tracker import performance_tracker
from src.services.toll.no_toll_strategy import NoTollStrategy
from src.services.toll.fallback_strategy import FallbackStrategy
from src.services.toll.one_open_toll_strategy import OneOpenTollStrategy
from src.services.toll.many_tolls_strategy import ManyTollsStrategy

class TollRouteOptimizer:
    """
    Optimiseur d'itinéraires avec contraintes sur le nombre de péages.
    Intègre le tracking des performances pour analyser et optimiser les appels.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.no_toll_strategy = NoTollStrategy(ors_service)
        self.fallback_strategy = FallbackStrategy(ors_service)
        self.one_open_toll_strategy = OneOpenTollStrategy(ors_service)
        self.many_tolls_strategy = ManyTollsStrategy(ors_service)  # Ajouter cette ligne
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class="c1", max_comb_size=2):
        """
        Calcule un itinéraire avec une limite sur le nombre de péages.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        with performance_tracker.measure_operation("compute_route_with_toll_limit", {
            "max_tolls": max_tolls,
            "veh_class": veh_class,
            "max_comb_size": max_comb_size
        }):
            print(f"=== Calcul d'itinéraire avec un maximum de {max_tolls} péages ===")
            
            # Cas spécial 1: Aucun péage autorisé
            if max_tolls == 0:
                return self._handle_no_toll_route(coordinates, veh_class)
                
            # Cas spécial 2: Un seul péage autorisé
            elif max_tolls == 1:
                return self._handle_one_toll_route(coordinates, veh_class, max_comb_size)
                
            # Cas général: Plusieurs péages autorisés
            else:
                result = self.many_tolls_strategy.compute_route_with_many_tolls(coordinates, max_tolls, veh_class, max_comb_size)
                
                if result:
                    result["status"] = "MULTI_TOLL_SUCCESS"
                    return result
                else:
                    # Fallback avec la route de base
                    return self._get_fallback_route(coordinates, veh_class, "NO_VALID_ROUTE_WITH_MAX_TOLLS")
    
    def _handle_no_toll_route(self, coordinates, veh_class):
        """Délègue à la stratégie spécialisée"""
        return self.no_toll_strategy.handle_no_toll_route(coordinates, veh_class)

    def _handle_one_toll_route(self, coordinates, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée"""
        return self.one_open_toll_strategy.handle_one_toll_route(coordinates, veh_class, max_comb_size)

    def _get_fallback_route(self, coordinates, veh_class, status):
        """Délègue à la stratégie de fallback"""
        return self.fallback_strategy.get_fallback_route(coordinates, veh_class, status)