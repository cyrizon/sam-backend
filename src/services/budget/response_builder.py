"""
response_builder.py
------------------

Construction centralisée des réponses API pour l'optimisation budgétaire.
Responsabilité unique : assembler les réponses finales pour l'API budget.
"""

from src.services.common.result_formatter import ResultFormatter
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.route_validator import BudgetRouteValidator


class BudgetResponseBuilder:
    """Constructeur centralisé pour les réponses API budgétaires."""
    
    @staticmethod
    def build_budget_success_response(optimization_results, budget_type, budget_limit=None, base_cost=None):
        """
        Construit une réponse de succès avec contrainte budgétaire.
        
        Args:
            optimization_results: Résultats d'optimisation
            budget_type: Type de budget ("zero", "absolute", "percentage", "none")
            budget_limit: Limite budgétaire
            base_cost: Coût de base (pour les pourcentages)
            
        Returns:
            dict: Réponse API formatée
        """
        # Informations sur la contrainte budgétaire
        budget_info = BudgetRouteValidator.get_budget_info(
            budget_limit if budget_type == "absolute" else None,
            budget_limit if budget_type == "percentage" else None,
            base_cost
        )
        
        response = {
            "success": True,
            "results": optimization_results,
            "status": optimization_results.get("status", "SUCCESS"),
            "budget_constraint": {
                "type": budget_type,
                "limit": budget_info.get("limit"),
                "satisfied": BudgetResponseBuilder._is_budget_satisfied(optimization_results, budget_info.get("limit")),
                "description": budget_info.get("description")
            }
        }
        
        # Ajouter les détails spécifiques au pourcentage
        if budget_type == "percentage" and base_cost is not None:
            response["budget_constraint"]["percentage"] = budget_limit
            response["budget_constraint"]["base_cost"] = base_cost
        
        # Ajouter le résumé comparatif
        response["summary"] = ResultFormatter.format_comparison_summary(optimization_results)
        
        return response
    
    @staticmethod
    def build_budget_exceeded_response(optimization_results, budget_type, budget_limit, best_alternative, base_cost=None):
        """
        Construit une réponse quand le budget est dépassé.
        
        Args:
            optimization_results: Résultats d'optimisation
            budget_type: Type de budget
            budget_limit: Limite budgétaire
            best_alternative: Meilleure alternative trouvée
            base_cost: Coût de base (pour les pourcentages)
            
        Returns:
            dict: Réponse API formatée
        """
        # Calculer la limite effective pour les pourcentages
        effective_limit = budget_limit
        if budget_type == "percentage" and base_cost is not None:
            effective_limit = base_cost * budget_limit
        
        # Informations sur la contrainte budgétaire
        budget_info = BudgetRouteValidator.get_budget_info(
            budget_limit if budget_type == "absolute" else None,
            budget_limit if budget_type == "percentage" else None,
            base_cost
        )
        
        response = {
            "success": True,
            "results": optimization_results,
            "status": optimization_results.get("status", "BUDGET_EXCEEDED"),
            "budget_constraint": {
                "type": budget_type,
                "limit": effective_limit,
                "satisfied": False,
                "description": budget_info.get("description"),
                "best_alternative": {
                    "cost": best_alternative.get("cost") if best_alternative else None,
                    "difference": (best_alternative.get("cost", 0) - effective_limit) if best_alternative and effective_limit else None
                }
            }
        }
        
        # Ajouter les détails spécifiques au pourcentage
        if budget_type == "percentage" and base_cost is not None:
            response["budget_constraint"]["percentage"] = budget_limit
            response["budget_constraint"]["base_cost"] = base_cost
        
        response["summary"] = ResultFormatter.format_comparison_summary(optimization_results)
        return response
    
    @staticmethod
    def build_zero_budget_response(optimization_results, has_tolls_warning=False):
        """
        Réponse spécialisée pour budget zéro.
        
        Args:
            optimization_results: Résultats d'optimisation
            has_tolls_warning: True si des péages sont présents malgré l'évitement
            
        Returns:
            dict: Réponse API formatée
        """
        response = BudgetResponseBuilder.build_budget_success_response(
            optimization_results, "zero", 0
        )
        
        # Ajouter l'avertissement sur les péages si nécessaire
        if has_tolls_warning:
            response["warning"] = "Route gratuite non trouvée, l'itinéraire contient des péages"
        
        return response
    
    @staticmethod
    def build_fallback_response(optimization_results, original_budget_type, original_budget_limit, fallback_reason="strategy_failure"):
        """
        Construit une réponse de fallback.
        
        Args:
            optimization_results: Résultats d'optimisation
            original_budget_type: Type de budget original
            original_budget_limit: Limite budgétaire originale
            fallback_reason: Raison du fallback
            
        Returns:
            dict: Réponse API formatée
        """
        response = {
            "success": True,
            "results": optimization_results,
            "status": optimization_results.get("status", "FALLBACK_USED"),
            "fallback_info": {
                "reason": fallback_reason,
                "original_constraint": {
                    "type": original_budget_type,
                    "limit": original_budget_limit
                }
            }
        }
        
        response["summary"] = ResultFormatter.format_comparison_summary(optimization_results)
        return response
    
    @staticmethod
    def build_error_response(error_status, error_message, budget_type=None, budget_limit=None):
        """
        Construit une réponse d'erreur.
        
        Args:
            error_status: Code de statut d'erreur
            error_message: Message d'erreur
            budget_type: Type de budget (optionnel)
            budget_limit: Limite budgétaire (optionnel)
            
        Returns:
            dict: Réponse d'erreur formatée
        """
        response = {
            "success": False,
            "results": {
                "fastest": None,
                "cheapest": None,
                "min_tolls": None,
                "status": error_status
            },
            "error": {
                "message": error_message,
                "status_code": error_status
            }
        }
        
        if budget_type and budget_limit is not None:
            response["budget_constraint"] = {
                "type": budget_type,
                "limit": budget_limit,
                "satisfied": False
            }
        
        return response
    
    @staticmethod
    def _is_budget_satisfied(optimization_results, budget_limit):
        """
        Vérifie si au moins une solution respecte le budget.
        
        Args:
            optimization_results: Résultats d'optimisation
            budget_limit: Limite budgétaire
            
        Returns:
            bool: True si au moins une solution respecte le budget
        """
        if budget_limit is None:
            return True
        
        # Vérifier chaque type de résultat
        for result_type in ["fastest", "cheapest", "min_tolls"]:
            result = optimization_results.get(result_type)
            if result and result.get("cost", float('inf')) <= budget_limit:
                return True
        
        return False
    
    @staticmethod
    def add_performance_metrics(response, performance_data):
        """
        Ajoute des métriques de performance à la réponse.
        
        Args:
            response: Réponse API
            performance_data: Données de performance
            
        Returns:
            dict: Réponse enrichie avec les métriques
        """
        if performance_data:
            response["performance"] = {
                "total_duration_ms": performance_data.get("total_duration", 0),
                "api_calls_count": performance_data.get("api_calls", 0),
                "combinations_tested": performance_data.get("combinations_tested", 0)
            }
        
        return response