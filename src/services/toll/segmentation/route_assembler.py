"""
route_assembler.py
-----------------

Responsabilité : Assembler les segments validés en une route complète.
Gère la concaténation des géométries et le calcul des métriques globales.
"""

from src.services.common.result_formatter import ResultFormatter


class RouteAssembler:
    """
    Assembleur de routes à partir de segments.
    Responsabilité unique : combiner des segments en route finale.
    """
    
    def __init__(self):
        pass
    
    def assemble_route(self, segments, waypoints):
        """
        Assemble une liste de segments en une route complète.
        
        Args:
            segments: Liste des segments calculés
                     Format: [{'segment_data': {...}, 'success': True}, ...]
            waypoints: Points de passage originaux [départ, péage1, ..., arrivée]
            
        Returns:
            dict: Route assemblée au format standard ou None si échec
        """
        if not segments or not all(seg.get('success', False) for seg in segments):
            print("❌ Impossible d'assembler : segments invalides")
            return None
        
        print(f"🔨 Assemblage de {len(segments)} segments...")
        
        try:
            # Extraire les données de chaque segment
            segment_data_list = [seg['segment_data'] for seg in segments]
            
            # Assembler la géométrie
            assembled_geometry = self._assemble_geometry(segment_data_list)
            
            # Calculer les métriques globales
            total_distance, total_duration = self._calculate_totals(segment_data_list)
            
            # Identifier les péages de la route (ceux dans les waypoints)
            route_tolls = self._extract_route_tolls(waypoints)
              # Créer un GeoJSON Feature complet comme attendu par le frontend
            geojson_route = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature", 
                    "geometry": assembled_geometry,
                    "properties": {
                        "summary": {
                            "distance": total_distance,
                            "duration": total_duration
                        },
                        "segments": [{"distance": seg.get('distance', 0), "duration": seg.get('duration', 0)} for seg in segment_data_list],
                        "way_points": [0, len(assembled_geometry['coordinates']) - 1]  # Indices début/fin
                    }
                }],
                "metadata": {
                    "service": "routing",
                    "engine": {"version": "segmentation", "build_date": "2025-06-13"},
                    "query": {"coordinates": f"{len(waypoints)} waypoints"},
                    "attribution": "openrouteservice.org, OpenStreetMap contributors"
                },
                "bbox": self._calculate_bbox(assembled_geometry['coordinates'])
            }
            # Calculer le coût total en utilisant la logique de coût appropriée
            # Les route_tolls sont les waypoints péages, mais pour le coût il faut utiliser 
            # la logique de détection et coût des péages sur la route assemblée
            total_cost = 0  # Pour l'instant, le coût sera calculé par le système principal
            
            # TODO: Intégrer le calcul de coût des péages détectés sur la route assemblée
            # Cela nécessite d'utiliser locate_tolls et cost_tolls sur le GeoJSON final
            # Utiliser ResultFormatter pour garantir le format standard
            formatted_result = ResultFormatter.format_route_result(
                geojson_route, total_cost, total_duration, len(route_tolls)
            )
            
            print(f"✅ Route assemblée : {total_distance:.0f}m, {total_duration:.0f}s, {len(route_tolls)} péages waypoints")
            return formatted_result
            
        except Exception as e:
            print(f"❌ Erreur assemblage : {e}")
            return None
    
    def _assemble_geometry(self, segment_data_list):
        """
        Assemble les géométries des segments en une géométrie continue.
        Évite la duplication des coordonnées aux points de jonction.
        
        Args:
            segment_data_list: Liste des données de segments
            
        Returns:
            dict: Géométrie assemblée
        """
        if not segment_data_list:
            return {}
        
        # Commencer avec la géométrie du premier segment
        first_segment = segment_data_list[0]
        assembled_coordinates = first_segment['geometry'].get('coordinates', [])
        
        # Ajouter les géométries des segments suivants
        for segment_data in segment_data_list[1:]:
            segment_coords = segment_data['geometry'].get('coordinates', [])
            
            if segment_coords:
                # Ignorer le premier point (duplication avec le dernier du segment précédent)
                assembled_coordinates.extend(segment_coords[1:])
        
        return {
            'coordinates': assembled_coordinates,
            'type': 'LineString'
        }
    
    def _calculate_totals(self, segment_data_list):
        """
        Calcule les totaux de distance et durée.
        
        Args:
            segment_data_list: Liste des données de segments
            
        Returns:
            tuple: (distance_totale, duree_totale)
        """
        total_distance = sum(seg.get('distance', 0) for seg in segment_data_list)
        total_duration = sum(seg.get('duration', 0) for seg in segment_data_list)
        
        return total_distance, total_duration
    
    def _extract_route_tolls(self, waypoints):
        """
        Extrait les péages de la liste des waypoints.
        
        Args:
            waypoints: Liste des points de passage [départ, péage1, ..., arrivée]
            
        Returns:
            list: Liste des péages (objets entre départ et arrivée)
        """
        # Les péages sont tous les waypoints sauf le premier (départ) et dernier (arrivée)
        if len(waypoints) <= 2:
            return []  # Pas de péages
        
        route_tolls = []
        for waypoint in waypoints[1:-1]:  # Exclure départ et arrivée
            if isinstance(waypoint, dict):
                route_tolls.append(waypoint)
            # Si c'est juste des coordonnées, on peut pas les traiter comme péages
        
        return route_tolls
    
    def _calculate_bbox(self, coordinates):
        """
        Calcule la bounding box à partir des coordonnées.
        
        Args:
            coordinates: Liste de coordonnées [[lon, lat], ...]
            
        Returns:
            list: [min_lon, min_lat, max_lon, max_lat]
        """
        if not coordinates:
            return [0, 0, 0, 0]
        
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        return [min(lons), min(lats), max(lons), max(lats)]
