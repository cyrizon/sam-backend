"""
toll_deduplicator.py
-------------------

Module pour la déduplication des péages détectés.
Responsable d'éliminer les doublons et de garder les péages les plus proches de la route.
"""

from typing import List
from .toll_matcher import MatchedToll
from .intelligent_segmentation_helpers import RouteUtils


class TollDeduplicator:
    """
    Classe responsable de la déduplication des péages.
    Élimine les doublons et garde les péages les plus proches de la route.
    """
    
    @staticmethod
    def deduplicate_tolls_by_proximity(
        matched_tolls: List[MatchedToll], 
        route_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """
        Déduplique les péages en gardant le plus proche de la route pour chaque nom.
        
        Args:
            matched_tolls: Liste des péages matchés
            route_coords: Coordonnées de la route de base
            
        Returns:
            List[MatchedToll]: Péages dédupliqués
        """
        if not matched_tolls:
            return []
        
        print(f"🔗 Déduplication de {len(matched_tolls)} péages par proximité à la route...")
        
        # Regrouper les péages par nom effectif
        toll_groups = {}
        for toll in matched_tolls:
            name = toll.effective_name.strip().lower()
            if name not in toll_groups:
                toll_groups[name] = []
            toll_groups[name].append(toll)
        
        deduplicated_tolls = []
        
        # Pour chaque groupe, garder le péage le plus proche de la route
        for name, group in toll_groups.items():
            if len(group) == 1:
                # Un seul péage, le garder
                deduplicated_tolls.append(group[0])
                print(f"   ✅ {name} : 1 péage gardé")
            else:
                # Plusieurs péages, garder le plus proche de la route
                closest_toll = TollDeduplicator._find_closest_toll_to_route(group, route_coords)
                deduplicated_tolls.append(closest_toll)
                print(f"   ✅ {name} : {len(group)} péages → 1 gardé (le plus proche)")
        
        print(f"🎯 Péages uniques trouvés sur la route : {len(deduplicated_tolls)}")
        return deduplicated_tolls
    
    @staticmethod
    def _find_closest_toll_to_route(
        toll_group: List[MatchedToll], 
        route_coords: List[List[float]]
    ) -> MatchedToll:
        """
        Trouve le péage le plus proche de la route parmi un groupe.
        Utilise la distance point-à-polyline ET vérifie la correspondance avec les points de la route.
        
        Args:
            toll_group: Groupe de péages du même nom
            route_coords: Coordonnées de la route
            
        Returns:
            MatchedToll: Péage le plus proche et correspondant au trajet
        """
        from .polyline_intersection import point_to_polyline_distance
        
        print(f"   🔍 Déduplication de {len(toll_group)} péages du même nom:")
        
        # Première passe : trouver le péage qui correspond exactement à un point de la route
        for toll in toll_group:
            toll_lon, toll_lat = toll.osm_coordinates[0], toll.osm_coordinates[1]
            print(f"      🧪 Test péage à [{toll_lon:.7f}, {toll_lat:.7f}]")
            
            # Vérifier si ce point correspond exactement (±1m) à un point de la route
            for i, route_point in enumerate(route_coords):
                route_lon, route_lat = route_point[0], route_point[1]
                
                # Calculer la distance en mètres
                distance_m = TollDeduplicator._calculate_distance_meters([toll_lat, toll_lon], [route_lat, route_lon])
                
                if distance_m <= 1.0:  # Tolérance de 1m pour correspondance exacte
                    print(f"         ✅ Correspondance exacte trouvée avec point route {i} (distance: {distance_m:.1f}m)")
                    return toll
        
        print(f"      ⚠️ Aucune correspondance exacte trouvée, utilisation de la distance minimale")
        
        # Deuxième passe : utiliser la distance minimale comme avant
        closest_toll = None
        min_distance = float('inf')
        for toll in toll_group:
            # Utiliser la distance point-à-polyline (plus précise)
            toll_coords = [toll.osm_coordinates[1], toll.osm_coordinates[0]]  # [lat, lon]
            distance_result = point_to_polyline_distance(toll_coords, route_coords)
            distance_km = distance_result[0]  # Distance en km
            
            print(f"      📏 Péage à [{toll.osm_coordinates[0]:.7f}, {toll.osm_coordinates[1]:.7f}] : {distance_km*1000:.1f}m")
            
            if distance_km < min_distance:
                min_distance = distance_km
                closest_toll = toll
        
        print(f"      ✅ Péage sélectionné : [{closest_toll.osm_coordinates[0]:.7f}, {closest_toll.osm_coordinates[1]:.7f}] ({min_distance*1000:.1f}m)")
        return closest_toll
    
    @staticmethod
    def _calculate_distance_meters(coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance entre deux points en mètres.
        
        Args:
            coord1: Premier point [lat, lon]
            coord2: Deuxième point [lat, lon]
            
        Returns:
            float: Distance en mètres
        """
        import math
        
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371000.0 * c  # Rayon de la Terre en mètres
    
    @staticmethod
    def _calculate_distance(coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance entre deux points (formule haversine simplifiée).
        
        Args:
            coord1: Premier point [lat, lon]
            coord2: Deuxième point [lon, lat] (format OSM)
            
        Returns:
            float: Distance en kilomètres
        """
        import math
        
        lat1, lon1 = math.radians(coord2[1]), math.radians(coord2[0])  # coord2 car osm_coordinates est [lon, lat]
        lat2, lon2 = math.radians(coord1[1]), math.radians(coord1[0])  # coord1 est [lat, lon]
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371.0 * c  # Rayon de la Terre en km
    
    @staticmethod
    def sort_tolls_by_route_position(
        tolls: List[MatchedToll], 
        route_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """
        Ordonne les péages selon leur position sur la route (du début vers la fin).
        
        Args:
            tolls: Liste des péages à ordonner
            route_coords: Coordonnées de la route de base
            
        Returns:
            List[MatchedToll]: Péages ordonnés selon leur position sur la route
        """
        if not tolls or not route_coords:
            return tolls
        
        print(f"📍 Ordonnancement de {len(tolls)} péages selon leur position sur la route...")
        
        # Calculer la position de chaque péage sur la route
        toll_positions = []
        for toll in tolls:
            position = TollDeduplicator._find_toll_position_on_route(toll, route_coords)
            toll_positions.append((toll, position))
            print(f"   📍 {toll.effective_name} : position {position:.1f} km")
        
        # Trier par position croissante
        toll_positions.sort(key=lambda x: x[1])
        sorted_tolls = [toll for toll, position in toll_positions]
        
        print(f"✅ Péages ordonnés : {[toll.effective_name for toll in sorted_tolls]}")
        return sorted_tolls
    
    @staticmethod
    def _find_toll_position_on_route(
        toll: MatchedToll, 
        route_coords: List[List[float]]
    ) -> float:
        """
        Trouve la position d'un péage sur la route (distance depuis le début).
        Approche simplifiée basée sur la latitude pour l'ordonnancement nord-sud.
        
        Args:
            toll: Péage à positionner
            route_coords: Coordonnées de la route
            
        Returns:
            float: Position approximative basée sur la latitude
        """
        if not route_coords:
            return 0.0
        
        # Pour une route nord-sud, utiliser la latitude comme indicateur de position
        # Plus la latitude est élevée, plus on est au nord (début de route)
        toll_lat = toll.osm_coordinates[1]  # osm_coordinates = [lon, lat]
        
        # Normaliser par rapport aux latitudes de début et fin de route
        start_lat = route_coords[0][1]   # [lon, lat]
        end_lat = route_coords[-1][1]    # [lon, lat]
        
        if start_lat == end_lat:
            return 0.0
        
        # Calculer la position relative (0 = début, 1 = fin)
        position_ratio = (start_lat - toll_lat) / (start_lat - end_lat)
        
        # Calculer la distance totale de la route
        total_distance = 0
        for i in range(1, len(route_coords)):
            dist = TollDeduplicator._calculate_distance(
                [route_coords[i-1][1], route_coords[i-1][0]],
                [route_coords[i][1], route_coords[i][0]]
            )
            total_distance += dist
        
        # Position estimée le long de la route
        return total_distance * max(0, min(1, position_ratio))
