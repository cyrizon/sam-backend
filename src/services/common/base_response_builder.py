"""
base_response_builder.py
-----------------------

Constructeur de réponses de base commun aux modules toll et budget.
Responsabilité unique : assembler les réponses finales standardisées pour l'API.
"""

from src.services.common.result_formatter import ResultFormatter
from src.services.common.base_constants import BaseOptimizationConfig as Config


class BaseResponseBuilder:
    """Constructeur centralisé de base pour les réponses API."""
    
    @staticmethod
    def build_success_response(optimization_results, include_summary=True, additional_info=None):
        """
        Construit une réponse de succès standardisée.
        
        Args:
            optimization_results: Résultats d'optimisation formatés
            include_summary: Inclure un résumé comparatif (par défaut True)
            additional_info: Informations supplémentaires à inclure
            
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
        
        if additional_info:
            response.update(additional_info)
            
        return response
    
    @staticmethod
    def build_error_response(error_message, status_code, operation_name=None, details=None):
        """
        Construit une réponse d'erreur standardisée.
        
        Args:
            error_message: Message d'erreur descriptif
            status_code: Code de statut d'erreur
            operation_name: Nom de l'opération qui a échoué (optionnel)
            details: Détails supplémentaires sur l'erreur (optionnel)
            
        Returns:
            dict: Réponse d'erreur formatée
        """
        error_response = {
            "success": False,
            "error": True,
            "message": error_message,
            "status": status_code
        }
        
        if operation_name:
            error_response["operation"] = operation_name
        if details:
            error_response["details"] = details
            
        return error_response
    
    @staticmethod
    def build_warning_response(optimization_results, warning_message, warning_code=None):
        """
        Construit une réponse avec avertissement.
        
        Args:
            optimization_results: Résultats d'optimisation
            warning_message: Message d'avertissement
            warning_code: Code d'avertissement (optionnel)
            
        Returns:
            dict: Réponse avec avertissement
        """
        response = BaseResponseBuilder.build_success_response(optimization_results)
        response["warning"] = {
            "message": warning_message,
            "code": warning_code
        }
        
        return response
    
    @staticmethod
    def build_fallback_response(optimization_results, fallback_reason, original_strategy=None):
        """
        Construit une réponse de fallback.
        
        Args:
            optimization_results: Résultats de la stratégie de fallback
            fallback_reason: Raison du fallback
            original_strategy: Stratégie originale qui a échoué
            
        Returns:
            dict: Réponse de fallback
        """
        response = BaseResponseBuilder.build_success_response(optimization_results)
        response["fallback"] = {
            "reason": fallback_reason,
            "original_strategy": original_strategy
        }
        
        return response
