"""
toll_response_service.py
-----------------------

Service centralisé pour la construction de réponses API spécifiques aux péages.
Intègre le TollResponseBuilder existant dans la nouvelle architecture.
"""

from src.services.toll.response_builder import TollResponseBuilder
from src.services.common.result_formatter import ResultFormatter


class TollResponseService:
    """
    Service centralisé pour les réponses API de toll.
    Wrapper moderne autour de TollResponseBuilder.
    """
    
    @staticmethod
    def create_success_response(results, include_summary=True):
        """
        Crée une réponse de succès standardisée.
        
        Args:
            results: Résultats d'optimisation (fastest, cheapest, min_tolls)
            include_summary: Inclure un résumé dans la réponse
            
        Returns:
            dict: Réponse API formatée
        """
        return TollResponseBuilder.build_success_response(results, include_summary)
    
    @staticmethod
    def create_error_response(error_message, status_code=500, operation=None, details=None):
        """
        Crée une réponse d'erreur standardisée.
        
        Args:
            error_message: Message d'erreur principal
            status_code: Code de statut HTTP
            operation: Nom de l'opération qui a échoué
            details: Détails supplémentaires sur l'erreur
            
        Returns:
            dict: Réponse d'erreur formatée
        """
        return TollResponseBuilder.build_error_response(
            error_message, status_code, operation, details
        )
    
    @staticmethod
    def create_fallback_response(fallback_route, original_status="ERROR", reason="Unknown"):
        """
        Crée une réponse de fallback avec route de base.
        
        Args:
            fallback_route: Route de base à retourner
            original_status: Statut de l'opération qui a échoué
            reason: Raison du fallback
            
        Returns:
            dict: Réponse de fallback formatée
        """
        return TollResponseBuilder.build_fallback_response(
            fallback_route, original_status, reason
        )
    
    @staticmethod
    def create_validation_error_response(validation_errors):
        """
        Crée une réponse d'erreur de validation.
        
        Args:
            validation_errors: Liste des erreurs de validation
            
        Returns:
            dict: Réponse d'erreur de validation
        """
        return TollResponseBuilder.build_validation_error_response(validation_errors)
    
    @staticmethod
    def create_constraint_solution_response(route_result, constraint_type, status):
        """
        Crée une réponse spécialisée pour les solutions de contraintes.
        
        Args:
            route_result: Résultat de route calculée
            constraint_type: Type de contrainte (no_toll, one_toll, many_tolls)
            status: Statut de la solution
            
        Returns:
            dict: Réponse spécialisée formatée
        """
        # Formater en résultat uniforme pour la compatibilité
        uniform_result = {
            "fastest": route_result,
            "cheapest": route_result, 
            "min_tolls": route_result
        }
        
        # Ajouter des métadonnées sur la contrainte
        response = TollResponseBuilder.build_success_response(uniform_result, include_summary=True)
        response["constraint_info"] = {
            "type": constraint_type,
            "status": status,
            "toll_count": route_result.get("toll_count", 0),
            "cost": route_result.get("cost", 0)
        }
        
        return response
    
    @staticmethod
    def create_specialized_strategy_response(results, strategy_name, performance_stats=None):
        """
        Crée une réponse avec informations sur la stratégie utilisée.
        
        Args:
            results: Résultats d'optimisation
            strategy_name: Nom de la stratégie utilisée
            performance_stats: Statistiques de performance optionnelles
            
        Returns:
            dict: Réponse enrichie avec métadonnées de stratégie
        """
        response = TollResponseBuilder.build_success_response(results, include_summary=True)
        
        # Ajouter les métadonnées de stratégie
        response["strategy_info"] = {
            "name": strategy_name,
            "execution_time": performance_stats.get("total_time") if performance_stats else None,
            "api_calls": performance_stats.get("api_calls") if performance_stats else None
        }
        
        return response
