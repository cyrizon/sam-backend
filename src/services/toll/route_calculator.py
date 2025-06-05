"""
route_calculator.py
------------------

Utilitaires pour calculer des routes avec contraintes de péages.
Responsabilité unique : gérer la logique de calcul et d'évitement des péages.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from benchmark.performance_tracker import performance_tracker
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.route_validator import RouteValidator
from src.services.toll.exceptions import ORSConnectionError, RouteCalculationError
from src.services.toll.error_handler import ErrorHandler
from src.services.ors_payload_builder import ORSPayloadBuilder


class RouteCalculator:
    """Utilitaires pour calculer des routes avec contraintes de péages."""
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
    
    def calculate_route_avoiding_unwanted_tolls(self, coordinates, target_toll_id, part_name):
        """
        Calcule une route en évitant tous les péages sauf le péage cible.
        
        Args:
            coordinates: Coordonnées de la partie [départ, arrivée]
            target_toll_id: ID du péage cible à conserver
            part_name: Nom de la partie pour le logging
            
        Returns:
            dict: {"route": route_data, "tolls": tolls_list} ou None si échec
        """
        try:
            # Premier appel avec payload optimisé
            base_payload = ORSPayloadBuilder.build_base_payload(coordinates, include_tollways=True)
            route = self._call_ors_with_tracking(base_payload, f"ORS_{part_name}_route")
            tolls = self._locate_tolls_with_tracking(route, part_name)
            
            # Éviter les péages indésirables s'il y en a
            unwanted_tolls = [t for t in tolls if t["id"] != target_toll_id]
            
            if unwanted_tolls:
                route = self._avoid_tolls_and_recalculate(coordinates, unwanted_tolls, part_name)
                tolls = self._locate_tolls_with_tracking(route, f"{part_name}_verify")
                
                # Vérification finale
                if self._has_unwanted_tolls(tolls, target_toll_id, part_name):
                    return None
            
            return {"route": route, "tolls": tolls}
            
        except Exception as e:
            return ErrorHandler.handle_route_calculation_error(e, part_name=part_name)
    
    def _call_ors_with_tracking(self, payload, operation_name):
        """Appel ORS avec tracking des performances."""
        # Enrichir le payload avec les métadonnées de tracking
        enhanced_payload, metadata = ORSPayloadBuilder.enhance_payload_for_tracking(
            payload, operation_context=operation_name
        )
        
        with performance_tracker.measure_operation(metadata["operation_name"]):
            performance_tracker.count_api_call(metadata["operation_name"])
            return self.ors.call_ors(enhanced_payload)
    
    def _locate_tolls_with_tracking(self, route, operation_suffix):
        """Localise les péages avec tracking des performances."""
        with performance_tracker.measure_operation(f"{Config.Operations.LOCATE_TOLLS}_{operation_suffix}"):
            return locate_tolls(route, Config.get_barriers_csv_path())["on_route"]
    
    def _avoid_tolls_and_recalculate(self, coordinates, unwanted_tolls, part_name):
        """Évite les péages indésirables et recalcule la route."""
        with performance_tracker.measure_operation("create_avoidance_polygon"):
            avoid_poly = avoidance_multipolygon(unwanted_tolls)
        
        # Utiliser le builder pour créer le payload d'évitement
        avoid_payload = ORSPayloadBuilder.build_avoid_polygons_payload(coordinates, avoid_poly)
        return self._call_ors_with_tracking(avoid_payload, f"ORS_{part_name}_route_avoid")
    
    def _has_unwanted_tolls(self, tolls, target_toll_id, part_name):
        """Vérifie s'il reste des péages indésirables après évitement."""
        return not RouteValidator.validate_unwanted_tolls_avoided(tolls, target_toll_id, part_name)

    def get_route_avoid_tollways_with_tracking(self, coordinates):
        """Appel ORS pour éviter les péages avec tracking."""
        with performance_tracker.measure_operation(Config.Operations.ORS_AVOID_TOLLWAYS):
            performance_tracker.count_api_call("ORS_avoid_tollways")
            return self.ors.get_route_avoid_tollways(coordinates)

    def get_base_route_with_tracking(self, coordinates):
        """Appel ORS pour route de base avec tracking."""
        with performance_tracker.measure_operation(Config.Operations.ORS_BASE_ROUTE):
            performance_tracker.count_api_call("ORS_base_route")
            return self.ors.get_base_route(coordinates)

    def get_route_avoiding_polygons_with_tracking(self, coordinates, avoid_poly):
        """Appel ORS pour éviter des polygones avec tracking."""
        with performance_tracker.measure_operation(Config.Operations.ORS_ALTERNATIVE_ROUTE):
            performance_tracker.count_api_call("ORS_alternative_route")
            return self.ors.get_route_avoiding_polygons(coordinates, avoid_poly)

    def locate_and_cost_tolls(self, route, veh_class, operation_name=Config.Operations.LOCATE_TOLLS):
        """Localise les péages et calcule leurs coûts avec tracking."""
        with performance_tracker.measure_operation(operation_name):
            tolls_dict = locate_tolls(route, Config.get_barriers_csv_path())
            tolls_on_route = tolls_dict["on_route"]
            add_marginal_cost(tolls_on_route, veh_class)
            return tolls_dict