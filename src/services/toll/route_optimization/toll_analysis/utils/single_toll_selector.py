"""
Single Toll Selector
===================

Responsabilité : Sélection spéciale pour le cas d'un seul péage.
"""

from typing import List, Dict


class SingleTollSelector:
    """Sélecteur spécialisé pour un seul péage."""
    
    @staticmethod
    def select_single_open_toll(tolls_on_route: List) -> Dict:
        """
        Sélectionne un seul péage ouvert.
        
        Args:
            tolls_on_route: Péages disponibles sur la route
            
        Returns:
            Résultat de sélection avec un péage ouvert ou échec
        """
        print("🎯 Cas spécial : 1 péage demandé")
        
        # Chercher péages à système ouvert
        open_tolls = []
        for toll in tolls_on_route:
            if SingleTollSelector._is_open_system(toll):
                open_tolls.append(toll)
        
        if open_tolls:
            selected_toll = open_tolls[0]  # Premier péage ouvert
            toll_name = getattr(selected_toll, 'osm_name', 'Inconnu')
            print(f"✅ Péage ouvert sélectionné : {toll_name}")
            
            return {
                'selected_tolls': [selected_toll],
                'selection_method': 'count_based',
                'selection_strategy': 'single_open_toll',
                'target_count': 1,
                'achieved_count': 1,
                'selection_valid': True,
                'updated_segments_mapping': {}
            }
        
        # Aucun péage ouvert : retourner route sans péage
        print("⚠️ Aucun péage ouvert trouvé → Route sans péage")
        return {
            'selected_tolls': [],
            'selection_method': 'count_based',
            'selection_strategy': 'empty',
            'target_count': 1,
            'achieved_count': 0,
            'selection_valid': False,
            'failure_reason': 'no_open_system',
            'updated_segments_mapping': {}
        }
    
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
