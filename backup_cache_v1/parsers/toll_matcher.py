"""
Toll Matcher
-----------

Matches OSM toll stations with CSV toll data for cost information.
Refactored from toll_matcher.py with <300 lines.
"""

import math
from typing import List, Dict
from pyproj import Transformer

from ..models.matched_toll import MatchedToll


class TollMatcher:
    """
    Classe pour matcher les péages OSM avec les données CSV.
    """
    
    def __init__(self):
        """Initialise le matcher avec les données de barrières cachées."""
        self.barriers_df = None
        self.spatial_index = None
    
    def _ensure_barriers_loaded(self):
        """Assure que les données de barrières sont chargées (lazy loading)."""
        if self.barriers_df is None:
            try:
                from ...services.toll_locator import _get_barriers_from_cache
                self.barriers_df, self.spatial_index = _get_barriers_from_cache()
                print(f"📊 Barrières chargées : {len(self.barriers_df)} péages disponibles")
            except Exception as e:
                print(f"❌ Erreur chargement barrières : {e}")
                self.barriers_df = None
                self.spatial_index = None
    
    def match_osm_tolls_with_csv(
        self, 
        osm_tolls: List[Dict], 
        max_distance_km: float = 5.0
    ) -> List[MatchedToll]:
        """
        Matche les péages OSM avec les données CSV par proximité géographique.
        
        Args:
            osm_tolls: Liste des péages OSM avec format 
                      [{"id": "way/123", "name": "...", "coordinates": [lon, lat]}]
            max_distance_km: Distance maximale pour considérer un match
            
        Returns:
            List[MatchedToll]: Péages matchés avec leurs données combinées
        """
        self._ensure_barriers_loaded()
        
        if self.barriers_df is None:
            print("❌ Données de barrières non disponibles")
            return []
        
        matched_tolls = []
        wgs_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        
        print(f"🔗 Matching de {len(osm_tolls)} péages OSM avec les données CSV...")
        
        for osm_toll in osm_tolls:
            matched_toll = self._match_single_toll(osm_toll, max_distance_km, wgs_to_3857)
            if matched_toll:
                matched_tolls.append(matched_toll)
        
        return matched_tolls
    
    def _match_single_toll(self, osm_toll: Dict, max_distance_km: float, 
                          wgs_to_3857: Transformer) -> MatchedToll:
        """Matche un seul péage OSM avec les données CSV."""
        osm_coords = osm_toll.get('coordinates', [])
        if not osm_coords or len(osm_coords) != 2:
            return None
        
        # Convertir les coordonnées OSM en Web Mercator
        osm_x, osm_y = wgs_to_3857.transform(osm_coords[0], osm_coords[1])
        
        # Chercher le péage CSV le plus proche
        best_match = None
        min_distance = float('inf')
        
        for idx, row in self.barriers_df.iterrows():
            csv_geom = row['_geom3857']
            distance_m = math.sqrt((osm_x - csv_geom.x)**2 + (osm_y - csv_geom.y)**2)
            
            if distance_m < min_distance and distance_m <= (max_distance_km * 1000):
                min_distance = distance_m
                best_match = row
        
        if best_match is not None:
            # Convertir les coordonnées CSV vers WGS84
            to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
            csv_lon, csv_lat = to_wgs84.transform(
                best_match['_geom3857'].x, 
                best_match['_geom3857'].y
            )
            
            # Calculer la confiance
            confidence = max(0.0, 1.0 - (min_distance / (max_distance_km * 1000)))
            
            return MatchedToll(
                osm_id=osm_toll.get('id', ''),
                osm_name=osm_toll.get('name'),
                osm_coordinates=osm_coords,
                csv_id=best_match['id'],
                csv_name=best_match.get('name_base', ''),
                csv_role=best_match.get('role', ''),
                csv_coordinates=[csv_lon, csv_lat],
                distance_m=min_distance,
                confidence=confidence
            )
        
        return None
    
    def filter_open_system_tolls(self, matched_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """Filtre les péages à système ouvert."""
        open_tolls = [toll for toll in matched_tolls if toll.is_open_system]
        
        print(f"🎯 Péages à système ouvert : {len(open_tolls)}/{len(matched_tolls)}")
        for toll in open_tolls:
            print(f"   🟢 {toll.effective_name} ({toll.csv_id})")
        
        return open_tolls
    
    def deduplicate_tolls(self, matched_tolls: List[MatchedToll], 
                         max_distance_m: float = 100) -> List[MatchedToll]:
        """Élimine les doublons de péages basés sur leur nom CSV et leur proximité."""
        if not matched_tolls:
            return matched_tolls
        
        print(f"🔄 Déduplication de {len(matched_tolls)} péages...")
        
        # Regrouper par nom CSV
        toll_groups = {}
        unmatched_osm = []
        
        for toll in matched_tolls:
            if toll.csv_name and toll.csv_id:
                if toll.csv_name not in toll_groups:
                    toll_groups[toll.csv_name] = []
                toll_groups[toll.csv_name].append(toll)
            else:
                unmatched_osm.append(toll)
        
        # Pour chaque groupe, garder le meilleur match
        deduplicated = []
        
        for group_name, group_tolls in toll_groups.items():
            if len(group_tolls) == 1:
                deduplicated.append(group_tolls[0])
            else:
                # Garder celui avec la plus petite distance
                best_toll = min(group_tolls, key=lambda t: t.distance_m)
                deduplicated.append(best_toll)
        
        print(f"✅ Déduplication terminée : {len(matched_tolls)} → {len(deduplicated)} péages")
        return deduplicated
    
    def deduplicate_tolls_by_proximity(self, matched_tolls: List[MatchedToll], 
                                     route_coords: List[List[float]]) -> List[MatchedToll]:
        """
        Regroupe les péages par nom effectif et garde seulement celui le plus proche de la route.
        """
        if not matched_tolls or not route_coords:
            return matched_tolls
        
        print(f"🔧 Déduplication de {len(matched_tolls)} péages par proximité...")
        
        # Regrouper par nom effectif
        toll_groups = {}
        for toll in matched_tolls:
            name = toll.effective_name
            if name not in toll_groups:
                toll_groups[name] = []
            toll_groups[name].append(toll)
        
        deduplicated = []
        for name, group in toll_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
                print(f"   📍 {name} : 1 péage conservé")
            else:
                # Garder le premier par défaut (ou implémenter logique de proximité)
                best_toll = group[0]
                deduplicated.append(best_toll)
                print(f"   📍 {name} : {len(group)} péages → 1 conservé")
        
        print(f"✅ {len(matched_tolls)} → {len(deduplicated)} péages après déduplication")
        return deduplicated


def convert_osm_tolls_to_matched_format(osm_toll_stations: List) -> List[Dict]:
    """
    Convertit les TollStation OSM au format attendu par le matcher.
    
    Args:
        osm_toll_stations: Liste de TollStation du parseur OSM
        
    Returns:
        List[Dict]: Format compatible avec le matcher
    """
    converted = []
    
    for toll in osm_toll_stations:
        converted.append({
            'id': toll.feature_id,
            'name': toll.name,
            'coordinates': toll.coordinates  # [lon, lat]
        })
    
    return converted
