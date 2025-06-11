"""
route_calculator.py
------------------

Utilitaires pour calculer des routes avec contraintes budgétaires.
Responsabilité unique : gérer la logique de calcul et d'évitement avec focus budget.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.toll.constants import TollOptimizationConfig as TollConfig  # For buffer configuration
from src.services.budget.route_validator import BudgetRouteValidator
from src.services.budget.exceptions import BudgetOptimizationError, BudgetExceededError
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.common.common_messages import CommonMessages
from src.services.common.budget_messages import BudgetMessages
from src.services.ors_payload_builder import ORSPayloadBuilder


class BudgetRouteCalculator:
    """Utilitaires pour calculer des routes avec contraintes budgétaires."""
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
    
    def get_base_route_with_tracking(self, coordinates):
        """Appel ORS pour la route de base avec tracking spécialisé budget."""
        with performance_tracker.measure_operation(Config.Operations.GET_BASE_ROUTE_FALLBACK):
            performance_tracker.count_api_call("ORS_base_route_budget")
            return self.ors.get_base_route(coordinates)
    
    def get_route_avoid_tollways_with_tracking(self, coordinates):
        """Appel ORS pour éviter les péages avec tracking budget."""
        with performance_tracker.measure_operation("get_route_avoid_tollways_budget"):
            performance_tracker.count_api_call("ORS_avoid_tollways_budget")
            return self.ors.get_route_avoid_tollways(coordinates)
    
    def get_route_avoiding_polygons_with_tracking(self, coordinates, avoid_poly):
        """Appel ORS pour éviter des polygones avec tracking budget."""
        with performance_tracker.measure_operation("get_route_avoiding_polygons_budget"):
            performance_tracker.count_api_call("ORS_alternative_route_budget")
            return self.ors.get_route_avoiding_polygons(coordinates, avoid_poly)
    
    def locate_and_cost_tolls(self, route, veh_class, operation_name="locate_tolls_budget"):
        """Localise les péages et calcule leurs coûts avec tracking budget."""
        with performance_tracker.measure_operation(operation_name):
            tolls_dict = locate_tolls(route, Config.get_barriers_csv_path(), buffer_m=TollConfig.TOLL_DETECTION_BUFFER_M)
            tolls_on_route = tolls_dict["on_route"]
            add_marginal_cost(tolls_on_route, veh_class)
            return tolls_dict
    
    def calculate_route_with_budget_constraint(self, coordinates, budget_limit, budget_type, veh_class):
        """
        Calcule une route en respectant une contrainte budgétaire.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            budget_limit: Limite budgétaire
            budget_type: Type de budget ("zero", "absolute", "percentage")
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route avec validation budgétaire
        """
        with performance_tracker.measure_operation(f"calculate_route_{budget_type}_budget"):
            try:
                # Route de base
                base_route = self.get_base_route_with_tracking(coordinates)
                tolls_dict = self.locate_and_cost_tolls(base_route, veh_class)
                
                cost = sum(t.get("cost", 0) for t in tolls_dict["on_route"])
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(tolls_dict["on_route"])
                
                # Validation budgétaire
                if budget_type == "zero":
                    is_valid = BudgetRouteValidator.validate_zero_budget(cost, "base_route")
                elif budget_type == "absolute":
                    is_valid = BudgetRouteValidator.validate_budget_limit(cost, budget_limit, "base_route")
                elif budget_type == "percentage":
                    # Pour le pourcentage, budget_limit est déjà la limite calculée
                    is_valid = BudgetRouteValidator.validate_budget_limit(cost, budget_limit, "base_route")
                else:
                    is_valid = True
                
                return {
                    "route": base_route,
                    "cost": cost,
                    "duration": duration,
                    "toll_count": toll_count,
                    "tolls": tolls_dict["on_route"],
                    "within_budget": is_valid
                }
                
            except Exception as e:
                BudgetErrorHandler.handle_route_calculation_error(e, budget_type, budget_limit)
                return None
    
    def calculate_alternative_avoiding_tolls(self, coordinates, tolls_to_avoid, budget_limit, budget_type, veh_class):
        """
        Calcule une route alternative en évitant certains péages.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            tolls_to_avoid: Liste des péages à éviter
            budget_limit: Limite budgétaire
            budget_type: Type de budget
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route alternative avec validation budgétaire
        """
        with performance_tracker.measure_operation("calculate_alternative_budget"):
            try:
                # Créer le polygone d'évitement
                avoid_poly = avoidance_multipolygon(tolls_to_avoid)
                
                # Calculer la route alternative
                alt_route = self.get_route_avoiding_polygons_with_tracking(coordinates, avoid_poly)
                tolls_dict = self.locate_and_cost_tolls(alt_route, veh_class, "analyze_alternative_budget")
                
                cost = sum(t.get("cost", 0) for t in tolls_dict["on_route"])
                duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(tolls_dict["on_route"])
                
                # Validation budgétaire
                if budget_type == "zero":
                    is_valid = BudgetRouteValidator.validate_zero_budget(cost, "alternative_route")
                elif budget_type == "absolute":
                    is_valid = BudgetRouteValidator.validate_budget_limit(cost, budget_limit, "alternative_route")
                elif budget_type == "percentage":
                    is_valid = BudgetRouteValidator.validate_budget_limit(cost, budget_limit, "alternative_route")
                else:
                    is_valid = True
                
                # Vérifier que les péages ont bien été évités
                avoided_ids = set(t["id"] for t in tolls_to_avoid)
                present_ids = set(t["id"] for t in tolls_dict["on_route"])
                
                if avoided_ids & present_ids:
                    print(CommonMessages.TOLLS_NOT_AVOIDED.format(tolls=list(avoided_ids & present_ids)))
                
                return {
                    "route": alt_route,
                    "cost": cost,
                    "duration": duration,
                    "toll_count": toll_count,
                    "tolls": tolls_dict["on_route"],
                    "within_budget": is_valid,
                    "avoided_tolls": tolls_to_avoid,
                    "successfully_avoided": len(avoided_ids - present_ids)
                }
                
            except Exception as e:
                BudgetErrorHandler.handle_route_calculation_error(e, budget_type, budget_limit)
                return None
    
    def find_cheapest_route_within_budget(self, coordinates, budget_limit, budget_type, veh_class, max_attempts=10):
        """
        Recherche intelligente de la route la moins chère dans le budget.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            budget_limit: Limite budgétaire
            budget_type: Type de budget
            veh_class: Classe de véhicule
            max_attempts: Nombre maximum de tentatives
            
        Returns:
            dict: Meilleure route dans le budget trouvée
        """
        with performance_tracker.measure_operation("find_cheapest_within_budget"):
            best_route = None
            best_cost = float('inf')
            
            # Route de base
            base_result = self.calculate_route_with_budget_constraint(coordinates, budget_limit, budget_type, veh_class)
            if base_result and base_result["within_budget"]:
                best_route = base_result
                best_cost = base_result["cost"]
            
            # Si déjà dans le budget et gratuite, pas besoin de chercher plus
            if best_cost == 0:
                return best_route
            
            # Essayer d'éviter les péages les plus chers
            if base_result and base_result["tolls"]:
                tolls_sorted = sorted(base_result["tolls"], key=lambda t: t.get("cost", 0), reverse=True)
                
                attempts = 0
                for toll in tolls_sorted:
                    if attempts >= max_attempts:
                        break
                    
                    if toll.get("cost", 0) <= 0:
                        continue
                    
                    attempts += 1
                    alt_result = self.calculate_alternative_avoiding_tolls(
                        coordinates, [toll], budget_limit, budget_type, veh_class
                    )
                    
                    if (alt_result and 
                        alt_result["within_budget"] and 
                        alt_result["cost"] < best_cost):
                        best_route = alt_result
                        best_cost = alt_result["cost"]
                        
                        # Si route gratuite trouvée, arrêter la recherche
                        if best_cost == 0:
                            break
            
            return best_route
    
    def _call_ors_with_tracking(self, payload, operation_name):
        """Appel ORS avec tracking des performances spécialisé budget."""
        # Enrichir le payload avec les métadonnées de tracking budget
        enhanced_payload, metadata = ORSPayloadBuilder.enhance_payload_for_tracking(
            payload, operation_context=f"budget_{operation_name}"
        )
        
        with performance_tracker.measure_operation(metadata["operation_name"]):
            performance_tracker.count_api_call(metadata["operation_name"])
            return self.ors.call_ors(enhanced_payload)