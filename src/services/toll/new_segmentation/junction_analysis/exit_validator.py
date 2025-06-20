"""
exit_validator.py
-----------------

Module pour valider les sorties d'autoroute et leurs capacités d'évitement des péages.
"""

from typing import List, Dict, Optional
from ..toll_matcher import MatchedToll
from ..osm_data_parser import OSMDataParser
from .geographic_utils import calculate_distance_km


class ExitValidator:
    """
    Classe pour valider les sorties d'autoroute et tester leur efficacité pour éviter les péages.
    """
    
    def __init__(self, osm_parser: OSMDataParser):
        """
        Initialise le validateur avec les données OSM.
        
        Args:
            osm_parser: Parser contenant les données OSM
        """
        self.osm_parser = osm_parser

    def test_exit_avoids_tolls(
        self, 
        junction: Dict, 
        unwanted_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> Optional[Dict]:
        """
        Teste si une sortie évite tous les péages non-désirés.
        
        Args:
            junction: Junction à tester
            unwanted_tolls: Péages à éviter
            route_coords: Coordonnées de la route
            
        Returns:
            Dict: Informations sur la sortie si elle évite les péages, None sinon
        """
        junction_name = junction['name']
        junction_ref = junction['ref']
        junction_position = junction['position_on_route_km']
        formatted_name = self._format_junction_name(junction)
        
        print(f"🧪 Test de la sortie {formatted_name}")
        
        # Vérifier que la sortie est AVANT tous les péages non-désirés
        for unwanted_toll in unwanted_tolls:
            toll_position = self._calculate_position_on_route(
                unwanted_toll.osm_coordinates, route_coords
            )
            
            if junction_position >= toll_position:
                print(f"   ❌ Sortie {formatted_name} est APRÈS {unwanted_toll.effective_name} ({junction_position:.1f} km >= {toll_position:.1f} km)")
                return None
        
        # La sortie est avant tous les péages non-désirés
        print(f"   ✅ Sortie {formatted_name} est avant tous les péages non-désirés")
          
        # Chercher le motorway_link associé
        exit_link = self._find_motorway_link_for_junction(junction)
        
        # S'assurer que les coordonnées sont valides
        link_coordinates = junction['coordinates']  # Fallback sur les coordonnées de la junction
        if exit_link and exit_link.get('coordinates'):
            # Vérifier que les coordonnées du link sont valides
            link_coords = exit_link['coordinates']
            if (isinstance(link_coords, list) and len(link_coords) >= 1 and 
                isinstance(link_coords[0], list) and len(link_coords[0]) == 2 and
                isinstance(link_coords[0][0], (int, float)) and isinstance(link_coords[0][1], (int, float))):
                link_coordinates = link_coords[0]  # Premier point du link
            else:
                print(f"   ⚠️ Coordonnées du motorway_link invalides, utilisation de la junction")
        
        return {
            'type': 'motorway_junction',
            'name': junction['name'],
            'ref': junction['ref'],
            'coordinates': junction['coordinates'],
            'link_coordinates': link_coordinates,
            'position_km': junction_position,
            'avoids_tolls': [toll.effective_name for toll in unwanted_tolls]
        }

    def is_real_exit(self, junction: Dict) -> bool:
        """
        Détermine si une junction est une vraie sortie d'autoroute ou juste un accès vers une aire de repos/service.
        Se base principalement sur le champ 'destination' qui est le plus fiable.
        
        Args:
            junction: Données de la junction
            
        Returns:
            bool: True si c'est une vraie sortie, False si c'est une aire/service
        """
        name = junction.get('name', '').lower()
        ref = junction.get('ref', '')
        destination = junction.get('destination', '').lower()
        
        # 1. PRIORITÉ: Vérifier la destination (le plus important)
        if destination:
            # Mots-clés dans la destination qui indiquent une aire/service (à exclure)
            excluded_destination_keywords = [
                'aire de', 'aire du', 'aire des', 'aire ',
                'service', 'services',
                'station service', 'station-service',
                'parking', 'relais', 'halte',
                'repos', 'essence', 'gas', 'fuel'
            ]
            
            for keyword in excluded_destination_keywords:
                if keyword in destination:
                    print(f"   🚫 Exclusion {junction['name']} : destination contient '{keyword}' -> {destination}")
                    return False
        
        # 2. FALLBACK: Vérifier le nom si pas de destination claire
        if name:
            excluded_name_keywords = [
                'aire de', 'aire du', 'aire des', 
                'aire d\'',      # apostrophe ASCII (code 39)
                'aire d\u2019',  # apostrophe typographique Unicode (code 8217) 
                'service', 'services',
                'station service', 'station-service',
                'péage',  # Les péages ne sont pas des sorties
                'gare de péage',
                'parking'
            ]
            
            for keyword in excluded_name_keywords:
                if keyword in name:
                    print(f"   🚫 Exclusion {junction['name']} : nom contient '{keyword}'")
                    return False
        
        # 3. VALIDATION POSITIVE: Les vraies sorties ont généralement une référence numérique
        if ref and any(c.isdigit() for c in ref):
            print(f"   ✅ Inclusion {junction['name']} : a une référence numérique '{ref}'")
            return True
        
        # 4. Les échangeurs sont des vraies sorties
        if 'échangeur' in name or 'echangeur' in name:
            print(f"   ✅ Inclusion {junction['name']} : échangeur")
            return True
        
        # 5. Si destination vers des villes (pas d'aire), c'est une vraie sortie
        if destination and not any(excluded in destination for excluded in ['aire', 'service', 'parking']):
            print(f"   ✅ Inclusion {junction['name']} : destination vers ville -> {destination}")
            return True
        
        # 6. NOUVEAU: Exclure les sorties sans référence (souvent inutilisées ou en construction)
        if not ref or ref.strip() == '':
            print(f"   🚫 Exclusion {junction['name']} : pas de référence (sortie peu utilisée)")
            return False
        
        # 7. Par défaut, inclure si aucun critère d'exclusion n'est trouvé
        print(f"   ✅ Inclusion par défaut {junction['name']} : aucun critère d'exclusion trouvé")
        return True

    def _find_motorway_link_for_junction(self, junction: Dict) -> Optional[Dict]:
        """
        Trouve le motorway_link associé à une junction pour la sortie.
        
        Args:
            junction: Junction pour laquelle chercher le link
            
        Returns:
            Dict: Informations sur le motorway_link ou None
        """        
        # Récupérer tous les motorway_links
        all_links = self.osm_parser.motorway_links
        if not all_links:
            return None
        
        junction_coords = junction['coordinates']
        best_link = None
        min_distance = float('inf')
        
        for link in all_links:
            link_coords = link.coordinates if hasattr(link, 'coordinates') else []
            if not link_coords:
                continue
            
            # Calculer la distance entre junction et link
            distance_km = calculate_distance_km(junction_coords, link_coords[0])  # Premier point du link
            distance_m = distance_km * 1000
            
            # Garder le link le plus proche (< 1km)
            if distance_m < min_distance and distance_m <= 1000:
                min_distance = distance_m
                best_link = {
                    'id': link.way_id if hasattr(link, 'way_id') else '',
                    'coordinates': link_coords,
                    'distance_to_junction': distance_m
                }
        
        if best_link:
            print(f"   🔗 Motorway_link trouvé à {best_link['distance_to_junction']:.0f}m de la junction")
            return best_link
        
        return None

    def _format_junction_name(self, junction: Dict) -> str:
        """
        Formate le nom d'une junction avec sa référence pour un affichage plus informatif.
        
        Args:
            junction: Junction avec 'name' et 'ref'
            
        Returns:
            str: Nom formaté avec référence (ex: "Sortie 14.1" ou "Colmar-Nord (25)")
        """
        name = junction.get('name', 'Sortie inconnue')
        ref = junction.get('ref', '')
        
        if ref and ref.strip():
            # Si le nom contient déjà la référence, ne pas la dupliquer
            if ref in name:
                return name
            else:
                # Ajouter la référence entre parenthèses
                return f"{name} ({ref})"
        else:
            return name

    def _calculate_position_on_route(
        self, 
        point_coords: List[float], 
        route_coords: List[List[float]]
    ) -> float:
        """
        Calcule la position d'un point sur la route en kilomètres depuis le début.
        
        Args:
            point_coords: Coordonnées du point [lon, lat]
            route_coords: Coordonnées de la route
            
        Returns:
            float: Position en kilomètres depuis le début de la route
        """
        if not route_coords or len(route_coords) < 2:
            return 0.0
        
        # Trouver le segment de route le plus proche du point
        min_distance = float('inf')
        closest_segment_index = 0
        
        for i in range(len(route_coords) - 1):
            segment_start = route_coords[i]
            segment_end = route_coords[i + 1]
            
            # Distance du point au segment
            distance = self._point_to_segment_distance(
                point_coords, segment_start, segment_end
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_segment_index = i
        
        # Calculer la distance cumulée jusqu'au segment le plus proche
        cumulative_distance = 0.0
        for i in range(closest_segment_index):
            distance = calculate_distance_km(route_coords[i], route_coords[i + 1])
            cumulative_distance += distance
        
        # Ajouter la moitié du segment le plus proche (approximation)
        if closest_segment_index < len(route_coords) - 1:
            segment_distance = calculate_distance_km(
                route_coords[closest_segment_index], 
                route_coords[closest_segment_index + 1]
            )
            cumulative_distance += segment_distance / 2
        
        return cumulative_distance

    def _point_to_segment_distance(
        self, 
        point: List[float], 
        seg_start: List[float], 
        seg_end: List[float]
    ) -> float:
        """
        Calcule la distance d'un point à un segment de ligne.
        
        Args:
            point: Point [lon, lat]
            seg_start: Début du segment [lon, lat]
            seg_end: Fin du segment [lon, lat]
            
        Returns:
            float: Distance minimale en kilomètres
        """
        # Distance aux extrémités du segment
        dist_to_start = calculate_distance_km(point, seg_start)
        dist_to_end = calculate_distance_km(point, seg_end)
        
        # Retourner la distance minimale (approximation simple)
        return min(dist_to_start, dist_to_end)
