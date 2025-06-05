"""
response_builder.py
------------------

Construction centralisée des réponses API.
Responsabilité unique : assembler les réponses finales pour l'API.
"""

from src.services.common.result_formatter import ResultFormatter
from src.services.toll.constants import TollOptimizationConfig as Config


class ResponseBuilder:
    """Constructeur centralisé pour les réponses API."""
    
    @staticmethod
    def build_success_response(optimization_results, include_summary=True):
        """
        Construit une réponse de succès avec les résultats d'optimisation.
        
        Args:
            optimization_results: Résultats d'optimisation formatés
            include_summary: Inclure un résumé comparatif (par défaut True)
            
        Returns:
            dict: Réponse API complète
        """
        response = {
            "success": True,
            "results": optimization_results,
            "status": optimization_results.get("status", "SUCCESS")
        }
        
        if include_summary:
            response["summary"] = ResultFormatter.format_comparison_summary(optimization_results)
        
        return response
    
    @staticmethod
    def build_error_response(error_message, status_code, operation_name=None, details=None):
        """
        Construit une réponse d'erreur.
        
        Args:
            error_message: Message d'erreur principal
            status_code: Code de statut d'erreur
            operation_name: Nom de l'opération qui a échoué (optionnel)
            details: Détails supplémentaires sur l'erreur (optionnel)
            
        Returns:
            dict: Réponse d'erreur API
        """
        response = {
            "success": False,
            "error": {
                "message": error_message,
                "status_code": status_code
            }
        }
        
        if operation_name:
            response["error"]["operation"] = operation_name
            
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def build_fallback_response(fallback_route, original_status, fallback_reason):
        """
        Construit une réponse de fallback avec une route de base.
        
        Args:
            fallback_route: Route de fallback
            original_status: Status de l'erreur originale
            fallback_reason: Raison du fallback
            
        Returns:
            dict: Réponse de fallback
        """
        response = {
            "success": True,
            "results": fallback_route,
            "status": original_status,
            "fallback": {
                "used": True,
                "reason": fallback_reason,
                "message": "Aucune solution optimisée trouvée, route de base utilisée"
            }
        }
        
        response["summary"] = ResultFormatter.format_comparison_summary(fallback_route)
        
        return response
    
    @staticmethod
    def build_partial_response(optimization_results, missing_routes, warnings=None):
        """
        Construit une réponse partielle quand certaines optimisations ont échoué.
        
        Args:
            optimization_results: Résultats d'optimisation (certains peuvent être None)
            missing_routes: Liste des types de routes manquantes
            warnings: Messages d'avertissement (optionnel)
            
        Returns:
            dict: Réponse partielle
        """
        response = {
            "success": True,
            "results": optimization_results,
            "status": optimization_results.get("status", "PARTIAL_SUCCESS"),
            "partial": {
                "missing_routes": missing_routes,
                "message": f"Solutions partielles trouvées, manquant: {', '.join(missing_routes)}"
            }
        }
        
        if warnings:
            response["warnings"] = warnings
            
        response["summary"] = ResultFormatter.format_comparison_summary(optimization_results)
        
        return response
    
    @staticmethod
    def build_validation_error_response(validation_errors):
        """
        Construit une réponse d'erreur de validation.
        
        Args:
            validation_errors: Liste des erreurs de validation
            
        Returns:
            dict: Réponse d'erreur de validation
        """
        return ResponseBuilder.build_error_response(
            error_message="Erreurs de validation des paramètres",
            status_code="VALIDATION_ERROR",
            details={
                "errors": validation_errors,
                "count": len(validation_errors)
            }
        )
    
    @staticmethod
    def build_no_route_response(max_tolls, constraints=None):
        """
        Construit une réponse quand aucune route n'est trouvée.
        
        Args:
            max_tolls: Nombre maximum de péages demandé
            constraints: Contraintes appliquées (optionnel)
            
        Returns:
            dict: Réponse d'absence de route
        """
        message = f"Aucune route trouvée respectant la contrainte de {max_tolls} péage(s)"
        
        if max_tolls == 0:
            status_code = Config.StatusCodes.NO_TOLL_ROUTE_NOT_POSSIBLE
        elif max_tolls == 1:
            status_code = Config.StatusCodes.NO_VALID_ROUTE_WITH_MAX_ONE_TOLL
        else:
            status_code = Config.StatusCodes.NO_VALID_ROUTE_WITH_MAX_TOLLS
        
        details = {"max_tolls": max_tolls}
        if constraints:
            details["constraints"] = constraints
            
        return ResponseBuilder.build_error_response(
            error_message=message,
            status_code=status_code,
            details=details
        )