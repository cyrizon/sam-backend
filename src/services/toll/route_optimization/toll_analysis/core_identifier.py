"""
Core Toll Identification
=======================

Module principal pour l'identification des péages avec le nouveau système unifié.
Responsabilité : Orchestration des phases d'identification.
"""

from typing import List, Dict, Optional
from .spatial.unified_spatial_manager import UnifiedSpatialIndexManager
from .detection.distance_calculator import OptimizedDistanceCalculator
from .detection.toll_classifier import TollClassifier


class CoreTollIdentifier:
    """Identifieur de péages optimisé avec cache V2."""
    
    def __init__(self):
        """Initialise l'identifieur avec les nouveaux index unifiés."""
        self.spatial_manager = UnifiedSpatialIndexManager()
        self.distance_calculator = OptimizedDistanceCalculator() 
        self.classifier = TollClassifier()
        print("🔍 Core Toll Identifier initialisé avec cache V2")
    
    def identify_tolls_on_route(
        self, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict] = None
    ) -> Dict:
        """
        Identifie les péages sur une route donnée.
        
        Args:
            route_coordinates: Coordonnées de la route
            tollway_segments: Segments tollways (optionnel)
            
        Returns:
            Résultat d'identification avec péages détectés
        """
        print("🔍 Identification des péages sur la route...")
        
        if not self._validate_input(route_coordinates):
            return self._create_empty_result()
        
        try:
            # Phase 1: Recherche spatiale des péages proches
            nearby_tolls = self._find_nearby_tolls(route_coordinates)
            if not nearby_tolls:
                return self._create_empty_result()
            
            # Phase 2: Calcul des distances précises
            toll_distances = self._calculate_precise_distances(nearby_tolls, route_coordinates)
            
            # Phase 3: Classification et filtrage
            classified_tolls = self._classify_tolls(toll_distances)
            
            # Phase 4: Construction du résultat final
            return self._build_identification_result(classified_tolls, route_coordinates)
            
        except Exception as e:
            print(f"❌ Erreur identification péages : {e}")
            return self._create_empty_result()
    
    def _validate_input(self, route_coordinates: List[List[float]]) -> bool:
        """Valide les données d'entrée."""
        if not route_coordinates or len(route_coordinates) < 2:
            print("❌ Coordonnées de route invalides")
            return False
        return True
    
    def _find_nearby_tolls(self, route_coordinates: List[List[float]]) -> List:
        """Phase 1: Trouve les péages proches de la route."""
        print("   🗂️ Phase 1: Recherche spatiale des péages...")
        
        nearby_tolls = self.spatial_manager.get_nearby_tolls(route_coordinates)
        
        if not nearby_tolls:
            print("   ⚠️ Aucun péage trouvé dans la zone")
            return []
        
        print(f"   ✅ {len(nearby_tolls)} péages trouvés dans la zone")
        return nearby_tolls
    
    def _calculate_precise_distances(self, tolls: List, route_coordinates: List[List[float]]) -> List[Dict]:
        """Phase 2: Calcule les distances précises pour chaque péage."""
        print("   📏 Phase 2: Calcul des distances précises...")
        
        toll_distances = []
        
        for toll in tolls:
            try:
                # Utiliser les nouvelles propriétés de TollBoothStation
                toll_coords = toll.get_coordinates()
                
                # Calculer la distance minimale à la route
                min_distance = self.distance_calculator.calculate_min_distance_to_route(
                    toll_coords, route_coordinates
                )
                
                toll_distances.append({
                    'toll': toll,
                    'coordinates': toll_coords,
                    'min_distance_m': min_distance,
                    'is_on_route': min_distance <= 50,  # 50m de tolérance
                    'toll_type': 'ouvert' if toll.is_open_toll else 'fermé',
                    'operator': toll.operator or 'Inconnu'
                })
                
            except Exception as e:
                print(f"   ⚠️ Erreur calcul distance pour péage {toll.osm_id}: {e}")
                continue
        
        print(f"   ✅ Distances calculées pour {len(toll_distances)} péages")
        return toll_distances
    
    def _classify_tolls(self, toll_distances: List[Dict]) -> Dict:
        """Phase 3: Classifie les péages selon leur position."""
        print("   🏷️ Phase 3: Classification des péages...")
        
        on_route = []
        nearby = []
        
        for toll_data in toll_distances:
            if toll_data['is_on_route']:
                on_route.append(toll_data)
            elif toll_data['min_distance_m'] <= 1000:  # 1km autour
                nearby.append(toll_data)
        
        # Trier par distance
        on_route.sort(key=lambda x: x['min_distance_m'])
        nearby.sort(key=lambda x: x['min_distance_m'])
        
        print(f"   ✅ Classification : {len(on_route)} sur route, {len(nearby)} à proximité")
        
        return {
            'on_route': on_route,
            'nearby': nearby,
            'all_processed': toll_distances
        }
    
    def _build_identification_result(self, classified_tolls: Dict, route_coordinates: List[List[float]]) -> Dict:
        """Phase 4: Construit le résultat final d'identification."""
        print("   📋 Phase 4: Construction du résultat...")
        
        tolls_on_route = classified_tolls['on_route']
        nearby_tolls = classified_tolls['nearby']
        
        # Statistiques par type
        open_tolls_count = sum(1 for t in tolls_on_route if t['toll_type'] == 'ouvert')
        closed_tolls_count = sum(1 for t in tolls_on_route if t['toll_type'] == 'fermé')
        
        # Opérateurs présents
        operators = list(set(t['operator'] for t in tolls_on_route if t['operator'] != 'Inconnu'))
        
        result = {
            'identification_success': True,
            'total_tolls_on_route': len(tolls_on_route),
            'tolls_on_route': tolls_on_route,
            'nearby_tolls': nearby_tolls,
            'statistics': {
                'open_tolls': open_tolls_count,
                'closed_tolls': closed_tolls_count,
                'operators': operators,
                'total_nearby': len(nearby_tolls)
            },
            'route_info': {
                'total_points': len(route_coordinates),
                'start_point': route_coordinates[0],
                'end_point': route_coordinates[-1]
            }
        }
        
        print(f"   ✅ Identification terminée : {result['total_tolls_on_route']} péages sur route")
        return result
    
    def _create_empty_result(self) -> Dict:
        """Crée un résultat vide en cas d'échec."""
        return {
            'identification_success': False,
            'total_tolls_on_route': 0,
            'tolls_on_route': [],
            'nearby_tolls': [],
            'statistics': {
                'open_tolls': 0,
                'closed_tolls': 0,
                'operators': [],
                'total_nearby': 0
            },
            'route_info': {}
        }
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques des index spatiaux."""
        return self.spatial_manager.get_unified_stats()
