"""
error_handler.py
---------------

Gestionnaire centralisé pour la gestion des erreurs budgétaires.
Responsabilité unique : traiter et formatter les erreurs de manière uniforme.
"""

from src.services.common.base_error_handler import BaseErrorHandler
from src.services.common.result_formatter import ResultFormatter
from src.services.common.common_messages import CommonMessages
from src.services.common.budget_messages import BudgetMessages
from src.services.common.operation_tracker import OperationTracker
from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config


class BudgetErrorHandler(BaseErrorHandler):
    """Gestionnaire d'erreurs spécialisé pour l'optimisation budgétaire."""
    
    @staticmethod
    def handle_budget_validation_error(max_price, max_price_percent):
        """
        Gère les erreurs de validation des contraintes budgétaires.
        
        Args:
            max_price: Budget maximum en euros
            max_price_percent: Budget en pourcentage du coût de base
            
        Returns:
            dict ou None: Résultat d'erreur formaté ou None si validation OK
        """
        # Validation budget absolu
        if max_price is not None and not Config.validate_absolute_budget(max_price):
            BudgetErrorHandler.log_operation_failure(
                "budget_validation", 
                f"Budget absolu invalide: {max_price}€"
            )
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status=Config.StatusCodes.INVALID_MAX_PRICE
            )
        
        # Validation budget pourcentage
        if max_price_percent is not None and not Config.validate_percentage(max_price_percent):
            BudgetErrorHandler.log_operation_failure(
                "budget_validation", 
                f"Budget pourcentage invalide: {max_price_percent*100}%"
            )
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status=Config.StatusCodes.INVALID_MAX_PRICE_PERCENT
            )
        
        return None
    
    @staticmethod
    def handle_route_calculation_error(exception, budget_type=None, budget_limit=None):
        """
        Gère les erreurs de calcul de route budgétaire.
        
        Args:
            exception: Exception capturée
            budget_type: Type de budget ("zero", "absolute", "percentage")
            budget_limit: Limite budgétaire
            
        Returns:
            None: Toujours None pour indiquer un échec
        """
        if budget_type and budget_limit is not None:
            error_msg = f"Erreur lors du calcul de route avec budget {budget_type} ({budget_limit}): {exception}"
        else:
            error_msg = f"Erreur lors du calcul de route budgétaire: {exception}"
        
        BudgetErrorHandler.log_operation_failure("route_calculation", error_msg)
        return None
    
    @staticmethod
    def handle_no_budget_route_error(budget_limit, base_cost=None):
        """
        Gère le cas où aucune route ne respecte le budget.
        
        Args:
            budget_limit: Limite budgétaire
            base_cost: Coût de base (optionnel)
            
        Returns:
            dict: Résultat d'erreur formaté
        """
        if base_cost is not None:
            details = f"Budget: {budget_limit}€, Coût base: {base_cost}€"
        else:
            details = f"Budget: {budget_limit}€"
        
        BudgetErrorHandler.log_operation_failure("budget_constraint", f"Aucune route dans le budget - {details}")
        
        return ResultFormatter.format_optimization_results(
            fastest=None,
            cheapest=None,
            min_tolls=None,
            status=Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET
        )
    
    @staticmethod
    def handle_strategy_failure(strategy_name, exception, coordinates=None):
        """
        Gère l'échec d'une stratégie spécialisée.
        
        Args:
            strategy_name: Nom de la stratégie qui a échoué
            exception: Exception capturée
            coordinates: Coordonnées de la route (optionnel)
            
        Returns:
            None: Toujours None pour déclencher le fallback
        """
        error_msg = f"Stratégie {strategy_name} échouée: {exception}"
        BudgetErrorHandler.log_operation_failure("strategy_execution", error_msg)
        
        # Log additionnel pour le debugging
        if coordinates:
            print(BudgetMessages.COORDINATES_INFO.format(coordinates=coordinates))
        
        return None
    
    @staticmethod
    def handle_ors_error(exception, operation_name="ORS_API_CALL"):
        """
        Gère les erreurs de l'API ORS avec spécialisation budget.
        Hérite du comportement de base mais ajoute le contexte budget.
        
        Args:
            exception: Exception ORS
            operation_name: Nom de l'opération
            
        Returns:
            dict: Résultat d'erreur formaté
        """
        budget_operation = f"budget_{operation_name}"
        BudgetErrorHandler.log_operation_failure(budget_operation, f"Erreur ORS: {exception}")
        
        # Déléguer au gestionnaire de base avec le nom d'opération modifié
        return BaseErrorHandler.handle_ors_error(exception, budget_operation)
    
    @staticmethod
    def handle_critical_budget_error(exception, operation_context=None):
        """
        Gère les erreurs critiques dans le contexte budgétaire.
        
        Args:
            exception: Exception critique
            operation_context: Contexte de l'opération (optionnel)
            
        Returns:
            dict: Résultat d'erreur critique formaté
        """
        if operation_context:
            error_msg = f"Erreur critique budget ({operation_context}): {exception}"
        else:
            error_msg = f"Erreur critique budget: {exception}"
        
        BudgetErrorHandler.log_operation_failure("critical_error", error_msg)
        
        return ResultFormatter.format_optimization_results(
            fastest=None,
            cheapest=None,
            min_tolls=None,
            status=Config.StatusCodes.CRITICAL_ERROR
        )
    
    @staticmethod
    def log_budget_constraint_info(budget_type, budget_limit, base_cost=None):
        """
        Log des informations sur les contraintes budgétaires.
        
        Args:
            budget_type: Type de budget
            budget_limit: Limite budgétaire
            base_cost: Coût de base (optionnel)
        """
        if budget_type == "zero":
            print(BudgetMessages.CONSTRAINT_ZERO_BUDGET)
        elif budget_type == "percentage" and base_cost is not None:
            actual_limit = base_cost * budget_limit
            print(BudgetMessages.CONSTRAINT_PERCENTAGE_BUDGET.format(
                percent=budget_limit*100, 
                base_cost=base_cost, 
                actual_limit=actual_limit
            ))
        elif budget_type == "absolute":
            print(BudgetMessages.CONSTRAINT_ABSOLUTE_BUDGET.format(budget_limit=budget_limit))
        else:
            print(BudgetMessages.CONSTRAINT_GENERIC.format(budget_type=budget_type, budget_limit=budget_limit))