"""
tollway_segmentation_strategy.py
-------------------------------

Stratégie de visualisation des segments de péages basée sur les données tollways d'ORS.

Responsabilité : extraire et afficher les coordonnées des segments de péages.
"""

from typing import List, Dict, Optional, Tuple
from .tollway_extractor import TollwayExtractor, TollwaySegment, TollwayAnalyzer
from .tollway_alternatives_calculator import TollwayAlternativesCalculator
from .response_harmonizer import ResponseHarmonizer
from benchmark.performance_tracker import performance_tracker


class TollwaySegmentationStrategy:
    """
    Stratégie de visualisation des segments tollways d'ORS.
    Pipeline simplifié :
    1. Récupère route de base avec extra_info: ["tollways"]
    2. Extrait segments de péages depuis les données ORS
    3. Affiche les coordonnées de départ/arrivée de chaque segment
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance du service ORS pour les appels API
        """
        self.ors = ors_service
        self.extractor = TollwayExtractor()
        self.analyzer = TollwayAnalyzer()
        self.alternatives_calculator = TollwayAlternativesCalculator(ors_service)
        self.harmonizer = ResponseHarmonizer()
    
    def analyze_route_tollways(
        self, 
        coordinates: List[List[float]]
    ) -> Optional[Dict]:
        """
        Analyse une route et affiche les segments de péages avec leurs coordonnées.
        
        Args:
            coordinates: [départ, arrivée]
            
        Returns:
            dict: Résultat avec informations des segments de péages
        """
        with performance_tracker.measure_operation("tollway_analysis_strategy"):
            print(f"🧩 Analyse Tollways : extraction des segments de péages")
            
            # Étape 1 : Récupérer la route de base avec tollways
            base_route = self._get_base_route_with_tollways(coordinates)
            if not base_route:
                print("❌ Impossible de récupérer la route de base")
                return None
            
            # Étape 2 : Extraire et analyser les segments tollways
            tollway_data = self.extractor.extract_tollway_data(base_route)
            if not tollway_data:
                print("ℹ️ Aucune donnée de péage trouvée - route probablement gratuite")
                return self._format_no_tolls_result(base_route)
            
            segments = self.extractor.parse_segments(tollway_data)
            toll_segments = self.extractor.get_toll_segments_only(segments)
            
            print(f"📊 Analyse terminée : {len(toll_segments)} segments avec péages trouvés")
            # Étape 3 : Afficher les coordonnées des segments et calculer routes alternatives
            self._display_segment_coordinates(toll_segments)
              # Étape 4 : Calculer des routes sans péage pour chaque segment
            alternatives = self.alternatives_calculator.calculate_alternatives(toll_segments)
            
            # Étape 5 : Corriger le comptage des péages (grouper les segments consécutifs)
            actual_toll_count = self._count_actual_tolls(toll_segments)
            
            print(f"🔢 Comptage corrigé : {actual_toll_count} péages réels (vs {len(toll_segments)} segments)")
            
            # Étape 6 : Retourner les informations
            return self._format_analysis_result(base_route, toll_segments, tollway_data, alternatives, actual_toll_count)
    
    def _get_base_route_with_tollways(self, coordinates: List[List[float]]) -> Optional[Dict]:
        """
        Récupère la route de base avec les informations tollways.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            
        Returns:
            dict: Réponse ORS avec données tollways ou None
        """
        try:
            return self.ors.get_base_route(coordinates, include_tollways=True)
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la route de base : {e}")
            return None
    
    def _display_segment_coordinates(self, toll_segments: List[TollwaySegment]):
        """
        Affiche les coordonnées de départ et d'arrivée de chaque segment de péage.
        
        Args:
            toll_segments: Liste des segments avec péages
        """
        if not toll_segments:
            print("ℹ️ Aucun segment de péage à afficher")
            return
        
        print(f"\n📍 Coordonnées des {len(toll_segments)} segments de péages :")
        print("-" * 60)
        
        for i, segment in enumerate(toll_segments, 1):
            if segment.coordinates and len(segment.coordinates) >= 2:
                start_coord = segment.coordinates[0]  # [longitude, latitude]
                end_coord = segment.coordinates[-1]   # [longitude, latitude]
                
                print(f"Segment {i} (indices {segment.start_index}-{segment.end_index}):")
                print(f"  🟢 Début  : [{start_coord[0]:.6f}, {start_coord[1]:.6f}]")
                print(f"  🔴 Fin    : [{end_coord[0]:.6f}, {end_coord[1]:.6f}]")
                print(f"  📏 Points : {len(segment.coordinates)} coordonnées")
                print()
            else:
                print(f"Segment {i} : ❌ Coordonnées non disponibles")
                print()
    
    def _format_no_tolls_result(self, route: Dict) -> Dict:
        """
        Formate le résultat quand aucun péage n'est trouvé avec format harmonisé.
        """
        from src.services.toll.new_segmentation.response_harmonizer import ResponseHarmonizer
        
        return ResponseHarmonizer.create_standard_response(
            route=route,
            target_tolls=None,
            found_solution='no_tolls_found',
            strategy_used='tollway_analysis',
            respects_constraint=True,
            detailed_tolls=[],  # Aucun péage
            total_cost=0,  # Coût 0
            segments_info={'count': 1, 'toll_segments': 0, 'free_segments': 1}
        )
    
    def _format_analysis_result(self, route: Dict, toll_segments: List[TollwaySegment], tollway_data: Dict, alternatives: List[Dict] = None, actual_toll_count: int = None) -> Dict:
        """
        Formate le résultat de l'analyse des tollways avec harmonisation.
        
        Args:
            route: Route de base
            toll_segments: Segments avec péages
            tollway_data: Données tollways complètes
            alternatives: Routes alternatives sans péage (optionnel)
            actual_toll_count: Nombre réel de péages (optionnel)
            
        Returns:
            dict: Résultat formaté harmonisé
        """
        # Utiliser le ResponseHarmonizer pour le format standard
        from src.services.toll.new_segmentation.intelligent_segmentation_helpers import RouteUtils
        
        instructions = RouteUtils.extract_instructions(route)
        distance = self._get_route_distance(route)
        duration = self._get_route_duration(route)
        final_toll_count = actual_toll_count if actual_toll_count is not None else len(toll_segments)
        
        # Créer la réponse harmonisée
        response = self.harmonizer.create_standard_response(
            route=route,
            distance=distance,
            duration=duration,
            instructions=instructions,
            target_tolls=None,  # Pas applicable pour l'analyse
            found_solution='analysis_complete',
            strategy_used='tollway_analysis',
            toll_count_override=final_toll_count
        )
        
        # Ajouter les données spécifiques à l'analyse (en plus du format standard)
        segments_info = self._extract_segments_info(toll_segments)
        cost_summary = self.analyzer.get_toll_summary(tollway_data)
        
        response.update({
            'toll_segments': segments_info,
            'toll_segments_count': len(toll_segments),  # Pour debug
            'cost_summary': cost_summary
        })
        # Ajouter les alternatives si disponibles
        if alternatives:
            response['toll_free_alternatives'] = alternatives
            response['alternatives_count'] = len(alternatives)
        
        return response
    
    def _extract_segments_info(self, toll_segments: List[TollwaySegment]) -> List[Dict]:
        """
        Extrait les informations des segments pour le résultat.
        
        Args:
            toll_segments: Segments avec péages
            
        Returns:
            List[Dict]: Informations des segments
        """
        segments_info = []
        for i, segment in enumerate(toll_segments):
            if segment.coordinates and len(segment.coordinates) >= 2:
                segments_info.append({
                    'segment_id': i + 1,
                    'start_index': segment.start_index,
                    'end_index': segment.end_index,
                    'start_coordinates': segment.coordinates[0],
                    'end_coordinates': segment.coordinates[-1],
                    'total_points': len(segment.coordinates)
                })
        return segments_info
    
    def _get_route_distance(self, route: Dict) -> float:
        """
        Extrait la distance d'une route.
        
        Args:
            route: Réponse ORS
            
        Returns:
            float: Distance en mètres
        """
        try:            return route['features'][0]['properties']['summary']['distance']
        except (KeyError, IndexError):
            return float('inf')
    
    def _count_actual_tolls(self, toll_segments: List[TollwaySegment]) -> int:
        """
        Compte le nombre réel de péages en groupant les segments consécutifs.
        
        Args:
            toll_segments: Segments avec péages
            
        Returns:
            int: Nombre réel de péages (segments consécutifs = 1 péage)
        """
        if not toll_segments:
            return 0
        
        # Trier les segments par index de début
        sorted_segments = sorted(toll_segments, key=lambda s: s.start_index)
        
        toll_count = 1  # Premier segment = premier péage
        
        for i in range(1, len(sorted_segments)):
            current_segment = sorted_segments[i]
            previous_segment = sorted_segments[i-1]
            
            # Si il y a un gap entre les segments, c'est un nouveau péage
            # Tolérance de quelques points pour gérer les petites interruptions
            gap = current_segment.start_index - previous_segment.end_index
            if gap > 5:  # Plus de 5 points d'écart = nouveau péage
                toll_count += 1
        
        return toll_count
    
    def _get_route_duration(self, route: Dict) -> float:
        """
        Extrait la durée d'une route.
        
        Args:
            route: Réponse ORS
            
        Returns:
            float: Durée en secondes
        """
        try:
            return route['features'][0]['properties']['summary']['duration']
        except (KeyError, IndexError):
            return float('inf')
  
