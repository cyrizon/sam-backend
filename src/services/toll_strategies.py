"""
toll_strategies.py
-----------------

Stratégies pour calculer des itinéraires avec des contraintes sur le nombre de péages.
Intègre le système de mesure des performances pour optimiser les appels.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.no_toll_strategy import NoTollStrategy
from src.services.toll.fallback_strategy import TollFallbackStrategy
from src.services.toll.one_open_toll_strategy import OneOpenTollStrategy
from src.services.toll.many_tolls_strategy import ManyTollsStrategy
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler

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
        self.fallback_strategy = TollFallbackStrategy(ors_service)
        self.one_open_toll_strategy = OneOpenTollStrategy(ors_service)
        self.many_tolls_strategy = ManyTollsStrategy(ors_service)
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
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
        
        # Log du début de l'opération
        TollErrorHandler.log_operation_start(
            "compute_route_with_toll_limit",
            max_tolls=max_tolls,
            veh_class=veh_class,
            max_comb_size=max_comb_size
        )
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_WITH_TOLL_LIMIT, {
            "max_tolls": max_tolls,
            "veh_class": veh_class,
            "max_comb_size": max_comb_size
        }):
            print(f"=== Calcul d'itinéraire avec un maximum de {max_tolls} péages ===")
            
            try:                
                # Cas spécial 1: Aucun péage autorisé
                if max_tolls == 0:
                    result = self._handle_no_toll_route(coordinates, veh_class)
                # Cas spécial 2: Un seul péage autorisé
                elif max_tolls == 1:
                    result = self._handle_one_toll_route(coordinates, veh_class, max_comb_size)
                # Cas général: Plusieurs péages autorisés
                else:
                    result = self.many_tolls_strategy.compute_route_with_many_tolls(
                        coordinates, max_tolls, veh_class, max_comb_size
                    )
                
                # Fallback automatique si échec ou si statut indique que le fallback est nécessaire
                if not result or self._should_trigger_fallback(result):
                    # Essayer d'extraire les données de route de base du résultat de la stratégie
                    base_data = self._extract_base_route_data_from_result(result)
                    result = self._handle_strategy_failure_with_base_data(
                        coordinates, max_tolls, veh_class, base_data
                    )
                # Log du succès
                if result and result.get("status"):
                    TollErrorHandler.log_operation_success(
                        "compute_route_with_toll_limit",
                        f"Status: {result['status']}"
                    )
                
                return result
            except Exception as e:
                TollErrorHandler.log_operation_failure("compute_route_with_toll_limit", str(e))
                return self._handle_critical_failure(coordinates, max_tolls, veh_class, str(e))
    
    def _handle_no_toll_route(self, coordinates, veh_class):
        """Délègue à la stratégie spécialisée"""
        return self.no_toll_strategy.handle_no_toll_route(coordinates, veh_class)

    def _handle_one_toll_route(self, coordinates, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée"""
        return self.one_open_toll_strategy.handle_one_toll_route(coordinates, veh_class, max_comb_size)

    def _get_fallback_route(self, coordinates, veh_class, status):
        """Délègue à la stratégie de fallback"""
        # Déterminer max_tolls en fonction du statut (approximation)
        max_tolls = 0
        if "ONE_TOLL" in status:
            max_tolls = 1
        elif "MANY_TOLLS" in status or "MAX_TOLLS" in status:
            max_tolls = 2  # Valeur par défaut
        
        return self.fallback_strategy.handle_toll_failure(coordinates, max_tolls, veh_class=veh_class)
    
    def _should_trigger_fallback(self, result):
        """Détermine si le fallback doit être déclenché selon le statut du résultat."""
        if not result:
            return True
        
        # Statuts qui indiquent un échec nécessitant un fallback
        failure_statuses = {
            Config.StatusCodes.NO_VALID_ROUTE_WITH_MAX_TOLLS,
            Config.StatusCodes.NO_VALID_ROUTE_WITH_MAX_ONE_TOLL,
            Config.StatusCodes.NO_VALID_OPEN_TOLL_ROUTE,
            Config.StatusCodes.NO_ALTERNATIVE_FOUND
        }
        
        return result.get("status") in failure_statuses
    
    def _extract_base_route_data_from_result(self, result):
        """Extrait les données de route de base d'un résultat de stratégie."""
        if not result:
            return None
        
        # Essayer d'extraire depuis fastest, cheapest ou min_tolls
        for route_type in ["fastest", "cheapest", "min_tolls"]:
            route_data = result.get(route_type)
            if route_data and route_data.get("route"):
                return {
                    "base_route": route_data.get("route"),
                    "base_cost": route_data.get("cost"),
                    "base_duration": route_data.get("duration"),
                    "base_toll_count": route_data.get("toll_count")
                }
        
        return None
    
    def _handle_strategy_failure_with_base_data(self, coordinates, max_tolls, veh_class, base_data):
        """Gère l'échec des stratégies avec données de base optionnelles."""
        # Utiliser les données de base si disponibles, sinon calculer
        if base_data:
            print(f"📋 Utilisation des données de route de base extraites du résultat de stratégie")
            return self.fallback_strategy.handle_toll_failure(
                coordinates, max_tolls,
                base_route=base_data.get("base_route"),
                base_cost=base_data.get("base_cost"),
                base_duration=base_data.get("base_duration"),
                base_toll_count=base_data.get("base_toll_count"),
                veh_class=veh_class
            )
        else:
            # Fallback vers l'ancienne méthode si pas de données de base
            return self._handle_strategy_failure(coordinates, max_tolls, veh_class)
    
    def _handle_strategy_failure(self, coordinates, max_tolls, veh_class):
        """Gère l'échec des stratégies principales avec fallback."""
        # Calcul de la route de base pour éviter de la recalculer dans le fallback
        try:
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
            
            # Essayer de calculer la route de base une seule fois
            base_route = self.many_tolls_strategy.route_calculator.get_base_route_with_tracking(coordinates)
            if base_route:
                # Calculer les métriques de base
                tolls_dict = self.many_tolls_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                base_toll_count = len(tolls_on_route)
                
                print(f"📋 Route de base calculée pour fallback: {base_cost}€, {base_toll_count} péage(s)")
        except Exception as e:
            print(f"⚠️  Impossible de calculer la route de base pour le fallback: {e}")
        
        return self.fallback_strategy.handle_toll_failure(
            coordinates, max_tolls, 
            base_route=base_route, base_cost=base_cost, 
            base_duration=base_duration, base_toll_count=base_toll_count,
            veh_class=veh_class
        )
    
    def _handle_critical_failure(self, coordinates, max_tolls, veh_class, error_message):
        """Gère les erreurs critiques avec fallback ultime."""
        try:
            # Essayer de calculer la route de base pour le fallback même en cas d'erreur critique
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
            
            try:
                base_route = self.many_tolls_strategy.route_calculator.get_base_route_with_tracking(coordinates)
                if base_route:
                    tolls_dict = self.many_tolls_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                    tolls_on_route = tolls_dict["on_route"]
                    
                    base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                    base_toll_count = len(tolls_on_route)
                    
                    print(f"📋 Route de base calculée pour fallback critique: {base_cost}€, {base_toll_count} péage(s)")
            except Exception as base_error:
                print(f"⚠️  Impossible de calculer la route de base pour le fallback critique: {base_error}")
            
            return self.fallback_strategy.handle_toll_failure(
                coordinates, max_tolls, 
                base_route=base_route, base_cost=base_cost,
                base_duration=base_duration, base_toll_count=base_toll_count,
                veh_class=veh_class
            )
        except Exception:
            # Fallback ultime - route de base avec statut d'erreur critique
            return {
                "fastest": None,
                "cheapest": None,
                "min_tolls": None,
                "status": Config.StatusCodes.CRITICAL_ERROR,
                "error": error_message
            }