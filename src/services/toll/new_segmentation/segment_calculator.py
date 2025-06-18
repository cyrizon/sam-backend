"""
segment_calculator.py
--------------------

Module pour calculer les segments de route avec/sans péages.
Responsable du calcul des routes ORS pour chaque segment.
"""

from typing import List, Dict, Optional


class SegmentCalculator:
    """
    Classe responsable du calcul des segments de route
    avec ou sans péages selon la stratégie.
    """
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
    
    def create_segments_coordinates(
        self, 
        original_coordinates: List[List[float]], 
        segmentation_points: List
    ) -> List[List[List[float]]]:
        """
        Crée la liste des coordonnées pour tous les segments.
        
        Args:
            original_coordinates: Coordonnées originales [départ, arrivée]
            segmentation_points: Points de segmentation (motorway_links)
            
        Returns:
            List[List[List[float]]]: Liste des coordonnées pour chaque segment
        """
        print("📐 Création des segments...")
        
        if not segmentation_points:
            # Pas de segmentation, retourner juste le trajet original
            return [original_coordinates]
        
        segments_coords = []
        current_start = original_coordinates[0]  # Point de départ
          # Créer un segment pour chaque point de segmentation
        for i, seg_point in enumerate(segmentation_points):
            # Utiliser le point de début du motorway_link comme point de segmentation
            segment_end = seg_point.get_start_point()
            segment_coords = [current_start, segment_end]
            segments_coords.append(segment_coords)
            print(f"   📍 Segment {i+1} : {current_start} → {segment_end}")
            
            # Le prochain segment commence où le précédent se termine
            current_start = segment_end
        
        # Dernier segment : du dernier point de segmentation à l'arrivée
        final_segment = [current_start, original_coordinates[1]]
        segments_coords.append(final_segment)
        print(f"   📍 Segment final : {current_start} → {original_coordinates[1]}")
        
        print(f"✅ {len(segments_coords)} segment(s) créé(s)")
        return segments_coords

    def calculate_all_segments(
        self, 
        segments_coords: List[List[List[float]]], 
        selected_tolls_count: int
    ) -> Optional[List[Dict]]:
        """
        Calcule tous les segments avec/sans péages.
        
        Args:
            segments_coords: Coordonnées de tous les segments
            selected_tolls_count: Nombre de péages sélectionnés
            
        Returns:
            Optional[List[Dict]]: Segments calculés ou None si échec
        """
        print(f"🛣️ Calcul de {len(segments_coords)} segment(s)...")
        
        calculated_segments = []
        
        for i, segment_coords in enumerate(segments_coords):
            try:
                # Logique : les premiers segments utilisent les péages, les derniers les évitent
                if i < selected_tolls_count:
                    print(f"   🚗 Segment {i+1} : AVEC péages...")
                    segment = self.ors.get_base_route(segment_coords, include_tollways=True)
                else:
                    print(f"   🚫 Segment {i+1} : SANS péages...")
                    segment = self.ors.get_route_avoid_tollways(segment_coords)
                
                if segment:
                    calculated_segments.append(segment)
                    print(f"   ✅ Segment {i+1} calculé")
                else:
                    print(f"   ❌ Échec segment {i+1}")
                    return None
                    
            except Exception as e:
                print(f"❌ Erreur segment {i+1} : {e}")
                return None
        
        print(f"✅ Tous les {len(calculated_segments)} segments calculés")
        return calculated_segments
