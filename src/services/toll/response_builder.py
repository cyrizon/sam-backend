"""
response_builder.py
------------------

Construction centralisée des réponses API pour toll.
Responsabilité unique : assembler les réponses finales spécifiques au toll.
"""

from src.services.common.base_response_builder import BaseResponseBuilder
from src.services.common.result_formatter import ResultFormatter
from src.services.common.base_constants import BaseOptimizationConfig as Config


class TollResponseBuilder(BaseResponseBuilder):
    """Constructeur centralisé pour les réponses API de toll."""
    @staticmethod
    def build_success_response(optimization_results, include_summary=True):
        """
        Construit une réponse de succès avec les résultats d'optimisation de toll.
        """
        return BaseResponseBuilder.build_success_response(
            optimization_results, 
            include_summary
        )
    
    @staticmethod
    def build_error_response(error_message, status_code, operation_name=None, details=None):
        """
        Construit une réponse d'erreur spécifique au toll.
        """
        return BaseResponseBuilder.build_error_response(
            error_message, 
            status_code, 
            operation_name, 
            details
        )

    @staticmethod
    def build_fallback_response(fallback_route, original_status, fallback_reason):
        """
        Construit une réponse de fallback avec une route de base.
        """
        return BaseResponseBuilder.build_fallback_response(
            fallback_route,
            fallback_reason,
            original_status
        )

    @staticmethod
    def build_validation_error_response(validation_errors):
        """
        Construit une réponse d'erreur de validation.
        """
        return TollResponseBuilder.build_error_response(
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
            
        return TollResponseBuilder.build_error_response(
            error_message=message,
            status_code=status_code,
            details=details
        )