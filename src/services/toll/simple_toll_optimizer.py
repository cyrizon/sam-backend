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
                    coordinates, max_tolls, veh_class
                )
                
                # Traiter les résultats selon la solution trouvée
                if constraint_result["found_solution"] == "primary":
                    result = self._format_primary_solution(constraint_result)
                elif constraint_result["found_solution"] == "backup":
                    result = self._format_backup_solution(constraint_result, max_tolls)
                else:
                    # Aucune solution trouvée, utiliser fallback
                    result = self._handle_no_solution_fallback(coordinates, max_tolls, veh_class)
                
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
    
    def _format_primary_solution(self, constraint_result):
        """
        Formate la solution primaire (respecte la contrainte exacte).
        """
        primary_route = constraint_result["primary_route"]
        
        print(f"✅ Solution PRIMAIRE trouvée - {primary_route['toll_count']} péages")
        
        # Dans l'approche simplifiée, la route trouvée devient fastest, cheapest et min_tolls
        formatted_result = {
            "fastest": primary_route,
            "cheapest": primary_route,
            "min_tolls": primary_route,
            "status": Config.StatusCodes.CONSTRAINT_RESPECTED
        }
        
        return formatted_result
    
    def _format_backup_solution(self, constraint_result, max_tolls):
        """
        Formate la solution backup (max_tolls + 1).
        """
        backup_route = constraint_result["backup_route"]
        
        print(f"🔄 Solution BACKUP trouvée - {backup_route['toll_count']} péages (max autorisé: {max_tolls})")
        
        # La solution backup devient fastest, cheapest et min_tolls
        formatted_result = {
            "fastest": backup_route,
            "cheapest": backup_route,
            "min_tolls": backup_route,
            "status": Config.StatusCodes.CONSTRAINT_EXCEEDED_BY_ONE
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
