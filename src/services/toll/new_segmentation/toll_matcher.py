"""
toll_matcher.py
--------------

Module pour matcher les péages OSM (GeoJSON) avec les péages CSV pour récupérer les coûts.
Utilise la proximité géographique pour associer les péages.

Responsabilité : 
- Associer les péages OSM avec les données de coût des CSV
- Identifier les péages à système ouvert (1 péage = 1 paiement)
- Fournir les informations de coût pour l'optimisation
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math
from pathlib import Path

# Importation du toll_locator existant pour utiliser le cache des barrières
from src.services.toll_locator import _get_barriers_from_cache
from pyproj import Transformer


@dataclass
class MatchedToll:
    """
    Péage matché avec ses données OSM et CSV.
    """
    # Données OSM
    osm_id: str
    osm_name: Optional[str]
    osm_coordinates: List[float]  # [lon, lat] WGS84
    
    # Données CSV matchées
    csv_id: Optional[str]
    csv_name: Optional[str]
    csv_role: Optional[str]  # 'O' pour ouvert, 'F' pour fermé
    csv_coordinates: Optional[List[float]]  # [lon, lat] WGS84
    
    # Métadonnées du matching
    distance_m: float  # Distance entre OSM et CSV en mètres
    confidence: float  # Confiance du matching (0-1)
    
    @property
    def is_open_system(self) -> bool:
        """Retourne True si c'est un péage à système ouvert."""
        return self.csv_role == 'O'
    
    @property
    def effective_name(self) -> str:
        """Retourne le nom le plus pertinent."""
        return self.csv_name or self.osm_name or f"Péage {self.osm_id}"


class TollMatcher:
    """
    Classe pour matcher les péages OSM avec les données CSV.
    """
    
    def __init__(self):
        """Initialise le matcher avec les données de barrières cachées."""
        self.barriers_df = None
        self.spatial_index = None
        self._load_barriers_from_cache()
    
    def _load_barriers_from_cache(self):
        """Charge les données de barrières depuis le cache global."""
        try:
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
        if self.barriers_df is None:
            print("❌ Données de barrières non disponibles")
            return []
        
        matched_tolls = []
        
        # Transformer pour calculs de distance
        wgs_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        
        print(f"🔗 Matching de {len(osm_tolls)} péages OSM avec les données CSV...")
        
        for osm_toll in osm_tolls:
            osm_coords = osm_toll.get('coordinates', [])
            if not osm_coords or len(osm_coords) != 2:
                continue
            
            # Convertir les coordonnées OSM en Web Mercator
            osm_x, osm_y = wgs_to_3857.transform(osm_coords[0], osm_coords[1])
            
            # Chercher le péage CSV le plus proche
            best_match = None
            min_distance = float('inf')
            
            for idx, row in self.barriers_df.iterrows():
                # Calculer la distance en mètres (déjà en Web Mercator)
                csv_geom = row['_geom3857']
                distance_m = math.sqrt((osm_x - csv_geom.x)**2 + (osm_y - csv_geom.y)**2)
                
                if distance_m < min_distance and distance_m <= (max_distance_km * 1000):
                    min_distance = distance_m
                    best_match = row
            
            # Créer le péage matché
            if best_match is not None:
                # Convertir les coordonnées CSV vers WGS84
                to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
                csv_lon, csv_lat = to_wgs84.transform(best_match['_geom3857'].x, best_match['_geom3857'].y)
                
                # Calculer la confiance (1.0 = distance 0, 0.0 = distance max)
                confidence = max(0.0, 1.0 - (min_distance / (max_distance_km * 1000)))
                
                matched_toll = MatchedToll(
                    osm_id=osm_toll.get('id', ''),
                    osm_name=osm_toll.get('name'),
                    osm_coordinates=osm_coords,
                    csv_id=best_match['id'],
                    csv_name=best_match.get('name', ''),
                    csv_role=best_match.get('role', ''),
                    csv_coordinates=[csv_lon, csv_lat],
                    distance_m=min_distance,
                    confidence=confidence
                )
                
                matched_tolls.append(matched_toll)
                
                print(f"   ✅ {osm_toll.get('name', 'Péage')} → {best_match.get('name', '')} "
                      f"({min_distance:.0f}m, {best_match.get('role', '')}-système)")
            else:
                # Péage OSM sans équivalent CSV
                unmatched_toll = MatchedToll(
                    osm_id=osm_toll.get('id', ''),
                    osm_name=osm_toll.get('name'),
                    osm_coordinates=osm_coords,
                    csv_id=None,
                    csv_name=None,
                    csv_role=None,
                    csv_coordinates=None,
                    distance_m=float('inf'),
                    confidence=0.0
                )
                
                matched_tolls.append(unmatched_toll)
                print(f"   ⚠️ {osm_toll.get('name', 'Péage')} → Aucun équivalent CSV trouvé")
        
        return matched_tolls
    
    def filter_open_system_tolls(self, matched_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """
        Filtre les péages à système ouvert (1 péage = 1 paiement).
        
        Args:
            matched_tolls: Liste des péages matchés
            
        Returns:
            List[MatchedToll]: Seulement les péages à système ouvert
        """
        open_tolls = [toll for toll in matched_tolls if toll.is_open_system]
        
        print(f"🎯 Péages à système ouvert : {len(open_tolls)}/{len(matched_tolls)}")
        for toll in open_tolls:
            print(f"   🟢 {toll.effective_name} ({toll.csv_id})")
        
        return open_tolls
    
    def get_toll_costs(self, matched_toll: MatchedToll, vehicle_class: str = 'c1') -> Optional[Dict]:
        """
        Récupère les coûts d'un péage à partir des données CSV.
        
        Args:
            matched_toll: Péage matché
            vehicle_class: Classe de véhicule (c1, c2, c3, c4, c5)
            
        Returns:
            Dict: Informations de coût ou None si pas disponible
        """
        if not matched_toll.csv_id:
            return None
        
        # TODO: Implémenter la récupération des coûts depuis virtual_edges.csv
        # Pour l'instant, retourner des données simulées
        return {
            'toll_id': matched_toll.csv_id,
            'vehicle_class': vehicle_class,
            'cost_estimate': 5.50,  # Coût simulé
            'currency': 'EUR'
        }
    
    def deduplicate_tolls(self, matched_tolls: List[MatchedToll], max_distance_m: float = 100) -> List[MatchedToll]:
        """
        Élimine les doublons de péages basés sur leur nom CSV et leur proximité.
        
        Args:
            matched_tolls: Liste des péages matchés
            max_distance_m: Distance maximale en mètres pour considérer 2 péages comme identiques
            
        Returns:
            List[MatchedToll]: Liste dédupliquée
        """
        if not matched_tolls:
            return matched_tolls
        
        print(f"🔄 Déduplication de {len(matched_tolls)} péages...")
        
        # Regrouper par nom CSV (péages identiques)
        toll_groups = {}
        unmatched_osm = []  # Péages OSM sans match CSV
        
        for toll in matched_tolls:
            if toll.csv_name and toll.csv_id:
                # Clé basée sur le nom CSV et l'ID
                key = f"{toll.csv_name}_{toll.csv_id}"
                if key not in toll_groups:
                    toll_groups[key] = []
                toll_groups[key].append(toll)
            else:
                # Péages OSM sans équivalent CSV
                unmatched_osm.append(toll)
        
        # Pour chaque groupe, garder le meilleur match (distance la plus faible)
        deduplicated = []
        
        for group_name, group_tolls in toll_groups.items():
            if len(group_tolls) == 1:
                # Pas de doublon
                deduplicated.append(group_tolls[0])
                print(f"   ✅ {group_tolls[0].effective_name} (unique)")
            else:
                # Plusieurs péages OSM matchent le même péage CSV
                # Garder celui avec la plus petite distance
                best_toll = min(group_tolls, key=lambda t: t.distance_m)
                deduplicated.append(best_toll)
                print(f"   🔄 {best_toll.effective_name} (sélectionné parmi {len(group_tolls)} doublons)")
                
                # Afficher les doublons éliminés
                for toll in group_tolls:
                    if toll != best_toll:
                        print(f"      ❌ Éliminé: {toll.osm_name} (distance: {toll.distance_m:.0f}m)")
        
        # Ajouter les péages OSM non matchés (si on veut les garder)
        # deduplicated.extend(unmatched_osm)
        
        print(f"✅ Déduplication terminée : {len(matched_tolls)} → {len(deduplicated)} péages")
        return deduplicated
    
    def deduplicate_tolls_by_proximity(self, matched_tolls: List[MatchedToll], route_coords: List[List[float]]) -> List[MatchedToll]:
        """
        Regroupe les péages par nom effectif et garde seulement celui le plus proche de la route.
        Élimine les doublons causés par les deux portes d'un même péage.
        
        Args:
            matched_tolls: Liste des péages matchés
            route_coords: Coordonnées de la route de base
            
        Returns:
            List[MatchedToll]: Péages dédupliqués
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
                # Un seul péage avec ce nom, le garder
                deduplicated.append(group[0])
                print(f"   📍 {name} : 1 péage conservé")
            else:
                # Plusieurs péages avec le même nom, garder le plus proche de la route
                best_toll = None
                best_toll = group[0]  # Par défaut, prendre le premier
                
                if best_toll:
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
