"""
Toll Identifier
===============

Module principal pour l'identification optimisée des péages sur une route.
Orchestrator des modules de détection spatiale et géométrique.
ÉTAPE 3 de l'algorithme d'optimisation.
"""

from typing import List, Dict, Optional, Tuple
from .spatial.spatial_index import SpatialIndexManager
from .detection.distance_calculator import OptimizedDistanceCalculator  
from .detection.toll_classifier import TollClassifier
from .verification.shapely_verifier import ShapelyVerifier


class TollIdentifier:
    """
    Identifieur de péages ultra-optimisé.
    Responsabilité : ÉTAPE 3 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise l'identifieur avec l'index spatial."""
        self.spatial_index = SpatialIndexManager()
        self.distance_calculator = OptimizedDistanceCalculator()
        self.classifier = TollClassifier()
        self.verifier = ShapelyVerifier()
    
    def identify_tolls_on_route(
        self, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict]
    ) -> Dict:
        """
        ÉTAPE 3: Identifie les péages sur la route et autour.
        
        Processus optimisé en 4 phases :
        1. Pré-filtrage spatial (R-tree)
        2. Calcul distances optimisé 
        3. Classification et indexation
        4. Vérification Shapely précise
        
        Args:
            route_coordinates: Coordonnées de la route
            tollway_segments: Segments tollways de la route
            
        Returns:
            Dictionnaire complet avec péages détectés et indexés
        """
        print("🔍 Étape 3: Identification des péages sur la route...")
        
        if not route_coordinates or len(route_coordinates) < 2:
            print("❌ Coordonnées de route invalides")
            return self._create_empty_result()
        
        # Phase 1: Pré-filtrage spatial ultra-rapide
        candidates = self._spatial_prefiltering(route_coordinates)
        if not candidates:
            print("⚠️ Aucun péage candidat trouvé")
            return self._create_empty_result()
        
        # Phase 2: Calcul distances pour tous les candidats
        toll_distances = self._calculate_distances(candidates, route_coordinates)
        if not toll_distances:
            print("❌ Échec calcul des distances")
            return self._create_empty_result()
        
        # Phase 3: Classification et indexation
        phase3_result = self._classify_and_index(toll_distances, tollway_segments, route_coordinates)
        
        # Phase 4: Vérification Shapely précise
        return self._shapely_verification(phase3_result, route_coordinates, tollway_segments)
    
    def _spatial_prefiltering(self, route_coordinates: List[List[float]]) -> List:
        """
        Phase 1: Pré-filtrage spatial avec R-tree.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des péages candidats
        """
        print("   🗂️ Phase 1: Pré-filtrage spatial R-tree...")
        
        # Requête R-tree pour la bounding box élargie
        candidates = self.spatial_index.query_bbox_candidates(route_coordinates)
        
        if not candidates:
            print("   ⚠️ Aucun candidat dans la zone géographique")
            return []
        
        print(f"   ✅ {len(candidates)} péages candidats sélectionnés")
        return candidates
    
    def _calculate_distances(
        self, 
        candidates: List, 
        route_coordinates: List[List[float]]
    ) -> List[Dict]:
        """
        Phase 2: Calcul optimisé des distances pour tous les candidats.
        
        Args:
            candidates: Péages candidats
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des résultats avec distances calculées
        """
        print("   📐 Phase 2: Calcul distances optimisées...")
        
        # Calcul par lot optimisé
        toll_distances = self.distance_calculator.batch_distance_calculation(
            candidates, route_coordinates
        )
        
        if not toll_distances:
            print("   ❌ Aucune distance calculée")
            return []
        
        print(f"   ✅ Distances calculées pour {len(toll_distances)} péages")
        return toll_distances
    
    def _classify_and_index(
        self, 
        toll_distances: List[Dict], 
        tollway_segments: List[Dict],
        route_coordinates: List[List[float]]
    ) -> Dict:
        """
        Phase 3: Classification par distance et indexation par segments.
        
        Args:
            toll_distances: Résultats des calculs de distance
            tollway_segments: Segments tollways
            route_coordinates: Coordonnées de la route
            
        Returns:
            Résultats de la phase 3 (avant vérification Shapely)
        """
        print("   📊 Phase 3: Classification et indexation...")
        
        # Classification par distance (sur route vs autour)
        classified = self.classifier.classify_tolls_by_distance(toll_distances)
        
        # Indexation des péages sur la route par segments tollways
        segments_mapping = self.classifier.index_tolls_by_segments(
            classified['on_route'], tollway_segments, route_coordinates
        )
        
        # Création de la liste ordonnée
        ordered_tolls = self.classifier.create_ordered_tolls_list(segments_mapping)
        
        return {
            'classified': classified,
            'segments_mapping': segments_mapping,
            'ordered_tolls': ordered_tolls
        }
    
    def _shapely_verification(
        self, 
        phase3_result: Dict, 
        route_coordinates: List[List[float]],
        tollway_segments: List[Dict]
    ) -> Dict:
        """
        Phase 4: Vérification Shapely précise.
        
        Args:
            phase3_result: Résultats de la phase 3
            route_coordinates: Coordonnées de la route
            tollway_segments: Segments tollways
            
        Returns:
            Résultats finaux après vérification Shapely
        """
        # Vérification Shapely de tous les péages
        shapely_result = self.verifier.verify_tolls_with_shapely(
            phase3_result['classified']['on_route'],
            phase3_result['classified']['around'],
            route_coordinates
        )
        
        # Reconstruction des segments avec les péages vérifiés Shapely
        verified_segments_mapping = self._rebuild_segments_mapping(
            shapely_result['shapely_on_route'], 
            tollway_segments, 
            route_coordinates
        )
        
        # Création liste ordonnée finale
        final_ordered_tolls = self.classifier.create_ordered_tolls_list(verified_segments_mapping)
        
        return self._build_complete_result_with_shapely(
            phase3_result, shapely_result, verified_segments_mapping, 
            final_ordered_tolls, tollway_segments
        )
    
    def _rebuild_segments_mapping(
        self, 
        shapely_on_route: List[Dict], 
        tollway_segments: List[Dict],
        route_coordinates: List[List[float]]
    ) -> Dict:
        """
        Reconstruit le mapping par segments avec les péages vérifiés Shapely.
        
        Args:
            shapely_on_route: Péages confirmés par Shapely
            tollway_segments: Segments tollways
            route_coordinates: Coordonnées route
            
        Returns:
            Nouveau mapping par segments
        """
        # Transformer format pour compatibilité avec classifier
        tolls_for_mapping = []
        for toll_data in shapely_on_route:
            toll = toll_data['toll']
            
            # Recalculer l'index du point le plus proche (approximatif)
            closest_point_idx = self._find_closest_point_index(
                toll, route_coordinates
            )
            
            tolls_for_mapping.append({
                'toll': toll,
                'closest_point_idx': closest_point_idx,
                'distance': toll_data['shapely_distance']
            })
        
        # Utiliser le classifier pour le mapping
        return self.classifier.index_tolls_by_segments(
            tolls_for_mapping, tollway_segments, route_coordinates
        )
    
    def _find_closest_point_index(self, toll, route_coordinates: List[List[float]]) -> int:
        """Trouve l'index du point le plus proche sur la route."""
        if not hasattr(toll, 'osm_coordinates') or not toll.osm_coordinates:
            return 0
        
        toll_coords = toll.osm_coordinates
        min_dist = float('inf')
        closest_idx = 0
        
        for i, route_point in enumerate(route_coordinates):
            # Distance approximative
            dx = toll_coords[0] - route_point[0]
            dy = toll_coords[1] - route_point[1]
            dist = dx*dx + dy*dy  # Distance carrée suffit pour comparaison
            
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
        
        return closest_idx
    
    def _build_complete_result_with_shapely(
        self, 
        phase3_result: Dict,
        shapely_result: Dict,
        verified_segments_mapping: Dict,
        final_ordered_tolls: List[Dict],
        tollway_segments: List[Dict]
    ) -> Dict:
        """
        Construit le résultat final avec vérification Shapely.
        
        Args:
            phase3_result: Résultats phase 3
            shapely_result: Résultats vérification Shapely
            verified_segments_mapping: Mapping final des segments
            final_ordered_tolls: Liste ordonnée finale
            tollway_segments: Segments tollways originaux
            
        Returns:
            Résultat complet formaté
        """
        # Extraire les péages finaux
        final_tolls_on_route = [item['toll'] for item in shapely_result['shapely_on_route']]
        final_tolls_around = [item['toll'] for item in shapely_result['shapely_around']]
        
        result = {
            # Données principales (ÉTAPE 3)
            'tolls_on_route': final_tolls_on_route,     # Vérifiés Shapely <5m
            'tolls_around': final_tolls_around,         # Vérifiés Shapely >=5m  
            'segments_mapping': verified_segments_mapping,  # Index par segments
            'ordered_tolls': final_ordered_tolls,       # Ordre sur la route
            
            # Métadonnées pour validation ÉTAPE 4
            'total_tolls_on_route': len(final_tolls_on_route),
            'total_tolls_around': len(final_tolls_around),
            'segments_with_tolls': len([s for s in verified_segments_mapping.values() if s['tolls']]),
            'tollway_segments': tollway_segments,
            
            # Statistiques pour debugging
            'detection_stats': {
                'candidates_found': len(phase3_result['classified']['on_route']) + len(phase3_result['classified']['around']) + len(phase3_result['classified']['rejected']),
                'phase3_on_route': len(phase3_result['classified']['on_route']),
                'phase3_around': len(phase3_result['classified']['around']),
                'phase3_rejected': len(phase3_result['classified']['rejected']),
                'final_on_route': len(final_tolls_on_route),
                'final_around': len(final_tolls_around),
                'segments_analyzed': len(tollway_segments),
                'segments_with_tolls': len(verified_segments_mapping),
                'shapely_verification': shapely_result['verification_stats']
            }
        }
        
        self._print_identification_summary_with_shapely(result)
        return result
    
    def _create_empty_result(self) -> Dict:
        """Crée un résultat vide en cas d'échec."""
        return {
            'tolls_on_route': [],
            'tolls_around': [],
            'segments_mapping': {},
            'ordered_tolls': [],
            'total_tolls_on_route': 0,
            'total_tolls_around': 0,
            'segments_with_tolls': 0,
            'tollway_segments': [],
            'detection_stats': {
                'candidates_found': 0,
                'phase3_on_route': 0,
                'phase3_around': 0,
                'phase3_rejected': 0,
                'final_on_route': 0,
                'final_around': 0,
                'segments_analyzed': 0,
                'segments_with_tolls': 0,
                'shapely_verification': {
                    'total_verified': 0,
                    'confirmed_on_route': 0,
                    'moved_to_around': 0,
                    'promoted_to_route': 0,
                    'shapely_errors': 0
                }
            }
        }
    
    def _print_identification_summary_with_shapely(self, result: Dict) -> None:
        """Affiche un résumé complet avec vérification Shapely."""
        stats = result['detection_stats']
        shapely_stats = stats['shapely_verification']
        
        print(f"✅ Identification terminée (avec vérification Shapely):")
        print(f"   🎯 Péages SUR la route (final): {stats['final_on_route']}")
        print(f"   🔄 Péages AUTOUR (final): {stats['final_around']}")
        print(f"   📊 Segments avec péages: {stats['segments_with_tolls']}")
        print(f"   🔍 Shapely: {shapely_stats['promoted_to_route']} promus, "
              f"{shapely_stats['moved_to_around']} rétrogradés")
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques de l'index spatial."""
        return self.spatial_index.get_index_stats()
