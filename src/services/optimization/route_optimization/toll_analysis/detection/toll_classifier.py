"""
Toll Classifier
===============

Classifie les péages selon leur distance à la route et les indexe par segments.
Responsabilité unique : classification et indexation des péages détectés.
"""

from typing import List, Dict, Tuple


class TollClassifier:
    """Classificateur et indexeur de péages optimisé."""
    
    # Seuils de classification (en mètres)
    ON_ROUTE_THRESHOLD = 50.0      # Péages SUR la route
    AROUND_THRESHOLD = 1000.0     # Péages AUTOUR de la route
    
    @staticmethod
    def classify_tolls_by_distance(toll_distances: List[Dict]) -> Dict:
        """
        Classifie les péages selon leur distance à la route.
        
        Args:
            toll_distances: Résultats des calculs de distance
            
        Returns:
            Dictionnaire avec péages classifiés
        """
        results = {
            'on_route': [],      # < 1m
            'around': [],        # < 1km
            'rejected': []       # > 1km
        }
        
        for item in toll_distances:
            toll = item['toll']
            distance = item['distance']
            
            if distance <= TollClassifier.ON_ROUTE_THRESHOLD:
                results['on_route'].append(item)
            elif distance <= TollClassifier.AROUND_THRESHOLD:
                results['around'].append(item)
            else:
                results['rejected'].append(item)
        
        print(f"   📊 Classification: {len(results['on_route'])} sur route, "
              f"{len(results['around'])} autour, {len(results['rejected'])} rejetés")
        
        return results
    
    @staticmethod
    def index_tolls_by_segments(
        tolls_on_route: List[Dict], 
        segments: List[Dict], 
        route_coordinates: List[List[float]]
    ) -> Dict:
        """
        Indexe les péages sur la route par segments tollways.
        
        Args:
            tolls_on_route: Péages sur la route avec leurs données
            segments: Segments tollways de la route
            route_coordinates: Coordonnées de la route
            
        Returns:
            Dictionnaire d'indexation par segments
        """
        if not segments:
            print("⚠️ Aucun segment tollway, indexation simple")
            return TollClassifier._create_simple_index(tolls_on_route)
        
        segments_mapping = {}
        
        for toll_data in tolls_on_route:
            toll = toll_data['toll']
            point_idx = toll_data['closest_point_idx']
            
            # Trouver le segment tollway correspondant
            segment_idx = TollClassifier._find_segment_for_point_index(
                point_idx, segments
            )
            
            if segment_idx not in segments_mapping:
                segments_mapping[segment_idx] = {
                    'segment_info': segments[segment_idx] if segment_idx >= 0 else None,
                    'tolls': []
                }
            
            # Ajouter le péage avec ses métadonnées
            segments_mapping[segment_idx]['tolls'].append({
                'toll': toll,
                'route_point_index': point_idx,
                'distance_to_route': toll_data['distance'],
                'segment_position': TollClassifier._calculate_segment_position(
                    point_idx, segments[segment_idx] if segment_idx >= 0 else None
                )
            })
        
        # Trier les péages dans chaque segment par ordre sur la route
        for segment_idx in segments_mapping:
            segments_mapping[segment_idx]['tolls'].sort(
                key=lambda x: x['route_point_index']
            )
        
        TollClassifier._print_segments_summary(segments_mapping)
        
        return segments_mapping
    
    @staticmethod
    def create_ordered_tolls_list(segments_mapping: Dict) -> List[Dict]:
        """
        Crée une liste ordonnée des péages selon leur position sur la route.
        
        Args:
            segments_mapping: Mapping des péages par segments
            
        Returns:
            Liste ordonnée des péages sur la route
        """
        all_tolls = []
        
        # Collecter tous les péages avec leur position
        for segment_idx, segment_data in segments_mapping.items():
            for toll_data in segment_data['tolls']:
                all_tolls.append({
                    'toll': toll_data['toll'],
                    'segment_index': segment_idx,
                    'route_position': toll_data['route_point_index'],
                    'distance_to_route': toll_data['distance_to_route']
                })
        
        # Trier par position sur la route
        all_tolls.sort(key=lambda x: x['route_position'])
        
        return all_tolls
    
    @staticmethod
    def _find_segment_for_point_index(point_idx: int, segments: List[Dict]) -> int:
        """
        Trouve le segment tollway contenant un point donné.
        
        Args:
            point_idx: Index du point sur la route
            segments: Liste des segments tollways
            
        Returns:
            Index du segment, -1 si non trouvé
        """
        if point_idx < 0 or not segments:
            return -1
        
        for i, segment in enumerate(segments):
            start_wp = segment.get('start_waypoint', 0)
            end_wp = segment.get('end_waypoint', 0)
            
            if start_wp <= point_idx <= end_wp:
                return i
        
        # Si pas trouvé, retourner le segment le plus proche
        closest_segment = -1
        min_distance = float('inf')
        
        for i, segment in enumerate(segments):
            start_wp = segment.get('start_waypoint', 0)
            end_wp = segment.get('end_waypoint', 0)
            
            # Distance au début ou à la fin du segment
            dist = min(abs(point_idx - start_wp), abs(point_idx - end_wp))
            
            if dist < min_distance:
                min_distance = dist
                closest_segment = i
        
        return closest_segment
    
    @staticmethod
    def _calculate_segment_position(point_idx: int, segment: Dict) -> float:
        """
        Calcule la position relative dans un segment (0.0 à 1.0).
        
        Args:
            point_idx: Index du point sur la route
            segment: Données du segment
            
        Returns:
            Position relative (0.0 = début, 1.0 = fin)
        """
        if not segment:
            return 0.0
        
        start_wp = segment.get('start_waypoint', 0)
        end_wp = segment.get('end_waypoint', 0)
        
        if end_wp <= start_wp:
            return 0.0
        
        relative_pos = (point_idx - start_wp) / (end_wp - start_wp)
        return max(0.0, min(1.0, relative_pos))
    
    @staticmethod
    def _create_simple_index(tolls_on_route: List[Dict]) -> Dict:
        """Crée un index simple quand il n'y a pas de segments."""
        return {
            0: {
                'segment_info': None,
                'tolls': [
                    {
                        'toll': item['toll'],
                        'route_point_index': item['closest_point_idx'],
                        'distance_to_route': item['distance'],
                        'segment_position': 0.0
                    }
                    for item in tolls_on_route
                ]
            }
        }
    
    @staticmethod
    def _print_segments_summary(segments_mapping: Dict) -> None:
        """Affiche un résumé de l'indexation par segments."""
        total_tolls = sum(len(data['tolls']) for data in segments_mapping.values())
        
        print(f"   🗂️ Indexation: {total_tolls} péages répartis sur "
              f"{len(segments_mapping)} segments")
        
        for segment_idx, data in segments_mapping.items():
            segment_info = data['segment_info']
            tolls_count = len(data['tolls'])
            
            if segment_info:
                is_toll = segment_info.get('is_toll', False)
                segment_type = 'payant' if is_toll else 'gratuit'
                print(f"      - Segment {segment_idx} ({segment_type}): {tolls_count} péages")
            else:
                print(f"      - Segment {segment_idx} (inconnu): {tolls_count} péages")
