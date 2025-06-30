"""
Toll Replacement Engine
======================

Moteur principal pour le remplacement des péages fermés par des entrées optimales.
Orchestre EntryFinder et RouteProximityAnalyzer pour une sélection intelligente.
"""

from typing import List, Optional, Dict, Any
from .entry_finder import EntryFinder
from .route_proximity_analyzer import RouteProximityAnalyzer
from src.cache.models.complete_motorway_link import CompleteMotorwayLink


class TollReplacementEngine:
    """
    Responsabilité : Orchestrer le remplacement intelligent des péages fermés.
    Combine recherche d'entrées et analyse de proximité pour une sélection optimale.
    """
    
    def __init__(self):
        """Initialise le moteur de remplacement."""
        self.entry_finder = EntryFinder()
        self.proximity_analyzer = RouteProximityAnalyzer()
    
    def replace_closed_toll_with_entry(
        self, 
        toll_to_replace: Dict[str, Any],
        route_coordinates: List[List[float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Remplace un péage fermé par une entrée d'autoroute optimale.
        
        Args:
            toll_to_replace: Données du péage à remplacer
            route_coordinates: Coordonnées de la route de base
            
        Returns:
            Données de l'entrée de remplacement ou None
        """
        if not toll_to_replace or not route_coordinates:
            return None
        
        toll_coords = toll_to_replace.get('coordinates', [])
        if not toll_coords or len(toll_coords) != 2:
            return None
        
        # Étape 1: Trouver les entrées après le péage cible
        entries_after_toll = self.entry_finder.find_entries_after_position(
            route_coordinates, toll_coords
        )
        
        if not entries_after_toll:
            print(f"⚠️ Aucune entrée trouvée après le péage {toll_to_replace.get('name', 'Unknown')}")
            return None
        
        # Étape 2: Sélectionner la meilleure entrée
        candidate_entries = [entry for entry, _ in entries_after_toll]
        best_replacement = self.proximity_analyzer.find_best_replacement_entry(
            candidate_entries, toll_coords, route_coordinates
        )
        
        if not best_replacement:
            print(f"❌ Aucune entrée valide pour remplacer {toll_to_replace.get('name', 'Unknown')}")
            return None
        
        best_entry, score = best_replacement
        
        # Étape 3: Formater le résultat de remplacement
        return self._format_replacement_result(
            toll_to_replace, best_entry, score
        )
    
    def batch_replace_tolls(
        self, 
        tolls_to_replace: List[Dict[str, Any]],
        route_coordinates: List[List[float]]
    ) -> List[Dict[str, Any]]:
        """
        Remplace plusieurs péages en lot.
        
        Args:
            tolls_to_replace: Liste des péages à remplacer
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des remplacements effectués
        """
        replacements = []
        
        for toll in tolls_to_replace:
            replacement = self.replace_closed_toll_with_entry(toll, route_coordinates)
            if replacement:
                replacements.append(replacement)
        
        return replacements
    
    def validate_replacement_feasibility(
        self, 
        route_coordinates: List[List[float]]
    ) -> Dict[str, Any]:
        """
        Valide la faisabilité des remplacements pour une route donnée.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Rapport de faisabilité
        """
        # Statistiques sur les entrées disponibles
        entry_stats = self.entry_finder.get_entry_statistics(route_coordinates)
        
        return {
            'feasible': entry_stats['total_entries_found'] > 0,
            'available_entries': entry_stats['total_entries_found'],
            'entries_with_tolls': entry_stats['entries_with_tolls'],
            'operators_available': len(entry_stats['operators']),
            'buffer_meters': entry_stats['buffer_used_meters'],
            'recommendation': self._get_feasibility_recommendation(entry_stats)
        }
    
    def _format_replacement_result(
        self, 
        original_toll: Dict[str, Any],
        replacement_entry: CompleteMotorwayLink,
        score: float
    ) -> Dict[str, Any]:
        """
        Formate le résultat d'un remplacement.
        
        Args:
            original_toll: Péage original
            replacement_entry: Entrée de remplacement
            score: Score de pertinence
            
        Returns:
            Résultat formaté
        """
        replacement_toll = replacement_entry.associated_toll
        
        return {
            'type': 'replacement',
            'original_toll': {
                'name': original_toll.get('name', 'Unknown'),
                'coordinates': original_toll.get('coordinates', []),
                'toll_type': original_toll.get('toll_type', 'Unknown')
            },
            'replacement_entry': {
                'link_id': replacement_entry.link_id,
                'coordinates': replacement_entry.get_start_point(),
                'toll_name': replacement_toll.name if replacement_toll else 'Unknown',
                'operator': replacement_toll.operator if replacement_toll else 'Unknown',
                'toll_type': replacement_toll.toll_type if replacement_toll else 'Unknown'
            },
            'replacement_score': round(score, 3),
            'replacement_reason': 'Optimisation péage fermé vers entrée',
            'success': True
        }
    
    def _get_feasibility_recommendation(self, entry_stats: Dict[str, Any]) -> str:
        """
        Génère une recommandation basée sur les statistiques d'entrées.
        
        Args:
            entry_stats: Statistiques des entrées trouvées
            
        Returns:
            Recommandation textuelle
        """
        total_entries = entry_stats['total_entries_found']
        entries_with_tolls = entry_stats['entries_with_tolls']
        
        if total_entries == 0:
            return "Aucune entrée trouvée - remplacement impossible"
        elif entries_with_tolls == 0:
            return "Entrées trouvées mais sans péages - remplacement limité"
        elif entries_with_tolls < 3:
            return "Peu d'entrées avec péages - options limitées"
        else:
            return "Bonnes options de remplacement disponibles"
