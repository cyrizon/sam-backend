"""
motorway_junction_analyzer.py
----------------------------

Module pour analyser les motorway_junctions sur la route et identifier
les vraies sorties d'autoroute pour éviter les péages non-désirés.

Responsabilité : 
- Analyser les junctions sur la route de base
- Identifier les sorties avant chaque péage
- Valider que les sorties évitent bien les péages
- Recalculer les segments si nécessaire
"""

from typing import List, Dict, Optional, Tuple
import math
from .toll_matcher import MatchedToll
from .osm_data_parser import OSMDataParser
from .polyline_intersection import point_to_polyline_distance, calculate_distance


def calculate_distance_km(coord1: List[float], coord2: List[float]) -> float:
    """
    Calcule la distance entre deux coordonnées en kilomètres.
    
    Args:
        coord1: [lon, lat] première coordonnée
        coord2: [lon, lat] deuxième coordonnée
        
    Returns:
        float: Distance en kilomètres
    """
    # Conversion en radians
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    
    # Formule haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en km
    R = 6371
    return R * c


class MotorwayJunctionAnalyzer:
    """
    Analyse les motorway_junctions pour trouver les vraies sorties d'autoroute.
    """
    
    def __init__(self, osm_parser: OSMDataParser):
        """
        Initialise l'analyzeur avec les données OSM.
        
        Args:
            osm_parser: Parser contenant les données OSM
        """
        self.osm_parser = osm_parser

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

    def find_exit_before_toll(
        self, 
        route_coords: List[List[float]], 
        target_toll: MatchedToll,
        unwanted_tolls_after: List[MatchedToll]
    ) -> Optional[Dict]:
        """
        Trouve la sortie d'autoroute optimale avant un péage pour éviter les péages suivants.
        
        Args:
            route_coords: Coordonnées de la route de base
            target_toll: Péage cible (dernier qu'on veut utiliser)
            unwanted_tolls_after: Péages à éviter après le péage cible
            
        Returns:
            Dict: Informations sur la sortie optimale ou None
        """
        print(f"🔍 Recherche de sortie avant {target_toll.effective_name} pour éviter {len(unwanted_tolls_after)} péages")
        
        # 1. Analyser toutes les junctions sur la route
        junctions_on_route = self._find_junctions_on_route(route_coords)
        if not junctions_on_route:
            print("❌ Aucune junction trouvée sur la route")
            return None
        
        print(f"📍 {len(junctions_on_route)} junctions trouvées sur la route")
        
        # 2. Ordonner les junctions selon leur position sur la route
        ordered_junctions = self._order_junctions_by_route_position(junctions_on_route, route_coords)
        
        # 3. Trouver la position du péage cible sur la route
        target_toll_position = self._find_toll_position_on_route(target_toll, route_coords)
        
        # 4. Filtrer les junctions qui sont AVANT le péage cible
        junctions_before_target = self._filter_junctions_before_toll(
            ordered_junctions, target_toll_position, route_coords
        )
        
        if not junctions_before_target:
            print(f"❌ Aucune junction trouvée avant {target_toll.effective_name}")
            return None
        # 5. Tester les sorties une par une (de la plus proche à la plus lointaine)
        for junction in junctions_before_target:
            exit_info = self._test_exit_avoids_tolls(junction, unwanted_tolls_after, route_coords)
            if exit_info:
                formatted_name = self._format_junction_name(exit_info)
                print(f"✅ Sortie validée : {formatted_name} évite les péages")
                return exit_info
        
        print("❌ Aucune sortie trouvée qui évite tous les péages")
        return None
    
    def find_exit_after_toll(
        self, 
        route_coords: List[List[float]], 
        used_toll: MatchedToll,
        unwanted_tolls_after: List[MatchedToll]
    ) -> Optional[Dict]:
        """
        Trouve la sortie d'autoroute optimale APRÈS un péage utilisé pour éviter les péages suivants.
        
        Args:
            route_coords: Coordonnées de la route de base
            used_toll: Péage qu'on vient d'utiliser (ex: Fontaine-Larivière)
            unwanted_tolls_after: Péages à éviter après le péage utilisé (ex: Saint-Maurice, Dijon-Crimolois)
            
        Returns:
            Dict: Informations sur la sortie optimale ou None
        """
        print(f"🔍 Recherche de sortie après {used_toll.effective_name} pour éviter {len(unwanted_tolls_after)} péages")
        
        # 1. Analyser toutes les junctions sur la route
        junctions_on_route = self._find_junctions_on_route(route_coords)
        if not junctions_on_route:
            print("❌ Aucune junction trouvée sur la route")
            return None
        
        print(f"📍 {len(junctions_on_route)} junctions trouvées sur la route")
        
        # 2. Ordonner les junctions selon leur position sur la route
        ordered_junctions = self._order_junctions_by_route_position(junctions_on_route, route_coords)
        
        # 3. Trouver la position du péage utilisé sur la route
        used_toll_position = self._find_toll_position_on_route(used_toll, route_coords)
        
        # 4. Filtrer les junctions qui sont APRÈS le péage utilisé mais AVANT le premier péage à éviter
        if unwanted_tolls_after:
            first_unwanted_toll_position = self._find_toll_position_on_route(unwanted_tolls_after[0], route_coords)
            junctions_between = self._filter_junctions_between_tolls(
                ordered_junctions, used_toll_position, first_unwanted_toll_position, route_coords
            )
        else:
            # Pas de péages à éviter, chercher toutes les sorties après le péage utilisé
            junctions_between = self._filter_junctions_after_toll(
                ordered_junctions, used_toll_position, route_coords
            )
        
        if not junctions_between:
            print(f"❌ Aucune junction trouvée entre {used_toll.effective_name} et les péages à éviter")
            return None
          # 5. Tester les sorties une par une (de la plus proche du péage utilisé à la plus lointaine)
        for junction in junctions_between:
            exit_info = self._test_exit_avoids_tolls(junction, unwanted_tolls_after, route_coords)
            if exit_info:
                formatted_name = self._format_junction_name(exit_info)
                print(f"✅ Sortie validée : {formatted_name} évite les péages")
                return exit_info
        
        print("❌ Aucune sortie trouvée qui évite tous les péages")
        return None

    def _find_junctions_on_route(self, route_coords: List[List[float]]) -> List[Dict]:        
        """
        Trouve toutes les motorway_junctions sur la route.
        
        Args:
            route_coords: Coordonnées de la route
        Returns:
            List[Dict]: Junctions qui sont sur la route
        """
        junctions_on_route = []
        all_junctions = self.osm_parser.motorway_junctions
        
        if not all_junctions:
            return []
        
        for junction in all_junctions:
            # Récupérer les coordonnées de la junction
            junction_coords = junction.coordinates if hasattr(junction, 'coordinates') else []
            if not junction_coords or len(junction_coords) != 2:
                continue
            # Calculer la distance à la route
            distance_result = point_to_polyline_distance(junction_coords, route_coords)
            min_distance_m = distance_result[0] * 1000  # Conversion km -> m (prendre seulement la distance)              # Garder seulement les junctions très proches de la route (1m max)
            if min_distance_m <= 1:  # Très strict pour éviter de prendre le mauvais côté du péage
                junction_data = {
                    'id': junction.node_id if hasattr(junction, 'node_id') else '',
                    'name': junction.properties.get('name', 'Sortie inconnue') if hasattr(junction, 'properties') else 'Sortie inconnue',
                    'ref': junction.ref if hasattr(junction, 'ref') else '',
                    'coordinates': junction_coords,
                    'distance_to_route': min_distance_m
                }
                
                # Filtrer les aires de repos et services
                if self._is_real_exit(junction_data):
                    junctions_on_route.append(junction_data)
        
        return junctions_on_route
    
    def _order_junctions_by_route_position(
        self, 
        junctions: List[Dict], 
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Ordonne les junctions selon leur position sur la route.
        
        Args:
            junctions: Liste des junctions
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions ordonnées selon leur position sur la route
        """
        for junction in junctions:
            junction_position = self._calculate_position_on_route(
                junction['coordinates'], route_coords
            )
            junction['position_on_route_km'] = junction_position
        
        # Trier par position sur la route
        junctions.sort(key=lambda j: j['position_on_route_km'])
        
        return junctions
    
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
        
        return cumulative_distance
    
    def _point_to_segment_distance(
        self, 
        point: List[float], 
        segment_start: List[float], 
        segment_end: List[float]
    ) -> float:
        """
        Calcule la distance d'un point à un segment de ligne.
        
        Args:
            point: Coordonnées du point [lon, lat]
            segment_start: Début du segment [lon, lat]
            segment_end: Fin du segment [lon, lat]
            
        Returns:
            float: Distance en mètres
        """
        # Pour simplifier, on utilise la distance au point le plus proche
        dist_to_start = calculate_distance_km(point, segment_start)
        dist_to_end = calculate_distance_km(point, segment_end)
        
        return min(dist_to_start, dist_to_end) * 1000  # Conversion en mètres
    
    def _find_toll_position_on_route(
        self, 
        toll: MatchedToll, 
        route_coords: List[List[float]]
    ) -> float:
        """
        Trouve la position d'un péage sur la route.
        
        Args:
            toll: Péage à localiser
            route_coords: Coordonnées de la route
            
        Returns:
            float: Position en kilomètres
        """
        return self._calculate_position_on_route(toll.osm_coordinates, route_coords)
    
    def _filter_junctions_before_toll(
        self, 
        junctions: List[Dict], 
        toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont AVANT le péage cible.
        
        Args:
            junctions: Junctions ordonnées
            toll_position_km: Position du péage en km
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions avant le péage (ordonnées de la plus proche à la plus lointaine du péage)
        """
        junctions_before = []
        
        for junction in junctions:
            if junction['position_on_route_km'] < toll_position_km:
                junctions_before.append(junction)
        
        # Trier par position décroissante (plus proche du péage en premier)
        junctions_before.sort(key=lambda j: j['position_on_route_km'], reverse=True)
        
        print(f"📍 {len(junctions_before)} junctions trouvées avant le péage cible")
        return junctions_before
    
    def _filter_junctions_between_tolls(
        self, 
        junctions: List[Dict], 
        start_toll_position_km: float,
        end_toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont ENTRE deux péages.
        
        Args:
            junctions: Junctions ordonnées
            start_toll_position_km: Position du péage de début (utilisé)
            end_toll_position_km: Position du péage de fin (à éviter)
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions entre les deux péages (ordonnées de la plus proche du début)
        """
        junctions_between = []
        
        for junction in junctions:
            position = junction['position_on_route_km']
            if start_toll_position_km < position < end_toll_position_km:
                junctions_between.append(junction)
        # Trier par position décroissante (plus proche du péage de destination en premier)
        junctions_between.sort(key=lambda j: j['position_on_route_km'], reverse=True)
        
        print(f"📍 {len(junctions_between)} junctions trouvées entre les péages ({start_toll_position_km:.1f} km - {end_toll_position_km:.1f} km)")
        return junctions_between
    
    def _filter_junctions_after_toll(
        self, 
        junctions: List[Dict], 
        toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont APRÈS le péage.
        
        Args:
            junctions: Junctions ordonnées
            toll_position_km: Position du péage en km
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions après le péage (ordonnées par position croissante)
        """
        junctions_after = []
        
        for junction in junctions:
            if junction['position_on_route_km'] > toll_position_km:
                junctions_after.append(junction)
        
        # Trier par position croissante (plus proche du péage en premier)
        junctions_after.sort(key=lambda j: j['position_on_route_km'])
        
        print(f"📍 {len(junctions_after)} junctions trouvées après le péage ({toll_position_km:.1f} km)")
        return junctions_after

    def _test_exit_avoids_tolls(
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
    
    def _is_real_exit(self, junction: Dict) -> bool:
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
        
        # 7. Par défaut, être conservateur : garder si pas sûr ET avec référence
        print(f"   ⚠️ Inclusion par défaut {junction['name']} (ref: {ref})")
        return True
