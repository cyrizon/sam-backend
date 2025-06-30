"""
Selection Result Builder
=======================

Responsabilité : Construction des résultats de sélection.
"""

from typing import List


class SelectionResultBuilder:
    """Constructeur de résultats de sélection."""
    
    @staticmethod
    def create_selection_result(
        selected_tolls: List, 
        target_count: int,
        selection_strategy: str
    ) -> dict:
        """Crée le résultat de sélection."""
        return {
            'selected_tolls': selected_tolls,
            'selection_method': 'count_based',
            'selection_strategy': selection_strategy,
            'target_count': target_count,
            'achieved_count': len(selected_tolls),
            'selection_valid': len(selected_tolls) > 0,
            'updated_segments_mapping': {}
        }
    
    @staticmethod
    def create_empty_selection(target_count: int, reason: str = 'no_tolls') -> dict:
        """Crée une sélection vide."""
        return {
            'selected_tolls': [],
            'selection_method': 'count_based',
            'selection_strategy': 'empty',
            'target_count': target_count,
            'achieved_count': 0,
            'selection_valid': False,
            'failure_reason': reason,
            'updated_segments_mapping': {}
        }
