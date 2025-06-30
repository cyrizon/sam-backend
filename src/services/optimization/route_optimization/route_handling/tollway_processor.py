"""
Tollway Processor
================

Traite les segments tollways pour fusionner les petits segments.
Évite la fragmentation excessive des segments tollways.
"""

from typing import List, Dict


class TollwayProcessor:
    """Processeur de segments tollways."""
    
    @staticmethod
    def merge_small_segments(segments: List[Dict], min_waypoints: int = 50) -> List[Dict]:
        """
        Fusionne les petits segments tollways (<min_waypoints) avec le segment précédent payant.
        
        Args:
            segments: Liste des segments tollways
            min_waypoints: Nombre minimum de waypoints pour un segment
            
        Returns:
            Liste des segments après fusion
        """
        if not segments:
            return []
        
        merged_segments = []
        
        for i, segment in enumerate(segments):
            start_wp = segment.get('start_waypoint')
            end_wp = segment.get('end_waypoint')
            
            # Calculer le nombre de waypoints
            waypoints_count = None
            if start_wp is not None and end_wp is not None:
                waypoints_count = end_wp - start_wp
            
            # Vérifier si le segment est trop petit
            should_merge = (
                waypoints_count is not None and 
                waypoints_count < min_waypoints and 
                i > 0 and 
                merged_segments  # S'assurer qu'il y a un segment précédent
            )
            
            if should_merge:
                previous_segment = merged_segments[-1]
                
                # Fusionner seulement si le segment précédent est payant
                if previous_segment.get('is_toll', False):
                    print(f"   🔗 Fusion petit segment {i} ({waypoints_count} waypoints) "
                          f"avec segment précédent payant")
                    
                    # Étendre le segment précédent
                    previous_segment['end_waypoint'] = segment.get(
                        'end_waypoint', 
                        previous_segment.get('end_waypoint')
                    )
                    previous_segment['segment_type'] = 'toll'
                    continue  # Ne pas ajouter ce segment
                else:
                    # Segment précédent gratuit, ajouter normalement
                    merged_segments.append(segment)
            else:
                # Segment normal, ajouter tel quel
                merged_segments.append(segment)
        
        print(f"   📊 Segments tollways : {len(segments)} → {len(merged_segments)} "
              f"après fusion (seuil: {min_waypoints} waypoints)")
        
        return merged_segments
    
    @staticmethod
    def analyze_segments(segments: List[Dict]) -> Dict:
        """
        Analyse les segments tollways pour fournir des statistiques.
        
        Args:
            segments: Liste des segments tollways
            
        Returns:
            Dictionnaire avec les statistiques des segments
        """
        if not segments:
            return {
                'total_segments': 0,
                'toll_segments': 0,
                'free_segments': 0,
                'total_waypoints': 0,
                'avg_waypoints_per_segment': 0
            }
        
        toll_segments = sum(1 for s in segments if s.get('is_toll', False))
        free_segments = len(segments) - toll_segments
        
        total_waypoints = 0
        for segment in segments:
            start_wp = segment.get('start_waypoint', 0)
            end_wp = segment.get('end_waypoint', 0)
            total_waypoints += max(0, end_wp - start_wp)
        
        avg_waypoints = total_waypoints / len(segments) if segments else 0
        
        return {
            'total_segments': len(segments),
            'toll_segments': toll_segments,
            'free_segments': free_segments,
            'total_waypoints': total_waypoints,
            'avg_waypoints_per_segment': round(avg_waypoints, 1)
        }
    
    @staticmethod
    def validate_segments(segments: List[Dict]) -> bool:
        """
        Valide la cohérence des segments tollways.
        
        Args:
            segments: Liste des segments tollways
            
        Returns:
            True si les segments sont valides, False sinon
        """
        if not segments:
            return True
        
        for i, segment in enumerate(segments):
            # Vérifier les champs obligatoires
            if 'start_waypoint' not in segment or 'end_waypoint' not in segment:
                print(f"❌ Segment {i}: waypoints manquants")
                return False
            
            if 'is_toll' not in segment:
                print(f"❌ Segment {i}: flag is_toll manquant")
                return False
            
            # Vérifier la cohérence des waypoints
            start_wp = segment['start_waypoint']
            end_wp = segment['end_waypoint']
            
            if start_wp >= end_wp:
                print(f"❌ Segment {i}: waypoints incohérents ({start_wp} >= {end_wp})")
                return False
            
            # Vérifier la continuité avec le segment suivant
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                next_start = next_segment.get('start_waypoint')
                
                if next_start is not None and end_wp != next_start:
                    print(f"❌ Segments {i}-{i+1}: discontinuité ({end_wp} != {next_start})")
                    return False
        
        return True
