"""
operation_tracker.py
-------------------

Tracker centralisé pour les opérations communes entre toll et budget.
Responsabilité unique : gérer le nommage et tracking des opérations.
"""

from benchmark.performance_tracker import performance_tracker


class OperationTracker:
    """Gestionnaire centralisé pour le tracking des opérations."""
    
    @staticmethod
    def track_operation(operation_name, context="global"):
        """
        Crée un context manager pour tracker une opération.
        
        Args:
            operation_name: Nom de l'opération
            context: Contexte ("toll", "budget", "global")
            
        Returns:
            Context manager pour le tracking
        """
        full_name = f"{context}_{operation_name}" if context != "global" else operation_name
        return performance_tracker.measure_operation(full_name)
    
    @staticmethod
    def count_ors_call(api_type, context="global"):
        """
        Compte un appel ORS avec contexte.
        
        Args:
            api_type: Type d'appel ("base_route", "avoid_tollways", "alternative_route")
            context: Contexte ("toll", "budget", "global")
        """
        call_name = f"ORS_{api_type}_{context}" if context != "global" else f"ORS_{api_type}"
        performance_tracker.count_api_call(call_name)
    
    @staticmethod
    def log_operation_start(operation_name, details=None):
        """
        Log le début d'une opération.
        
        Args:
            operation_name: Nom de l'opération
            details: Détails additionnels (optionnel)
        """
        message = f"🚀 Début: {operation_name}"
        if details:
            message += f" - {details}"
        performance_tracker.log_info(message)
    
    @staticmethod
    def log_operation_success(operation_name, result_summary=None):
        """
        Log le succès d'une opération.
        
        Args:
            operation_name: Nom de l'opération
            result_summary: Résumé du résultat (optionnel)
        """
        message = f"✅ Succès: {operation_name}"
        if result_summary:
            message += f" - {result_summary}"
        performance_tracker.log_info(message)
    
    @staticmethod
    def log_operation_failure(operation_name, error_message):
        """
        Log l'échec d'une opération.
        
        Args:
            operation_name: Nom de l'opération
            error_message: Message d'erreur
        """
        message = f"❌ Échec: {operation_name} - {error_message}"
        performance_tracker.log_error(message)
    
    @staticmethod
    def log_strategy_selection(strategy_name, context, reason=None):
        """
        Log la sélection d'une stratégie.
        
        Args:
            strategy_name: Nom de la stratégie
            context: Contexte ("toll", "budget")
            reason: Raison de la sélection (optionnel)
        """
        message = f"🎯 Stratégie {context}: {strategy_name}"
        if reason:
            message += f" - {reason}"
        performance_tracker.log_info(message)
    
    @staticmethod
    def log_fallback_activation(fallback_type, original_error=None):
        """
        Log l'activation d'un fallback.
        
        Args:
            fallback_type: Type de fallback
            original_error: Erreur originale qui a déclenché le fallback
        """
        message = f"🔄 Fallback activé: {fallback_type}"
        if original_error:
            message += f" - Cause: {original_error}"
        performance_tracker.log_info(message)
