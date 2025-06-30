"""
Toll Optimizer
==============

Responsabilité : Optimisation des péages fermés supprimés par remplacement géographique.
"""

from typing import List, Dict, Optional
from ...utils.distance_calculator import DistanceCalculator


class TollOptimizer:
    """Optimiseur de péages avec remplacement géographique."""
    
    @staticmethod
    def optimize_after_removal(
        remaining_tolls: List, 
        removed_closed_tolls: List,
        identification_result: Dict
    ) -> List:
        """
        Optimise les péages après suppression de péages fermés.
        
        Args:
            remaining_tolls: Péages restants après suppression
            removed_closed_tolls: Péages fermés qui ont été supprimés
            identification_result: Résultat de l'identification des péages
            
        Returns:
            Liste des péages optimisés
        """
        if not removed_closed_tolls or not remaining_tolls:
            return remaining_tolls
        
        # Trouver le prochain péage fermé à optimiser
        next_closed_toll = TollOptimizer._find_next_closed_toll(remaining_tolls)
        
        if not next_closed_toll:
            print("   ℹ️ Aucun péage fermé restant à optimiser")
            return remaining_tolls
        
        # Chercher un remplacement pour ce péage
        replacement_toll = TollOptimizer._find_replacement_toll(
            next_closed_toll, identification_result
        )
        
        if replacement_toll:
            # Remplacer le péage
            optimized_tolls = remaining_tolls.copy()
            toll_index = optimized_tolls.index(next_closed_toll)
            optimized_tolls[toll_index] = replacement_toll
            
            next_name = getattr(next_closed_toll, 'osm_name', 'Inconnu')
            replacement_name = getattr(replacement_toll, 'osm_name', 'Inconnu')
            print(f"   🔧 Optimisé {next_name} → {replacement_name}")
            
            return optimized_tolls
        else:
            print("   ⚠️ Aucun remplacement trouvé pour l'optimisation")
            return remaining_tolls
    
    @staticmethod
    def _find_next_closed_toll(tolls: List):
        """Trouve le prochain péage fermé dans la liste."""
        for toll in tolls:
            if not TollOptimizer._is_open_system(toll):
                return toll
        return None
    
    @staticmethod
    def _find_replacement_toll(target_toll, identification_result: Dict):
        """Trouve un péage de remplacement géographiquement correct."""
        tolls_around = identification_result.get('tolls_around', [])
        ordered_tolls = identification_result.get('ordered_tolls', [])
        route_coordinates = identification_result.get('route_coordinates', [])
        
        if not tolls_around or not ordered_tolls or not route_coordinates:
            return TollOptimizer._fallback_replacement(tolls_around, target_toll)
        
        # Trouver la position du péage cible
        target_position = TollOptimizer._find_toll_position(target_toll, ordered_tolls)
        if target_position is None:
            return TollOptimizer._fallback_replacement(tolls_around, target_toll)
        
        # Calculer les positions des candidats
        candidates = TollOptimizer._calculate_candidate_positions(
            tolls_around, target_toll, route_coordinates
        )
        
        # Trouver le meilleur candidat après la position cible
        best_candidate = TollOptimizer._find_best_candidate_after_position(
            candidates, target_position
        )
        
        return best_candidate or TollOptimizer._fallback_replacement(tolls_around, target_toll)
    
    @staticmethod
    def _find_toll_position(target_toll, ordered_tolls: List) -> Optional[int]:
        """Trouve la position d'un péage dans ordered_tolls."""
        for item in ordered_tolls:
            toll = item.get('toll')
            if toll and TollOptimizer._tolls_are_same(toll, target_toll):
                return item.get('route_position')
        return None
    
    @staticmethod
    def _calculate_candidate_positions(tolls_around: List, target_toll, route_coordinates: List) -> List[Dict]:
        """Calcule les positions des candidats sur la route."""
        candidates = []
        
        for candidate in tolls_around:
            if TollOptimizer._tolls_are_same(candidate, target_toll):
                continue
            
            candidate_coords = TollOptimizer._get_toll_coordinates(candidate)
            if not candidate_coords:
                continue
            
            position = TollOptimizer._find_closest_point_on_route(candidate_coords, route_coordinates)
            if position is not None:
                candidates.append({
                    'toll': candidate,
                    'route_position': position,
                    'name': getattr(candidate, 'osm_name', 'Inconnu')
                })
        
        return candidates
    
    @staticmethod
    def _find_best_candidate_after_position(candidates: List[Dict], target_position: int):
        """Trouve le meilleur candidat après une position donnée."""
        best_candidate = None
        best_position = None
        
        for item in candidates:
            position = item['route_position']
            if position > target_position:
                if best_candidate is None or position < best_position:
                    best_candidate = item['toll']
                    best_position = position
        
        return best_candidate
    
    @staticmethod
    def _fallback_replacement(tolls_around: List, target_toll):
        """Remplacement de fallback simple."""
        for candidate in tolls_around:
            if not TollOptimizer._tolls_are_same(candidate, target_toll):
                return candidate
        return None
    
    @staticmethod
    def _get_toll_coordinates(toll) -> Optional[List[float]]:
        """Récupère les coordonnées d'un péage."""
        # MatchedToll
        if hasattr(toll, 'osm_coordinates'):
            return getattr(toll, 'osm_coordinates', None)
        # TollStation
        elif hasattr(toll, 'coordinates'):
            return getattr(toll, 'coordinates', None)
        return None
    
    @staticmethod
    def _find_closest_point_on_route(toll_coords: List[float], route_coordinates: List[List[float]]) -> Optional[int]:
        """Trouve le point le plus proche sur la route."""
        if not toll_coords or not route_coordinates:
            return None
        
        min_distance = float('inf')
        closest_index = 0
        
        for i, route_point in enumerate(route_coordinates):
            distance = DistanceCalculator.calculate_distance_meters(toll_coords, route_point)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        return closest_index
    
    @staticmethod
    def _tolls_are_same(toll1, toll2) -> bool:
        """Compare deux péages pour déterminer s'ils sont identiques."""
        if toll1 is toll2:
            return True
        
        if not toll1 or not toll2:
            return False
        
        # Comparaison par ID (MatchedToll)
        if hasattr(toll1, 'osm_id') and hasattr(toll2, 'osm_id'):
            return toll1.osm_id == toll2.osm_id
        
        # Comparaison par feature_id (TollStation)
        if hasattr(toll1, 'feature_id') and hasattr(toll2, 'feature_id'):
            return toll1.feature_id == toll2.feature_id
        
        # Fallback par nom
        name1 = getattr(toll1, 'osm_name', None) or getattr(toll1, 'name', None)
        name2 = getattr(toll2, 'osm_name', None) or getattr(toll2, 'name', None)
        
        if name1 and name2:
            return name1 == name2
        
        return False
    
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
