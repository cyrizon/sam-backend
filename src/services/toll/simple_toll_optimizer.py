"""
simple_toll_optimizer.py
-----------------------

Optimiseur de routes simplifié pour respecter les contraintes de péages.
Remplace l'ancien système complexe d'optimisation de coût par une approche
pragmatique centrée sur le respect des contraintes.

Stratégie :
1. Priorité 1 : Routes avec ≤ max_tolls péages
2. Priorité 2 : Routes avec max_tolls + 1 péages (backup)
3. Priorité 3 : Fallback si aucune solution trouvée
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.simple_constraint_strategy import SimpleConstraintStrategy
from src.services.toll.fallback_strategy import TollFallbackStrategy
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler
from src.services.common.result_formatter import ResultFormatter


class SimpleTollOptimizer:
    """
    Optimiseur simplifié pour les contraintes de péages.
    Focus : respect des contraintes plutôt qu'optimisation de coût.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur simplifié avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.constraint_strategy = SimpleConstraintStrategy(ors_service)
        self.fallback_strategy = TollFallbackStrategy(ors_service)
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Calcule un itinéraire en respectant les contraintes de péages.
        
        Nouvelle approche simplifiée :
        1. Cherche route respectant max_tolls (≤ contrainte)
        2. Si pas trouvé, cherche backup avec max_tolls + 1
        3. Si toujours rien, utilise fallback
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            dict: Résultats formatés (fastest, cheapest, min_tolls, status)
        """
        # Log du début de l'opération
        TollErrorHandler.log_operation_start(
            "compute_route_with_toll_limit_simplified",
            max_tolls=max_tolls,
            veh_class=veh_class
        )
        
        with performance_tracker.measure_operation("simple_toll_optimizer", {
            "max_tolls": max_tolls,
            "veh_class": veh_class
        }):
            print(f"=== Optimiseur Simplifié : max {max_tolls} péages ===")
            
            try:
                # Utiliser la stratégie de contrainte simplifiée
                constraint_result = self.constraint_strategy.find_route_respecting_constraint(
                    coordinates, max_tolls, veh_class)                # Traiter les résultats selon la solution trouvée
                solution_type = constraint_result.get("found_solution", "none")
                
                if solution_type in ["within_limit", "backup_plus_one", "backup_minus_one", "no_toll_fallback"]:
                    # Une solution a été trouvée
                    result = self._format_constraint_solution(constraint_result, max_tolls, solution_type)
                elif solution_type == "none":
                    # Aucune solution trouvée, utiliser fallback
                    print("❌ Aucune solution trouvée (ni primaire ni backup) - Activation fallback")
                    result = self._handle_no_solution_fallback(coordinates, max_tolls, veh_class)
                else:
                    # Type de solution inattendu, traiter comme solution valide
                    print(f"⚠️ Type de solution inattendu: {solution_type}, traitement comme solution valide")
                    result = self._format_constraint_solution(constraint_result, max_tolls, solution_type)
                
                # Log du succès
                if result and result.get("status"):
                    TollErrorHandler.log_operation_success(
                        "compute_route_with_toll_limit_simplified",
                        f"Status: {result['status']}"
                    )
                
                return result
                
            except Exception as e:
                TollErrorHandler.log_operation_failure(
                    "compute_route_with_toll_limit_simplified", str(e)
                )
                return self._handle_critical_failure(coordinates, max_tolls, veh_class, str(e))
    def _format_constraint_solution(self, constraint_result, max_tolls, solution_type):
        """
        Formate une solution trouvée par la stratégie de contrainte.
        """
        primary_route = constraint_result["primary_route"]
        actual_tolls = constraint_result.get("actual_tolls", primary_route.get('toll_count', 0))
        
        # Déterminer le status code approprié selon le nouveau système
        if solution_type == "within_limit":
            status = Config.StatusCodes.CONSTRAINT_RESPECTED
            print(f"✅ Solution RESPECTÉE trouvée - {actual_tolls} péages (≤ {max_tolls})")
        elif solution_type == "backup_plus_one":
            status = Config.StatusCodes.CONSTRAINT_EXCEEDED_BY_ONE  
            print(f"🔄 Solution +1 trouvée - {actual_tolls} péages (max: {max_tolls})")
        elif solution_type == "backup_minus_one":
            status = Config.StatusCodes.CONSTRAINT_RESPECTED
            print(f"📉 Solution -1 trouvée - {actual_tolls} péages (< {max_tolls})")
        elif solution_type == "no_toll_fallback":
            status = Config.StatusCodes.NO_TOLL_SUCCESS
            print(f"🚫 Solution sans péage trouvée - {actual_tolls} péages")
        else:
            status = Config.StatusCodes.SUCCESS
            print(f"✅ Solution trouvée - {actual_tolls} péages (type: {solution_type})")
        
        # Dans l'approche simplifiée, la route trouvée devient fastest, cheapest et min_tolls
        formatted_result = {
            "fastest": primary_route,
            "cheapest": primary_route, 
            "min_tolls": primary_route,
            "status": status
        }
        
        return formatted_result
    
    def _handle_no_solution_fallback(self, coordinates, max_tolls, veh_class):
        """
        Gère le fallback quand aucune solution n'est trouvée.
        """
        print("❌ Aucune solution trouvée (ni primaire ni backup) - Activation fallback")
        
        # Utiliser la stratégie de fallback existante
        return self.fallback_strategy.handle_toll_failure(
            coordinates, max_tolls, veh_class=veh_class
        )
    
    def _handle_critical_failure(self, coordinates, max_tolls, veh_class, error_message):
        """
        Gère les erreurs critiques avec fallback ultime.
        """
        print(f"💥 Erreur critique: {error_message}")
        
        try:
            # Essayer le fallback même en cas d'erreur critique
            return self.fallback_strategy.handle_toll_failure(
                coordinates, max_tolls, veh_class=veh_class
            )
        except Exception:
            # Fallback ultime - réponse d'erreur standard
            return {
                "fastest": None,
                "cheapest": None,
                "min_tolls": None,
                "status": Config.StatusCodes.CRITICAL_ERROR,
                "error": error_message
            }
