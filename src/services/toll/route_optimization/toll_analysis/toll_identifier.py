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
    
    def identify_tolls_on_route(
        self, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict]
    ) -> Dict:
        """
        ÉTAPE 3: Identifie les péages sur la route et autour.
        
        Processus optimisé en 3 phases :
        1. Pré-filtrage spatial (R-tree)
        2. Calcul distances optimisé 
        3. Classification et indexation
        
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
        return self._classify_and_index(toll_distances, tollway_segments, route_coordinates)
    
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
            Résultats complets de l'identification
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
        
        return self._build_complete_result(
            classified, segments_mapping, ordered_tolls, tollway_segments
        )
    
    def _build_complete_result(
        self, 
        classified: Dict, 
        segments_mapping: Dict,
        ordered_tolls: List[Dict],
        tollway_segments: List[Dict]
    ) -> Dict:
        """
        Construit le résultat complet de l'identification.
        
        Args:
            classified: Péages classifiés par distance
            segments_mapping: Mapping par segments
            ordered_tolls: Liste ordonnée des péages
            tollway_segments: Segments tollways originaux
            
        Returns:
            Résultat complet formaté
        """
        # Extraire les péages pour compatibilité
        tolls_on_route = [item['toll'] for item in classified['on_route']]
        tolls_around = [item['toll'] for item in classified['around']]
        
        result = {
            # Données principales (ÉTAPE 3)
            'tolls_on_route': tolls_on_route,           # < 1m de la route
            'tolls_around': tolls_around,               # < 1km de la route  
            'segments_mapping': segments_mapping,        # Index par segments
            'ordered_tolls': ordered_tolls,             # Ordre sur la route
            
            # Métadonnées pour validation ÉTAPE 4
            'total_tolls_on_route': len(tolls_on_route),
            'total_tolls_around': len(tolls_around),
            'segments_with_tolls': len([s for s in segments_mapping.values() if s['tolls']]),
            'tollway_segments': tollway_segments,
            
            # Statistiques pour debugging
            'detection_stats': {
                'candidates_found': len(classified['on_route']) + len(classified['around']) + len(classified['rejected']),
                'on_route_count': len(tolls_on_route),
                'around_count': len(tolls_around),
                'rejected_count': len(classified['rejected']),
                'segments_analyzed': len(tollway_segments),
                'segments_with_tolls': len(segments_mapping)
            }
        }
        
        self._print_identification_summary(result)
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
                'on_route_count': 0,
                'around_count': 0,
                'rejected_count': 0,
                'segments_analyzed': 0,
                'segments_with_tolls': 0
            }
        }
    
    def _print_identification_summary(self, result: Dict) -> None:
        """Affiche un résumé de l'identification."""
        stats = result['detection_stats']
        
        print(f"✅ Identification terminée:")
        print(f"   🎯 Péages SUR la route: {stats['on_route_count']}")
        print(f"   🔄 Péages AUTOUR: {stats['around_count']}")
        print(f"   📊 Segments avec péages: {stats['segments_with_tolls']}")
        print(f"   🚫 Candidats rejetés: {stats['rejected_count']}")
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques de l'index spatial."""
        return self.spatial_index.get_index_stats()
