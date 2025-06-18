"""
error_handler.py
---------------

Gestionnaire centralisé pour la gestion des erreurs et exceptions.
Responsabilité unique : traiter et formatter les erreurs de manière uniforme.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.common.base_error_handler import BaseErrorHandler
from src.services.common.common_messages import CommonMessages
from src.services.common.toll_messages import TollMessages
from src.services.common.operation_tracker import OperationTracker
from src.services.toll.exceptions import (
    TollOptimizationError, ORSConnectionError, NoTollRouteError,
    NoOpenTollError, NoValidOpenTollRouteError, RouteCalculationError
)
from src.services.toll.constants import TollOptimizationConfig as Config


class TollErrorHandler(BaseErrorHandler):
    """Gestionnaire centralisé pour les erreurs d'optimisation."""
    
    @staticmethod
    def handle_ors_error(exception, operation_name="ORS_API_CALL"):
        """
        Gère les erreurs d'appel ORS et les convertit en exceptions métier.
        
        Args:
            exception: Exception originale de l'appel ORS
            operation_name: Nom de l'opération pour le logging
            
        Returns:
            tuple: (None, status_code)
        """
        error_msg = CommonMessages.ORS_API_ERROR.format(error=exception)
        OperationTracker.log_operation_failure(operation_name, str(exception))
        print(error_msg)
        
        ors_error = ORSConnectionError(error_msg, original_exception=exception)
        return None, ors_error.status_code
    
    @staticmethod
    def handle_route_calculation_error(exception, toll_id=None, part_name=None):
        """
        Gère les erreurs de calcul de route.
        
        Args:
            exception: Exception originale
            toll_id: ID du péage concerné (optionnel)
            part_name: Nom de la partie de route (optionnel)
            
        Returns:
            None
        """
        if toll_id and part_name:
            error_msg = f"Erreur lors du calcul de l'itinéraire via {toll_id} (partie {part_name}): {exception}"
        elif toll_id:
            error_msg = f"Erreur lors du calcul de l'itinéraire via {toll_id}: {exception}"
        elif part_name:
            error_msg = f"Erreur lors du calcul de {part_name}: {exception}"
        else:
            error_msg = f"Erreur lors du calcul de route: {exception}"
        
        performance_tracker.log_error(error_msg)
        print(error_msg)
        return None
    
    @staticmethod
    def handle_no_toll_route_error(exception):
        """
        Gère les erreurs spécifiques aux routes sans péage.
        
        Args:
            exception: Exception originale
            
        Returns:
            tuple: (None, status_code)
        """
        error_msg = f"Impossible de trouver un itinéraire sans péage: {exception}"
        performance_tracker.log_error(error_msg)
        print(error_msg)
        
        return None, Config.StatusCodes.NO_TOLL_ROUTE_NOT_POSSIBLE
    
    @staticmethod
    def handle_no_open_toll_error(search_radius_km):
        """
        Gère l'absence de péages ouverts dans la zone.
        
        Args:
            search_radius_km: Rayon de recherche en km
            
        Returns:
            tuple: (None, status_code)
        """
        print(TollMessages.NO_OPEN_TOLLS_IN_RADIUS.format(distance=search_radius_km))
        return None, Config.StatusCodes.NO_OPEN_TOLL_FOUND
    
    @staticmethod
    def log_operation_start(operation_name, **kwargs):
        """
        Log le début d'une opération avec ses paramètres.
        
        Args:
            operation_name: Nom de l'opération
            **kwargs: Paramètres de l'opération
        """
        if kwargs:
            params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            print(f"Début {operation_name} avec paramètres: {params_str}")
        else:
            print(f"Début {operation_name}")
    
    @staticmethod
    def log_operation_success(operation_name, result_summary=None):
        """
        Log le succès d'une opération.
        
        Args:
            operation_name: Nom de l'opération
            result_summary: Résumé du résultat (optionnel)
        """
        if result_summary:
            print(f"Succès {operation_name}: {result_summary}")
        else:
            print(f"Succès {operation_name}")
    
    @staticmethod
    def log_operation_failure(operation_name, error_message):
        """
        Log l'échec d'une opération.
        
        Args:
            operation_name: Nom de l'opération
            error_message: Message d'erreur
        """
        error_msg = f"Échec {operation_name}: {error_message}"
        performance_tracker.log_error(error_msg)
        print(error_msg)