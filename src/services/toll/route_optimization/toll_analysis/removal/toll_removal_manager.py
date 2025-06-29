"""
Toll Removal Manager
===================

Responsabilité : Gestion de la suppression des péages depuis la fin de route.
"""

from typing import List, Dict, Tuple


class TollRemovalManager:
    """Gestionnaire de suppression des péages."""
    
    @staticmethod
    def remove_tolls_from_end(tolls_on_route: List, target_count: int) -> Tuple[List, List, List]:
        """
        Supprime les péages depuis la fin de route pour atteindre le nombre cible.
        
        Args:
            tolls_on_route: Liste des péages sur la route
            target_count: Nombre de péages souhaité
            
        Returns:
            Tuple[remaining_tolls, removed_open, removed_closed]
            - remaining_tolls: Péages restants après suppression
            - removed_open: Péages ouverts supprimés
            - removed_closed: Péages fermés supprimés
        """
        if target_count >= len(tolls_on_route):
            return tolls_on_route.copy(), [], []
        
        working_tolls = tolls_on_route.copy()
        removed_open = []
        removed_closed = []
        
        tolls_to_remove = len(working_tolls) - target_count
        print(f"🔄 Suppression depuis la fin : {len(working_tolls)} → {target_count} péages")
        
        for i in range(tolls_to_remove):
            if not working_tolls:
                break
            
            # Supprimer le premier péage (fin de route géographiquement)
            removed_toll = working_tolls.pop(0)
            toll_name = getattr(removed_toll, 'osm_name', 'Inconnu')
            print(f"   ❌ Supprimé : {toll_name}")
            
            # Classer par système
            if TollRemovalManager._is_open_system(removed_toll):
                removed_open.append(removed_toll)
            else:
                removed_closed.append(removed_toll)
        
        return working_tolls, removed_open, removed_closed
    
    @staticmethod
    def _is_open_system(toll) -> bool:
        """Vérifie si le péage est à système ouvert."""
        # MatchedToll model
        if hasattr(toll, 'is_open_system'):
            return toll.is_open_system
        elif hasattr(toll, 'csv_role'):
            return getattr(toll, 'csv_role', '') == 'O'
        
        # TollStation model  
        elif hasattr(toll, 'toll_type'):
            return getattr(toll, 'toll_type', '').lower() == 'open'
        
        # Fallback : examiner le nom pour indicateurs
        name = getattr(toll, 'osm_name', None) or getattr(toll, 'name', '') or ''
        name = name.lower()
        return 'open' in name or 'ouvert' in name
