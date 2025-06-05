"""
exceptions.py
------------

Exceptions personnalisées pour l'optimisation de routes avec péages.
Responsabilité unique : définir une hiérarchie d'exceptions métier.
"""

from src.services.toll.constants import TollOptimizationConfig as Config


class TollOptimizationError(Exception):
    """Exception de base pour toutes les erreurs d'optimisation de péages."""
    
    def __init__(self, message, status_code=None, operation_name=None):
        """
        Initialise l'exception avec un message et des métadonnées optionnelles.
        
        Args:
            message: Message d'erreur descriptif
            status_code: Code de statut associé (depuis Config.StatusCodes)
            operation_name: Nom de l'opération qui a échoué
        """
        super().__init__(message)
        self.status_code = status_code
        self.operation_name = operation_name
        self.message = message
    
    def to_dict(self):
        """Convertit l'exception en dictionnaire pour la réponse API."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "operation": self.operation_name
        }


class ORSConnectionError(TollOptimizationError):
    """Erreur de connexion ou d'appel au service ORS."""
    
    def __init__(self, message, original_exception=None):
        super().__init__(
            message, 
            status_code=Config.StatusCodes.ORS_CONNECTION_ERROR,
            operation_name="ORS_API_CALL"
        )
        self.original_exception = original_exception


class NoValidRouteError(TollOptimizationError):
    """Aucune route valide trouvée respectant les contraintes."""
    
    def __init__(self, message, max_tolls=None, constraints=None):
        super().__init__(message)
        self.max_tolls = max_tolls
        self.constraints = constraints


class NoTollRouteError(NoValidRouteError):
    """Impossible de trouver une route sans péage."""
    
    def __init__(self, message="Impossible de trouver un itinéraire sans péage"):
        super().__init__(
            message, 
            max_tolls=0
        )
        self.status_code = Config.StatusCodes.NO_TOLL_ROUTE_NOT_POSSIBLE


class NoOpenTollError(NoValidRouteError):
    """Aucun péage ouvert trouvé dans la zone."""
    
    def __init__(self, message="Aucun péage à système ouvert trouvé", search_radius_km=None):
        super().__init__(message, max_tolls=1)
        self.status_code = Config.StatusCodes.NO_OPEN_TOLL_FOUND
        self.search_radius_km = search_radius_km


class NoValidOpenTollRouteError(NoValidRouteError):
    """Aucune route valide trouvée avec un péage ouvert."""
    
    def __init__(self, message="Aucune route valide trouvée avec un péage ouvert"):
        super().__init__(message, max_tolls=1)
        self.status_code = Config.StatusCodes.NO_VALID_OPEN_TOLL_ROUTE


class MaxTollsExceededError(TollOptimizationError):
    """Le nombre de péages dépasse la limite autorisée."""
    
    def __init__(self, found_tolls, max_tolls, operation_name=""):
        message = f"Route ignorée : {found_tolls} péages > max_tolls={max_tolls}"
        if operation_name:
            message += f" pour {operation_name}"
        
        super().__init__(message, operation_name=operation_name)
        self.found_tolls = found_tolls
        self.max_tolls = max_tolls


class TollValidationError(TollOptimizationError):
    """Erreur de validation des contraintes sur les péages."""
    
    def __init__(self, message, validation_type=None):
        super().__init__(message)
        self.validation_type = validation_type


class AvoidedTollsStillPresentError(TollValidationError):
    """Des péages à éviter sont toujours présents sur la route."""
    
    def __init__(self, present_tolls, operation_name=""):
        message = f"Certains péages à éviter sont toujours présents : {present_tolls}"
        if operation_name:
            message += f" pour {operation_name}"
        
        super().__init__(message, validation_type="avoided_tolls")
        self.present_tolls = present_tolls
        self.operation_name = operation_name


class TargetTollMissingError(TollValidationError):
    """Le péage cible n'est pas présent dans la route."""
    
    def __init__(self, toll_id, operation_name=""):
        message = f"Le péage cible {toll_id} n'est pas présent dans l'itinéraire final"
        if operation_name:
            message += f" pour {operation_name}"
        
        super().__init__(message, validation_type="target_toll_missing")
        self.toll_id = toll_id
        self.operation_name = operation_name


class RouteCalculationError(TollOptimizationError):
    """Erreur lors du calcul d'une route spécifique."""
    
    def __init__(self, message, toll_id=None, part_name=None):
        super().__init__(message)
        self.toll_id = toll_id
        self.part_name = part_name