"""
route_validator.py
-----------------

Validateur centralisé pour les contraintes sur les routes et péages.
Responsabilité unique : valider que les routes respectent les contraintes définies.
"""

from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.exceptions import (
    MaxTollsExceededError, AvoidedTollsStillPresentError, 
    TargetTollMissingError, TollValidationError
)


class RouteValidator:
    """Validateur centralisé pour les contraintes sur les routes et péages."""
    
    @staticmethod
    def validate_avoided_tolls(route_tolls, avoided_tolls, operation_name=""):
        """
        Vérifie qu'aucun péage à éviter n'est présent dans la route.
        
        Args:
            route_tolls: Liste des péages présents sur la route
            avoided_tolls: Liste des péages qui devaient être évités
            operation_name: Nom de l'opération pour le logging (optionnel)
            
        Returns:
            bool: True si validation OK (aucun péage évité présent), False sinon
        """
        if not avoided_tolls:
            return True  # Rien à éviter, validation OK
            
        avoided_ids = set(str(t["id"]).strip().lower() for t in avoided_tolls)
        present_ids = set(str(t["id"]).strip().lower() for t in route_tolls)
        
        unwanted_present = avoided_ids & present_ids
        if unwanted_present:
            operation_info = f" pour {operation_name}" if operation_name else ""
            print(Config.Messages.AVOIDED_TOLLS_STILL_PRESENT.format(
                present_tolls=unwanted_present
            ) + operation_info)
            return False
        return True
    
    @staticmethod
    def validate_max_tolls(toll_count, max_tolls, operation_name=""):
        """
        Vérifie que le nombre de péages respecte la limite maximum.
        
        Args:
            toll_count: Nombre de péages dans la route
            max_tolls: Nombre maximum de péages autorisés
            operation_name: Nom de l'opération pour le logging (optionnel)
            
        Returns:
            bool: True si validation OK (toll_count <= max_tolls), False sinon
        """
        if toll_count > max_tolls:
            operation_info = f" pour {operation_name}" if operation_name else ""
            print(Config.Messages.ROUTE_IGNORED_MAX_TOLLS.format(
                toll_count=toll_count, 
                max_tolls=max_tolls
            ) + operation_info)
            return False
        return True
    
    @staticmethod
    def validate_target_toll_present(route_tolls, target_toll_id, operation_name=""):
        """
        Vérifie que le péage cible est présent dans la route.
        
        Args:
            route_tolls: Liste des péages présents sur la route
            target_toll_id: ID du péage qui doit être présent
            operation_name: Nom de l'opération pour le logging (optionnel)
            
        Returns:
            bool: True si validation OK (péage cible présent), False sinon
        """
        toll_ids = set(t["id"] for t in route_tolls)
        if target_toll_id not in toll_ids:
            operation_info = f" pour {operation_name}" if operation_name else ""
            print(Config.Messages.TARGET_TOLL_MISSING.format(
                toll_id=target_toll_id
            ) + operation_info)
            return False
        return True
    
    @staticmethod
    def validate_unwanted_tolls_avoided(route_tolls, target_toll_id, part_name):
        """
        Vérifie qu'aucun péage indésirable n'est présent (version spécialisée pour route_calculator).
        
        Args:
            route_tolls: Liste des péages présents sur la route
            target_toll_id: ID du péage cible à conserver
            part_name: Nom de la partie de route pour le logging
            
        Returns:
            bool: True si validation OK (seul le péage cible est présent), False sinon
        """
        unwanted_tolls = [t for t in route_tolls if t["id"] != target_toll_id]
        if unwanted_tolls:
            unwanted_ids = [t['id'] for t in unwanted_tolls]
            print(Config.Messages.IMPOSSIBLE_AVOID_TOLLS.format(
                part_name=part_name, 
                unwanted_ids=unwanted_ids
            ))
            return False
        return True
    
    @staticmethod
    def validate_all_constraints(route_tolls, toll_count, max_tolls, avoided_tolls=None, 
                                target_toll_id=None, operation_name=""):
        """
        Validation complète qui combine toutes les contraintes.
        
        Args:
            route_tolls: Liste des péages présents sur la route
            toll_count: Nombre de péages dans la route
            max_tolls: Nombre maximum de péages autorisés
            avoided_tolls: Liste des péages qui devaient être évités (optionnel)
            target_toll_id: ID du péage qui doit être présent (optionnel)
            operation_name: Nom de l'opération pour le logging (optionnel)
            
        Returns:
            bool: True si toutes les validations passent, False sinon
        """
        # Validation du nombre maximum de péages
        if not RouteValidator.validate_max_tolls(toll_count, max_tolls, operation_name):
            return False
        
        # Validation des péages évités
        if avoided_tolls and not RouteValidator.validate_avoided_tolls(route_tolls, avoided_tolls, operation_name):
            return False
        
        # Validation de la présence du péage cible
        if target_toll_id and not RouteValidator.validate_target_toll_present(route_tolls, target_toll_id, operation_name):
            return False
        
        return True
    
    @staticmethod
    def validate_avoided_tolls_strict(route_tolls, avoided_tolls, operation_name=""):
        """
        Version stricte qui lève une exception si des péages évités sont présents.
        """
        if not avoided_tolls:
            return True
            
        avoided_ids = set(str(t["id"]).strip().lower() for t in avoided_tolls)
        present_ids = set(str(t["id"]).strip().lower() for t in route_tolls)
        
        unwanted_present = avoided_ids & present_ids
        if unwanted_present:
            raise AvoidedTollsStillPresentError(unwanted_present, operation_name)
        return True

    @staticmethod
    def validate_max_tolls_strict(toll_count, max_tolls, operation_name=""):
        """
        Version stricte qui lève une exception si trop de péages.
        """
        if toll_count > max_tolls:
            raise MaxTollsExceededError(toll_count, max_tolls, operation_name)
        return True

    @staticmethod
    def validate_target_toll_present_strict(route_tolls, target_toll_id, operation_name=""):
        """
        Version stricte qui lève une exception si le péage cible est absent.
        """
        toll_ids = set(t["id"] for t in route_tolls)
        if target_toll_id not in toll_ids:
            raise TargetTollMissingError(target_toll_id, operation_name)
        return True

    @staticmethod
    def validate_all_constraints_strict(route_tolls, toll_count, max_tolls, avoided_tolls=None, 
                                       target_toll_id=None, operation_name=""):
        """
        Version stricte de validate_all_constraints qui lève des exceptions.
        """
        RouteValidator.validate_max_tolls_strict(toll_count, max_tolls, operation_name)
        
        if avoided_tolls:
            RouteValidator.validate_avoided_tolls_strict(route_tolls, avoided_tolls, operation_name)
        
        if target_toll_id:
            RouteValidator.validate_target_toll_present_strict(route_tolls, target_toll_id, operation_name)
        
        return True