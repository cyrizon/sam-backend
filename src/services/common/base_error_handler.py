"""
base_error_handler.py
--------------------

Gestionnaire d'erreurs de base commun aux modules toll et budget.
Responsabilité unique : traiter et formatter les erreurs de manière uniforme.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.common.base_constants import BaseOptimizationConfig as Config

class BaseErrorHandler:
    """Gestionnaire d'erreurs de base pour l'optimisation."""
    
    @staticmethod
    def log_operation_start(operation_name, **kwargs):
        """Log le début d'une opération."""
        params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        print(f"🚀 Début: {operation_name} ({params_str})")
    
    @staticmethod
    def log_operation_success(operation_name, details=""):
        """Log le succès d'une opération."""
        print(f"✅ Succès: {operation_name} - {details}")
    
    @staticmethod
    def log_operation_failure(operation_name, error_message):
        """Log l'échec d'une opération."""
        print(f"❌ Échec: {operation_name} - {error_message}")
    
    @staticmethod
    def log_operation_warning(operation_name, warning_message):
        """Log un avertissement durant une opération."""
        print(f"⚠️ Attention: {operation_name} - {warning_message}")
    
    @staticmethod
    def track_operation_error(operation_name, exception, context=None):
        """Track une erreur avec le performance tracker."""
        try:
            performance_tracker.end_operation(operation_name, success=False)
            print(f"❌ Erreur trackée pour {operation_name}: {str(exception)}")
            if context:
                print(f"   Contexte: {context}")
        except Exception as e:
            print(f"Erreur lors du tracking de {operation_name}: {e}")
    
    @staticmethod
    def format_error_response(error_message, status_code, operation_name=None, details=None):
        """
        Formate une réponse d'erreur standardisée.
        
        Args:
            error_message: Message d'erreur
            status_code: Code de statut d'erreur
            operation_name: Nom de l'opération qui a échoué
            details: Détails supplémentaires
            
        Returns:
            tuple: (None, status_code) pour compatibilité
        """
        error_info = {
            "error": True,
            "message": error_message,
            "status": status_code
        }
        
        if operation_name:
            error_info["operation"] = operation_name
        if details:
            error_info["details"] = details
            
        print(f"❌ Erreur formatée: {error_message} (code: {status_code})")
        return None, status_code
    
    @staticmethod
    def handle_validation_error(exception, operation_name="validation"):
        """
        Gère les erreurs de validation et les convertit en format uniforme.
        
        Args:
            exception: Exception de validation
            operation_name: Nom de l'opération de validation
            
        Returns:
            tuple: (None, status_code)
        """
        error_message = f"Erreur de validation: {str(exception)}"
        BaseErrorHandler.log_operation_failure(operation_name, error_message)
        BaseErrorHandler.track_operation_error(operation_name, exception)
        
        return BaseErrorHandler.format_error_response(
            error_message=error_message,
            status_code=Config.StatusCodes.CRITICAL_ERROR,
            operation_name=operation_name
        )
