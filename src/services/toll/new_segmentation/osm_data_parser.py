"""
osm_data_parser.py
-----------------

Module pour parser et analyser les données OSM (GeoJSON) contenant :
- motorway_junction (sorties d'autoroute)
- motorway_link (liens de sortie)
- toll stations (péages)

Responsabilité : extraire et structurer les données OSM pertinentes.
"""

import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import math


@dataclass
class MotorwayJunction:
    """Représente une sortie d'autoroute (motorway_junction)."""
    node_id: str
    ref: Optional[str]  # Numéro de sortie (ex: "6.1")
    coordinates: List[float]  # [lon, lat]
    properties: Dict
    linked_motorway_links: List['MotorwayLink'] = field(default_factory=list)  # Chaîne de liens associés
    toll: bool = False  # Indique si la sortie possède un péage
    toll_station: Optional['MatchedToll'] = None  # Référence vers le péage s'il existe
    
    def distance_to(self, point: List[float]) -> float:
        """Calcule la distance à un point en km."""
        return calculate_distance(self.coordinates, point)


@dataclass
class MotorwayLink:
    """Représente un lien de sortie (motorway_link)."""
    way_id: str
    destination: Optional[str]
    coordinates: List[List[float]]  # Liste de points [lon, lat]
    properties: Dict
    next_link: Optional['MotorwayLink'] = None  # Lien suivant dans la chaîne
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début du lien."""
        return self.coordinates[0] if self.coordinates else [0, 0]
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin du lien."""
        return self.coordinates[-1] if self.coordinates else [0, 0]


@dataclass
class TollStation:
    """Représente une station de péage."""
    feature_id: str
    name: Optional[str]
    coordinates: List[float]  # [lon, lat]
    toll_type: str  # "open" ou "closed"
    properties: Dict
    csv_match: Optional[Dict] = None  # NOUVEAU : Données CSV pré-matchées
    
    def distance_to(self, point: List[float]) -> float:
        """Calcule la distance à un point en km."""
        return calculate_distance(self.coordinates, point)


def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calcule la distance entre deux points géographiques en km.
    
    Args:
        point1: [longitude, latitude]
        point2: [longitude, latitude]
        
    Returns:
        float: Distance en kilomètres
    """
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en km
    return 6371 * c


class OSMDataParser:
    """
    Parser pour les données OSM au format GeoJSON.
    
    Extrait et structure les données pertinentes pour l'algorithme de segmentation.
    """
    
    def __init__(self, geojson_file_path: str):
        """
        Initialise le parser avec un fichier GeoJSON.
        
        Args:
            geojson_file_path: Chemin vers le fichier GeoJSON OSM
        """
        self.geojson_file_path = geojson_file_path
        self.motorway_junctions: List[MotorwayJunction] = []
        self.motorway_links: List[MotorwayLink] = []
        self.toll_stations: List[TollStation] = []
    
    def load_and_parse(self) -> bool:
        """
        Charge et parse le fichier GeoJSON.
        
        Returns:
            bool: True si le parsing s'est bien passé
        """
        try:
            with open(self.geojson_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            print(f"📁 Chargement de {len(features)} features OSM...")
            
            for feature in features:
                self._parse_feature(feature)
            
            print(f"✅ Parsing terminé :")
            print(f"   - Motorway junctions: {len(self.motorway_junctions)}")
            print(f"   - Motorway links: {len(self.motorway_links)}")
            print(f"   - Toll stations: {len(self.toll_stations)}")
            
            # Phase 2: Linking des éléments OSM
            self._link_motorway_elements()
            
            # Phase 3: NOUVEAU - Pré-matching des péages OSM/CSV
            self._prematch_tolls_with_csv()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing OSM : {e}")
            return False
    
    def _parse_feature(self, feature: Dict):
        """
        Parse une feature individuelle du GeoJSON.
        
        Args:
            feature: Feature GeoJSON
        """
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        feature_id = feature.get('id', '')
        
        highway_type = properties.get('highway')
        
        if highway_type == 'motorway_junction':
            self._parse_motorway_junction(feature_id, properties, geometry)
        elif highway_type == 'motorway_link':
            self._parse_motorway_link(feature_id, properties, geometry)
        elif self._is_toll_station(properties):
            self._parse_toll_station(feature_id, properties, geometry)
    
    def _parse_motorway_junction(self, feature_id: str, properties: Dict, geometry: Dict):
        """Parse une motorway_junction."""
        if geometry.get('type') == 'Point':
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) >= 2:
                junction = MotorwayJunction(
                    node_id=feature_id,
                    ref=properties.get('ref'),
                    coordinates=coordinates,
                    properties=properties                )
                self.motorway_junctions.append(junction)
    
    def _parse_motorway_link(self, feature_id: str, properties: Dict, geometry: Dict):
        """Parse un motorway_link."""
        geometry_type = geometry.get('type')
        coordinates = geometry.get('coordinates', [])
        
        if geometry_type == 'LineString' and coordinates:
            # Motorway_link traditionnel avec plusieurs points
            link = MotorwayLink(
                way_id=feature_id,
                destination=properties.get('destination'),
                coordinates=coordinates,
                properties=properties
            )
            self.motorway_links.append(link)
        elif geometry_type == 'Point' and len(coordinates) >= 2:
            # Motorway_link simplifié avec un seul point (format OSM parfois utilisé)
            # Convertir en format LineString avec deux points identiques
            point_coords = [coordinates, coordinates]  # Dupliquer le point
            link = MotorwayLink(
                way_id=feature_id,
                destination=properties.get('destination'),
                coordinates=point_coords,
                properties=properties
            )
            self.motorway_links.append(link)
    
    def _parse_toll_station(self, feature_id: str, properties: Dict, geometry: Dict):
        """Parse une station de péage."""
        if geometry.get('type') == 'Point':
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) >= 2:
                # NOUVEAU: Filtrer les péages sans opérateur
                operator = properties.get('operator')
                if not operator or operator.strip() == '':
                    # Exclure les péages sans opérateur (souvent obsolètes ou non-officiels)
                    # print(f"   🚫 Péage {properties.get('name', 'Sans nom')} exclu : pas d'opérateur")
                    return
                
                # Déterminer le type de péage
                toll_type = "open"  # Par défaut
                if properties.get('barrier') == 'toll_booth':
                    toll_type = "closed"
                
                station = TollStation(
                    feature_id=feature_id,
                    name=properties.get('name'),
                    coordinates=coordinates,
                    toll_type=toll_type,
                    properties=properties
                )
                self.toll_stations.append(station)
                # print(f"   ✅ Péage {properties.get('name', 'Sans nom')} inclus : opérateur '{operator}'")
    
    def _is_toll_station(self, properties: Dict) -> bool:
        """
        Détermine si une feature représente une station de péage.
        
        Args:
            properties: Propriétés de la feature
            
        Returns:
            bool: True si c'est une station de péage
        """
        # Vérifier différents indicateurs de péage
        toll_indicators = [
            properties.get('barrier') == 'toll_booth',
            properties.get('amenity') == 'toll_booth',
            'toll' in properties.get('name', '').lower(),
            'péage' in properties.get('name', '').lower(),
        ]
        
        return any(toll_indicators)
    
    def find_junctions_near_route(self, route_coordinates: List[List[float]], max_distance_km: float = 2.0) -> List[MotorwayJunction]:
        """
        Trouve les motorway_junctions proches d'une route.
        
        Args:
            route_coordinates: Points de la route [[lon, lat], ...]
            max_distance_km: Distance maximale en km
            
        Returns:
            List[MotorwayJunction]: Junctions proches de la route
        """
        nearby_junctions = []
        
        for junction in self.motorway_junctions:
            min_distance = min(
                junction.distance_to(point) 
                for point in route_coordinates
            )
            
            if min_distance <= max_distance_km:
                nearby_junctions.append(junction)
        
        return nearby_junctions
    
    def find_links_near_point(self, point: List[float], max_distance_km: float = 1.0) -> List[MotorwayLink]:
        """
        Trouve les motorway_links près d'un point donné.
        
        Args:
            point: Coordonnées du point [lon, lat]
            max_distance_km: Distance maximale en km
            
        Returns:
            List[MotorwayLink]: Liste des liens trouvés
        """
        nearby_links = []
        
        print(f"   🔍 Debug: Recherche de liens près de {point} dans {max_distance_km} km")
        print(f"   📊 Total de motorway_links à examiner : {len(self.motorway_links)}")
        
        for i, link in enumerate(self.motorway_links):
            # Calculer la distance au point de début du lien
            start_point = link.get_start_point()
            end_point = link.get_end_point()
            
            start_distance = calculate_distance(point, start_point)
            end_distance = calculate_distance(point, end_point)
            
            # Prendre la distance minimale
            min_distance = min(start_distance, end_distance)
              # Debug pour les premiers liens ou ceux proches
            if i < 5 or min_distance <= max_distance_km * 2:  # Debug étendu
                print(f"   🔗 Lien {i}: start={start_point}, end={end_point}, min_dist={min_distance:.1f}km")
            
            if min_distance <= max_distance_km:
                nearby_links.append(link)
                print(f"   ✅ Lien trouvé à {min_distance:.1f}km")
        
        print(f"   📍 {len(nearby_links)} lien(s) trouvé(s) dans {max_distance_km} km")
        return nearby_links

    def find_tolls_near_route(self, route_coordinates: List[List[float]], max_distance_km: float = 5.0) -> List[TollStation]:
        """
        Trouve les stations de péage proches d'une route.
        
        Args:
            route_coordinates: Points de la route [[lon, lat], ...]
            max_distance_km: Distance maximale en km
            
        Returns:
            List[TollStation]: Stations de péage proches de la route
        """
        nearby_tolls = []
        
        for toll in self.toll_stations:
            min_distance = min(
                toll.distance_to(point) 
                for point in route_coordinates
            )
            
            if min_distance <= max_distance_km:
                nearby_tolls.append(toll)
        
        return nearby_tolls

    def _link_motorway_elements(self) -> None:
        """
        Lie les motorway_junctions avec leurs chaînes de motorway_links.
        
        Phase 2 du parsing : association des éléments OSM par proximité.
        """
        from src.services.toll.new_segmentation.linking.junction_linker import JunctionLinker
        
        linker = JunctionLinker()
        linker.link_all_junctions(self.motorway_junctions, self.motorway_links)
        
        # Afficher un exemple pour validation
        self._print_test_junction()
    
    def _print_test_junction(self) -> None:
        """
        Affiche les détails de la junction de test pour validation.
        """
        from src.services.toll.new_segmentation.linking.junction_linker import JunctionLinker
        
        linker = JunctionLinker()
        test_junction = linker.find_junction_by_id(self.motorway_junctions, "621758529")
        
        if test_junction:
            print(f"\n🔍 Junction de test trouvée : {test_junction.node_id}")
            print(f"   📍 Coordonnées : {test_junction.coordinates}")
            print(f"   🔗 Nombre de links liés : {len(test_junction.linked_motorway_links)}")
            
            for i, link in enumerate(test_junction.linked_motorway_links):
                link_id = link.way_id.split('/')[-1] if '/' in link.way_id else link.way_id
                print(f"   Link {i+1}: {link_id}")
                if link.destination:
                    print(f"      → Destination: {link.destination}")
                print(f"      → Start: {link.get_start_point()}")
                print(f"      → End: {link.get_end_point()}")
                
                # Vérifier si c'est un des IDs attendus
                expected_ids = ["657897788", "126357480", "1298540619", "1298540620"]
                if link_id in expected_ids:
                    print(f"      ✅ ID attendu trouvé!")
                else:
                    print(f"      ⚠️ ID inattendu")
        else:
            print(f"\n❌ Junction de test 621758529 non trouvée")
            print(f"   Junctions disponibles (échantillon) :")
            for i, junction in enumerate(self.motorway_junctions[:5]):
                junction_id = junction.node_id.split('/')[-1] if '/' in junction.node_id else junction.node_id
                print(f"   - {junction_id}")
    
    def _prematch_tolls_with_csv(self) -> None:
        """
        NOUVEAU : Pré-matche les péages OSM avec les données CSV au chargement.
        
        OPTIMISATION CLÉ : Les péages sont matchés une seule fois au chargement,
        pas à chaque requête. Chaque péage OSM aura son csv_role et nom CSV disponibles.
        """
        print("🔗 Phase 3 : Pré-matching péages OSM/CSV...")
        
        try:
            # Importer le TollMatcher pour utiliser sa logique de matching
            from .toll_matcher import TollMatcher
            
            # Initialiser le matcher
            matcher = TollMatcher()
            
            # Convertir les péages OSM au format attendu par le matcher
            osm_tolls_dict = []
            for toll_station in self.toll_stations:
                toll_dict = {
                    'id': toll_station.feature_id,
                    'name': toll_station.name,
                    'coordinates': toll_station.coordinates
                }
                osm_tolls_dict.append(toll_dict)
            
            # Effectuer le matching avec les données CSV
            matched_tolls = matcher.match_osm_tolls_with_csv(osm_tolls_dict, max_distance_km=5.0)

            # Appel de la fonction pour lier les junctions aux péages de sortie
            self.link_junctions_with_tolls(matched_tolls)

            # Associer les résultats du matching aux toll_stations
            self._associate_csv_matches(matched_tolls)
            
            print(f"✅ Pré-matching terminé : {len(matched_tolls)} péages traités")
            
            # Générer un rapport JSON des correspondances OSM/CSV
            try:
                from .osm_csv_match_reporter import write_osm_csv_match_report
                write_osm_csv_match_report(self.toll_stations)
            except Exception as e:
                print(f"⚠️ Erreur lors de la génération du rapport de matching OSM/CSV : {e}")
            
        except Exception as e:
            print(f"⚠️ Erreur pré-matching (non-critique) : {e}")
            # Le pré-matching est optionnel, on continue même en cas d'erreur
    
    def _associate_csv_matches(self, matched_tolls: List) -> None:
        """
        Associe les résultats du matching CSV aux toll_stations OSM.
        
        Args:
            matched_tolls: Résultats du matching OSM/CSV
        """
        # Créer un dictionnaire pour lookup rapide
        matches_by_osm_id = {match.osm_id: match for match in matched_tolls}
        
        matched_count = 0
        unmatched_count = 0
        
        for toll_station in self.toll_stations:
            match = matches_by_osm_id.get(toll_station.feature_id)
            
            if match and match.csv_id:
                # Péage matché avec succès
                toll_station.csv_match = {
                    'id': match.csv_id,
                    'name': match.csv_name,
                    'role': match.csv_role,  # 'O' ou 'F' - CLÉ pour l'optimisation
                    'coordinates': match.csv_coordinates,
                    'distance_m': match.distance_m,
                    'confidence': match.confidence
                }
                matched_count += 1
                
                role_str = f"({match.csv_role})" if match.csv_role else "(role inconnue)"
                csv_name_display = match.csv_name or "Nom CSV manquant"
                # print(f"   ✅ {toll_station.name or 'Sans nom'} → {csv_name_display} {role_str}")
                
            else:
                # Péage non matché - sera considéré comme fermé (csv_role='F')
                toll_station.csv_match = None
                unmatched_count += 1
                # print(f"   🔍 {toll_station.name or 'Sans nom'} → Non matché (considéré fermé)")
        
        print(f"   📊 Résultats matching : {matched_count} matchés, {unmatched_count} non-matchés")
    
    def link_junctions_with_tolls(self, matched_tolls: list, max_distance_m: float = 2.0):
        """
        Pour chaque motorway_junction, cherche un péage sur une de ses motorway_links (<2m de la polyligne).
        Si trouvé, met à jour les attributs toll et toll_station.
        """
        for junction in getattr(self, 'motorway_junctions', []):
            found = False
            for link in getattr(junction, 'linked_motorway_links', []):
                for toll in matched_tolls:
                    dist = self._distance_point_to_polyline_meters(toll.osm_coordinates, getattr(link, 'coordinates', []))
                    if dist < max_distance_m:
                        junction.toll = True
                        junction.toll_station = toll
                        found = True
                        break
                if found:
                    break
            if not found:
                junction.toll = False
                junction.toll_station = None
        # Affiche le nombre de sorties avec péage
        n_exit_tolls = sum(1 for j in getattr(self, 'motorway_junctions', []) if j.toll)
        print(f"[OSMDataParser] Nombre de sorties avec péage : {n_exit_tolls}")
    
    def _distance_point_to_polyline_meters(self, pt, polyline):
        """
        Calcule la distance minimale (en mètres) entre un point pt et une polyligne (liste de [lon, lat]).
        """
        import math
        min_dist = float('inf')
        for i in range(len(polyline) - 1):
            seg_a = polyline[i]
            seg_b = polyline[i + 1]
            # Adapté de _distance_point_to_segment_meters
            lon1, lat1 = math.radians(seg_a[0]), math.radians(seg_a[1])
            lon2, lat2 = math.radians(seg_b[0]), math.radians(seg_b[1])
            lonp, latp = math.radians(pt[0]), math.radians(pt[1])
            R = 6371000.0
            x1, y1 = R * lon1 * math.cos((lat1+lat2)/2), R * lat1
            x2, y2 = R * lon2 * math.cos((lat1+lat2)/2), R * lat2
            xp, yp = R * lonp * math.cos((lat1+lat2)/2), R * latp
            dx, dy = x2 - x1, y2 - y1
            if dx == 0 and dy == 0:
                dist = math.hypot(xp - x1, yp - y1)
            else:
                t = ((xp - x1) * dx + (yp - y1) * dy) / (dx*dx + dy*dy)
                t = max(0, min(1, t))
                x_proj, y_proj = x1 + t * dx, y1 + t * dy
                dist = math.hypot(xp - x_proj, yp - y_proj)
            if dist < min_dist:
                min_dist = dist
        return min_dist
