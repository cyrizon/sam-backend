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
from dataclasses import dataclass
import math


@dataclass
class MotorwayJunction:
    """Représente une sortie d'autoroute (motorway_junction)."""
    node_id: str
    ref: Optional[str]  # Numéro de sortie (ex: "6.1")
    coordinates: List[float]  # [lon, lat]
    properties: Dict
    
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
                    print(f"   🚫 Péage {properties.get('name', 'Sans nom')} exclu : pas d'opérateur")
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
                print(f"   ✅ Péage {properties.get('name', 'Sans nom')} inclus : opérateur '{operator}'")
    
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
