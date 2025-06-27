"""
OSM Parser
----------

Parser for OSM GeoJSON data containing motorway junctions, links, and toll stations.
Refactored from osm_data_parser.py with <300 lines.
"""

import json
from typing import List, Dict

from ..models.motorway_junction import MotorwayJunction
from ..models.motorway_link import MotorwayLink
from ..models.toll_station import TollStation
from ..utils.geographic_utils import calculate_distance


class OSMParser:
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
            
            self._link_motorway_elements()
            self._prematch_tolls_with_csv()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing OSM : {e}")
            return False
    
    def _parse_feature(self, feature: Dict):
        """Parse une feature individuelle du GeoJSON."""
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
                    properties=properties
                )
                self.motorway_junctions.append(junction)
    
    def _parse_motorway_link(self, feature_id: str, properties: Dict, geometry: Dict):
        """Parse un motorway_link."""
        geometry_type = geometry.get('type')
        coordinates = geometry.get('coordinates', [])
        
        if geometry_type == 'LineString' and coordinates:
            link = MotorwayLink(
                way_id=feature_id,
                destination=properties.get('destination'),
                coordinates=coordinates,
                properties=properties
            )
            self.motorway_links.append(link)
        elif geometry_type == 'Point' and len(coordinates) >= 2:
            # Convertir en format LineString avec deux points identiques
            point_coords = [coordinates, coordinates]
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
                # Filtrer les péages sans opérateur
                operator = properties.get('operator')
                if not operator or operator.strip() == '':
                    return
                
                # Déterminer le type de péage
                toll_type = "open" if properties.get('barrier') != 'toll_booth' else "closed"
                
                station = TollStation(
                    feature_id=feature_id,
                    name=properties.get('name'),
                    coordinates=coordinates,
                    toll_type=toll_type,
                    properties=properties
                )
                self.toll_stations.append(station)
    
    def _is_toll_station(self, properties: Dict) -> bool:
        """Détermine si une feature représente une station de péage."""
        toll_indicators = [
            properties.get('barrier') == 'toll_booth',
            properties.get('amenity') == 'toll_booth',
            'toll' in properties.get('name', '').lower(),
            'péage' in properties.get('name', '').lower(),
        ]
        return any(toll_indicators)
    
    def find_junctions_near_route(self, route_coordinates: List[List[float]], 
                                 max_distance_km: float = 2.0) -> List[MotorwayJunction]:
        """Trouve les motorway_junctions proches d'une route."""
        nearby_junctions = []
        
        for junction in self.motorway_junctions:
            min_distance = min(
                junction.distance_to(point) 
                for point in route_coordinates
            )
            
            if min_distance <= max_distance_km:
                nearby_junctions.append(junction)
        
        return nearby_junctions
    
    def find_tolls_near_route(self, route_coordinates: List[List[float]], 
                             max_distance_km: float = 5.0) -> List[TollStation]:
        """Trouve les stations de péage proches d'une route."""
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
        """Lie les motorway_junctions avec leurs chaînes de motorway_links."""
        print("🔗 Phase 2 : Linking des éléments OSM...")
        
        from ..linking.junction_linker import JunctionLinker
        
        linker = JunctionLinker()
        linker.link_all_junctions(self.motorway_junctions, self.motorway_links)
        
        # Afficher un exemple pour validation
        self._print_test_junction()
    
    def _print_test_junction(self) -> None:
        """Affiche les détails de la junction de test pour validation."""
        from ..linking.junction_linker import JunctionLinker
        
        linker = JunctionLinker()
        test_junction = linker.find_junction_by_id(self.motorway_junctions, "621758529")
        
        if test_junction:
            print(f"🎯 Junction test trouvée : {test_junction.node_id}")
            print(f"   - Ref : {test_junction.ref}")
            print(f"   - Liens liés : {len(test_junction.linked_motorway_links)}")
            for i, link in enumerate(test_junction.linked_motorway_links):
                print(f"     {i+1}. {link.way_id} → {link.destination}")
        else:
            print("❌ Junction test non trouvée")
    
    def _prematch_tolls_with_csv(self) -> None:
        """Pré-matche les péages OSM avec les données CSV."""
        print("🔗 Phase 3 : Pré-matching péages OSM/CSV...")
        
        try:
            from src.cache.parsers.toll_matcher import TollMatcher
            from ..utils.report_generator import write_osm_csv_match_report
            
            matcher = TollMatcher()
            osm_tolls_dict = [
                {
                    'id': toll.feature_id,
                    'name': toll.name,
                    'coordinates': toll.coordinates
                }
                for toll in self.toll_stations
            ]
            
            matched_tolls = matcher.match_osm_tolls_with_csv(osm_tolls_dict)
            self._associate_csv_matches(matched_tolls)
            
            # Phase 3b: Linking des péages avec les junctions
            self._link_junctions_with_tolls(matched_tolls)
            
            # Générer le rapport
            write_osm_csv_match_report(self.toll_stations)
            
        except Exception as e:
            print(f"⚠️ Erreur lors du pré-matching : {e}")
    
    def _associate_csv_matches(self, matched_tolls: List) -> None:
        """Associe les résultats du matching CSV aux toll_stations OSM."""
        matches_by_osm_id = {match.osm_id: match for match in matched_tolls}
        
        matched_count = 0
        for toll in self.toll_stations:
            match = matches_by_osm_id.get(toll.feature_id)
            if match:
                toll.csv_match = {
                    'id': match.csv_id,
                    'name': match.csv_name,
                    'role': match.csv_role,
                    'coordinates': match.csv_coordinates,
                    'distance_m': match.distance_m
                }
                matched_count += 1
        
        print(f"✅ {matched_count}/{len(self.toll_stations)} péages OSM matchés avec CSV")
    
    def _link_junctions_with_tolls(self, matched_tolls: List) -> None:
        """
        Lie les junctions avec les péages sur leurs motorway_links.
        Pour chaque junction, cherche un péage sur une de ses motorway_links (<2m de la polyligne).
        """
        from ..utils.geographic_utils import distance_point_to_polyline_meters
        
        max_distance_m = 2.0
        
        def toll_is_on_link(toll, link):
            """Vérifie si un péage est sur un lien."""
            toll_coords = [toll.longitude, toll.latitude] if hasattr(toll, 'longitude') else toll.coordinates
            return distance_point_to_polyline_meters(toll_coords, link.coordinates) <= max_distance_m
        
        # Convertir matched_tolls en dictionnaire pour lookup rapide
        tolls_by_osm_id = {toll.osm_id: toll for toll in matched_tolls}
        
        for junction in self.motorway_junctions:
            junction.toll = False
            junction.toll_station = None
            
            # Chercher un péage sur les links de cette junction
            for link in junction.linked_motorway_links:
                for toll_station in self.toll_stations:
                    if toll_is_on_link(toll_station, link):
                        junction.toll = True
                        
                        # Récupérer le MatchedToll correspondant
                        matched_toll = tolls_by_osm_id.get(toll_station.feature_id)
                        if matched_toll:
                            matched_toll.is_exit = True
                            junction.toll_station = matched_toll
                        
                        break
                
                if junction.toll:
                    break
        
        n_exit_tolls = sum(1 for j in self.motorway_junctions if j.toll)
        print(f"✅ {n_exit_tolls} sorties avec péage détectées")
        
        # Test de validation
        self._validate_toll_junction_linking()
    
    def _validate_toll_junction_linking(self) -> None:
        """Valide le linking des péages avec les junctions."""
        from ..linking.junction_linker import JunctionLinker
        
        linker = JunctionLinker()
        test_junction_id = "621758529"
        test_junction = linker.find_junction_by_id(self.motorway_junctions, test_junction_id)
        
        if test_junction:
            print(f"\n🔍 Junction de test : {test_junction.node_id}")
            print(f"   📍 Coordonnées : {test_junction.coordinates}")
            print(f"   🔗 Nombre de links liés : {len(test_junction.linked_motorway_links)}")
            print(f"   🚦 Péage détecté : {test_junction.toll}")
            if test_junction.toll_station:
                print(f"   🏷️ Péage associé : {test_junction.toll_station.effective_name} "
                      f"(is_exit={test_junction.toll_station.is_exit})")
        else:
            print(f"\n❌ Junction de test {test_junction_id} non trouvée")
