"""
hybrid_segmenter.py
------------------

Gestionnaire principal de la segmentation hybride.
Combine les stratégies tollways et optimisation de sortie.

Responsabilité unique :
- Orchestrer la segmentation hybride
- Utiliser tollways pour les cas simples
- Appliquer l'optimisation de sortie pour les cas complexes
- Assembler les segments finaux
"""

from typing import List, Dict, Optional
from src.services.toll.new_segmentation.hybrid_strategy.tollways_analyzer import TollwaysAnalyzer
from src.services.toll.new_segmentation.hybrid_strategy.segment_avoidance_manager import SegmentAvoidanceManager
from src.services.toll.new_segmentation.toll_matcher import MatchedToll


class HybridSegmenter:
    """Gestionnaire principal de la segmentation hybride."""
    
    def __init__(self, ors_service, exit_optimizer, osm_parser=None):
        """
        Initialise le segmenteur hybride.
        
        Args:
            ors_service: Service ORS
            exit_optimizer: Gestionnaire d'optimisation de sortie
            osm_parser: Parser OSM (récupéré du cache si None)
        """
        self.ors = ors_service
        self.exit_optimizer = exit_optimizer
        
        if osm_parser is None:
            from src.services.osm_data_cache import osm_data_cache
            self.osm_parser = osm_data_cache._osm_parser
        else:
            self.osm_parser = osm_parser
        
        self.tollways_analyzer = TollwaysAnalyzer()
        self.avoidance_manager = SegmentAvoidanceManager(ors_service, self.osm_parser)
    
    def create_hybrid_segments(
        self,
        coordinates: List[List[float]],
        tollways_data: Dict,
        tolls_on_route: List[MatchedToll],
        selected_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Crée les segments en utilisant la stratégie hybride.
        
        Args:
            coordinates: [départ, arrivée]
            tollways_data: Données des segments tollways
            tolls_on_route: Tous les péages sur la route
            selected_tolls: Péages sélectionnés à utiliser
            route_coords: Coordonnées de la route complète
            
        Returns:
            List[Dict]: Segments hybrides calculés
        """
        print("🔧 Segmentation hybride tollways + optimisation...")
        
        # Étape 1 : Analyser les segments tollways
        analysis = self.tollways_analyzer.analyze_segments_for_tolls(
            tollways_data['segments'], tolls_on_route, route_coords
        )
        
        # Étape 2 : Identifier les stratégies d'évitement
        strategies = self.tollways_analyzer.identify_avoidance_strategy(analysis, selected_tolls)
        
        # Étape 3 : Appliquer l'optimisation de sortie pour les cas complexes
        optimized_tolls = self._apply_exit_optimization(strategies, selected_tolls, route_coords)
        
        # Étape 4 : Créer les segments d'évitement basés sur tollways
        avoidance_segments = self.avoidance_manager.create_avoidance_segments(
            tollways_data['segments'],
            strategies['segments_to_avoid'],
            route_coords,
            coordinates[0],
            coordinates[1]
        )
        
        # Étape 5 : Combiner tous les segments
        final_segments = self._combine_all_segments(
            avoidance_segments, optimized_tolls, coordinates, route_coords
        )
        
        print(f"   ✅ {len(final_segments)} segments hybrides créés")
        return final_segments
    
    def _apply_exit_optimization(
        self,
        strategies: Dict,
        selected_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """
        Applique l'optimisation de sortie pour les cas complexes.
        
        Args:
            strategies: Stratégies d'évitement identifiées
            selected_tolls: Péages sélectionnés originaux
            route_coords: Coordonnées de la route
            
        Returns:
            List[MatchedToll]: Péages optimisés
        """
        if not strategies['exit_optimization']:
            print("   ✅ Aucune optimisation de sortie nécessaire")
            return selected_tolls
        
        print(f"   🔄 Optimisation de sortie pour {len(strategies['exit_optimization'])} cas complexes...")
        
        optimized_tolls = selected_tolls.copy()
        
        for strategy_info in strategies['exit_optimization']:
            tolls_to_use = strategy_info['tolls_to_use']
            tolls_to_avoid = strategy_info['tolls_to_avoid']
            
            print(f"      🎯 Segment complexe : {len(tolls_to_use)} à utiliser, {len(tolls_to_avoid)} à éviter")
            
            # Pour chaque péage à utiliser dans ce segment, l'optimiser
            for toll_to_optimize in tolls_to_use:
                # Trouver le péage précédent pour délimiter la recherche
                toll_index = optimized_tolls.index(toll_to_optimize)
                previous_toll = optimized_tolls[toll_index - 1] if toll_index > 0 else None
                
                # Appliquer l'optimisation de sortie
                optimized_toll = self.exit_optimizer.optimize_toll_exit(
                    toll_to_optimize,
                    tolls_to_avoid,  # Péages restants = péages à éviter
                    route_coords[-1],  # Destination = fin de route
                    previous_toll,
                    route_coords
                )
                
                if optimized_toll:
                    # Remplacer dans la liste
                    optimized_tolls[toll_index] = optimized_toll
                    print(f"         ✅ {toll_to_optimize.effective_name} → {optimized_toll.effective_name}")
                else:
                    print(f"         ❌ Optimisation échouée pour {toll_to_optimize.effective_name}")
        
        return optimized_tolls
    
    def _combine_all_segments(
        self,
        avoidance_segments: List[Dict],
        optimized_tolls: List[MatchedToll],
        coordinates: List[List[float]],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Combine tous les segments en une liste finale cohérente.
        
        Args:
            avoidance_segments: Segments d'évitement créés
            optimized_tolls: Péages optimisés
            coordinates: [départ, arrivée]
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Segments finaux
        """
        print("   🔗 Combinaison des segments...")
        
        final_segments = []
        current_position = coordinates[0]
        
        # Si on a des segments d'évitement, les utiliser
        if avoidance_segments:
            for segment in avoidance_segments:
                if segment['type'] == 'avoidance':
                    # Segment d'évitement → Route sans péage
                    final_segments.append({
                        'type': 'toll_free',
                        'start': current_position,
                        'end': segment['end_coord'],
                        'description': f"Évitement ({segment['strategy']})"
                    })
                    current_position = segment['end_coord']
                    
                elif segment['type'] == 'normal':
                    # Segment normal → Peut contenir des péages sélectionnés
                    toll_in_segment = self._find_toll_in_coordinates(
                        optimized_tolls, segment['coordinates']
                    )
                    
                    if toll_in_segment:
                        final_segments.append({
                            'type': 'toll_segment',
                            'start': current_position,
                            'end': self._get_toll_coordinates(toll_in_segment),
                            'toll': toll_in_segment,
                            'description': f"Vers {toll_in_segment.effective_name}"
                        })
                        current_position = self._get_toll_coordinates(toll_in_segment)
                    else:
                        final_segments.append({
                            'type': 'normal',
                            'start': current_position,
                            'end': segment['end_coord'],
                            'description': "Segment normal"
                        })
                        current_position = segment['end_coord']
        
        else:
            # Fallback : Créer des segments simples basés sur les péages optimisés
            for toll in optimized_tolls:
                toll_coords = self._get_toll_coordinates(toll)
                final_segments.append({
                    'type': 'toll_segment',
                    'start': current_position,
                    'end': toll_coords,
                    'toll': toll,
                    'description': f"Vers {toll.effective_name}"
                })
                current_position = toll_coords
        
        # Segment final vers la destination
        if current_position != coordinates[1]:
            final_segments.append({
                'type': 'final',
                'start': current_position,
                'end': coordinates[1],
                'description': "Vers destination"
            })
        
        return final_segments
    
    def _find_toll_in_coordinates(
        self,
        tolls: List[MatchedToll],
        segment_coords: List[List[float]]
    ) -> Optional[MatchedToll]:
        """Trouve un péage dans les coordonnées d'un segment."""
        for toll in tolls:
            toll_coords = self._get_toll_coordinates(toll)
            if not toll_coords:
                continue
                
            # Vérifier si le péage est proche des coordonnées du segment
            for coord in segment_coords:
                distance = self._calculate_distance(toll_coords, coord)
                if distance < 0.001:  # ~100m
                    return toll
        
        return None
    
    def _get_toll_coordinates(self, toll: MatchedToll) -> List[float]:
        """Récupère les coordonnées d'un péage."""
        if hasattr(toll, 'exit_coordinates') and toll.exit_coordinates:
            return toll.exit_coordinates
        return toll.osm_coordinates or toll.csv_coordinates or [0, 0]
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calcule la distance entre deux points."""
        lat_diff = point1[1] - point2[1]
        lon_diff = point1[0] - point2[0]
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5
