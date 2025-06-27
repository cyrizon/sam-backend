"""
segmentation_point_finder.py
---------------------------

Module pour trouver les points de segmentation dans la stratégie V2.
Responsable de l'identification des sorties et motorway_links.
"""

from typing import List, Optional
from src.cache.parsers.osm_parser import OSMParser, MotorwayJunction, MotorwayLink
from src.cache.parsers.toll_matcher import MatchedToll
import math


class SegmentationPointFinder:
    """
    Classe responsable de trouver les points de segmentation
    pour la stratégie intelligente V2.
    """
    
    def __init__(self, osm_parser: OSMParser):
        """
        Initialise le finder avec le parser OSM.
        
        Args:
            osm_parser: Parser OSM pour accéder aux données
        """
        self.osm_parser = osm_parser
    
    def find_segmentation_points(
        self, 
        route_coords: List[List[float]], 
        selected_tolls: List[MatchedToll],
        all_tolls_on_route: List[MatchedToll]
    ) -> List[MotorwayLink]:
        """
        Trouve les points de segmentation (motorway_links) pour tous les péages à éviter.
        
        Args:
            route_coords: Coordonnées de la route de base
            selected_tolls: Péages sélectionnés à utiliser
            all_tolls_on_route: Tous les péages sur la route
            
        Returns:
            List[MotorwayLink]: Points de segmentation trouvés
        """
        print(f"🔧 Recherche de {len(selected_tolls)} point(s) de segmentation...")
        
        segmentation_points = []
        
        # Pour chaque péage sélectionné, trouver le point de segmentation
        for i, selected_toll in enumerate(selected_tolls):
            print(f"   📍 Point {i+1} : péage {selected_toll.effective_name}")
            
            # Trouver le péage suivant (celui qu'on veut éviter)
            next_toll = self._find_next_toll_to_avoid(all_tolls_on_route, selected_toll)
            
            if next_toll:
                print(f"   🎯 Péage à éviter : {next_toll.effective_name}")
                # Trouver la dernière sortie avant ce péage
                last_exit = self._find_last_exit_before_toll(route_coords, next_toll)
                if last_exit:
                    # Trouver le motorway_link correspondant
                    link = self._find_motorway_link_for_junction(last_exit)
                    if link:
                        segmentation_points.append(link)
                        print(f"   ✅ Point de segmentation trouvé")
                    else:
                        print(f"   ⚠️ Pas de motorway_link pour la sortie")
                else:
                    print(f"   ⚠️ Pas de sortie trouvée avant le péage")
            else:
                print(f"   ⚠️ Pas de péage suivant à éviter")
        
        print(f"🎯 {len(segmentation_points)} point(s) de segmentation trouvé(s)")
        return segmentation_points

    def _find_next_toll_to_avoid(
        self, 
        all_tolls: List[MatchedToll], 
        selected_toll: MatchedToll
    ) -> Optional[MatchedToll]:
        """
        Trouve le prochain péage à éviter après le péage sélectionné.
        
        Args:
            all_tolls: Tous les péages sur la route
            selected_toll: Péage actuellement sélectionné
            
        Returns:
            Optional[MatchedToll]: Prochain péage à éviter ou None
        """
        try:
            current_index = all_tolls.index(selected_toll)
            # Retourner le péage suivant dans la liste (celui qu'on veut éviter)
            if current_index + 1 < len(all_tolls):
                return all_tolls[current_index + 1]
        except ValueError:
            pass
        return None

    def _find_last_exit_before_toll(
        self, 
        route_coords: List[List[float]], 
        toll_to_avoid: MatchedToll
    ) -> Optional[MotorwayJunction]:
        """
        Trouve la dernière sortie avant un péage à éviter en analysant la géométrie de la route.
        
        Args:
            route_coords: Coordonnées de la route
            toll_to_avoid: Péage à éviter
            
        Returns:
            Optional[MotorwayJunction]: Sortie trouvée ou None
        """
        print(f"🔍 Recherche d'une sortie avant le péage {toll_to_avoid.effective_name}")
        print(f"   📍 Péage à éviter : {toll_to_avoid.osm_coordinates}")
        
        # Chercher toutes les sorties proches de la route
        junctions = self.osm_parser.find_junctions_near_route(route_coords, max_distance_km=3.0)
        
        if not junctions:
            print("   ⚠️ Aucune sortie trouvée près de la route")
            return None
        
        print(f"   📍 {len(junctions)} sortie(s) trouvée(s) près de la route")
        
        # Debug : afficher toutes les sorties trouvées
        for i, junction in enumerate(junctions):
            ref = junction.ref or 'sans_ref'
            coords = junction.coordinates
            print(f"   🔍 Sortie {i+1}/{len(junctions)} : ref={ref}, coords=[{coords[1]:.6f}, {coords[0]:.6f}]")
        
        # Analyser chaque sortie pour trouver la meilleure
        suitable_junctions = []
        
        for junction in junctions:
            # Filtrer les aires de repos et sorties non valides
            if not self._is_valid_exit_ref(junction):
                continue
            
            # Calculer la position de la sortie sur la route
            junction_position = self._find_position_on_route(junction.coordinates, route_coords)
            toll_position = self._find_position_on_route(toll_to_avoid.osm_coordinates, route_coords)
            
            # La sortie doit être AVANT le péage sur la route
            if junction_position < toll_position:
                distance_to_toll = self._calculate_distance(junction.coordinates, toll_to_avoid.osm_coordinates)
                suitable_junctions.append((junction, junction_position, distance_to_toll))
                print(f"   ✅ Sortie {junction.ref} : position {junction_position:.1f} km, distance au péage {distance_to_toll:.1f} km")
            else:
                print(f"   🚫 Sortie {junction.ref} : après le péage (position {junction_position:.1f} km vs {toll_position:.1f} km)")
        
        if not suitable_junctions:
            print("   ⚠️ Aucune sortie valide trouvée AVANT le péage")
            return None
        
        # Prendre la sortie la plus proche du péage (mais avant lui)
        suitable_junctions.sort(key=lambda x: x[2])  # Trier par distance au péage
        best_junction = suitable_junctions[0][0]
        
        print(f"   🎯 Meilleure sortie sélectionnée : {best_junction.ref or 'sans ref'}")
        return best_junction
    
    def _is_valid_exit_ref(self, junction) -> bool:
        """
        Vérifie si une sortie est valide (pas une aire de repos).
        
        Args:
            junction: Sortie d'autoroute à vérifier
            
        Returns:
            bool: True si c'est une sortie valide, False si c'est une aire
        """
        # Vérifier le tag destination pour les aires de repos
        if hasattr(junction, 'properties') and junction.properties:
            destination = junction.properties.get('destination', '').lower()
            if 'aire' in destination:
                print(f"   🚫 Sortie {junction.ref or 'sans_ref'} exclue : aire de repos (destination: {destination})")
                return False
        
        # Vérifier la référence - les aires n'ont souvent pas de ref numérique
        if not junction.ref:
            print(f"   🚫 Sortie sans ref exclue")
            return False
        
        # Filtrer les références non numériques qui pourraient être des aires
        ref = junction.ref.lower()
        if any(keyword in ref for keyword in ['aire', 'repos', 'service']):
            print(f"   🚫 Sortie {junction.ref} exclue : référence d'aire de repos")
            return False
        
        # Si la ref contient au moins un chiffre, c'est probablement une vraie sortie
        if any(char.isdigit() for char in junction.ref):
            return True
        else:
            print(f"   🚫 Sortie {junction.ref} exclue : pas de numéro de sortie")
            return False

    def _find_position_on_route(
        self, 
        point_coords: List[float], 
        route_coords: List[List[float]]
    ) -> float:
        """
        Trouve la position d'un point le long de la route (distance depuis le début).
        
        Args:
            point_coords: Coordonnées du point [lon, lat]
            route_coords: Coordonnées de la route [[lon, lat], ...]
            
        Returns:
            float: Distance depuis le début de la route en km
        """
        if not route_coords or len(route_coords) < 2:
            return 0.0
        
        # Trouver le point de route le plus proche
        closest_index = 0
        min_distance = float('inf')
        
        for i, route_point in enumerate(route_coords):
            distance = self._calculate_distance(
                [point_coords[1], point_coords[0]],  # [lat, lon]
                [route_point[1], route_point[0]]     # [lat, lon]
            )
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        # Calculer la distance cumulée jusqu'à ce point
        cumulative_distance = 0
        for i in range(1, closest_index + 1):
            if i < len(route_coords):
                dist = self._calculate_distance(
                    [route_coords[i-1][1], route_coords[i-1][0]],
                    [route_coords[i][1], route_coords[i][0]]
                )
                cumulative_distance += dist
        
        return cumulative_distance

    def _find_motorway_link_for_junction(self, junction: MotorwayJunction) -> Optional[MotorwayLink]:
        """
        Récupère le motorway_link associé à la sortie.
        Essaie plusieurs distances de recherche si nécessaire.
        
        Args:
            junction: Sortie d'autoroute
            
        Returns:
            Optional[MotorwayLink]: Lien trouvé ou None
        """
        print(f"🔗 Recherche du motorway_link pour la sortie {junction.ref or 'sans ref'}")
        print(f"   📍 Coordonnées de la sortie : {junction.coordinates}")
        
        # Essayer plusieurs distances de recherche
        search_distances = [1.0, 2.0, 5.0, 10.0]  # km
        
        for distance in search_distances:
            print(f"   🔍 Recherche dans un rayon de {distance} km...")
            links = self.osm_parser.find_links_near_point(junction.coordinates, max_distance_km=distance)
            
            if links:
                selected_link = links[0]  # Prendre le premier lien trouvé
                print(f"   ✅ Motorway_link trouvé à {distance} km : {len(links)} lien(s)")
                print(f"   📍 Coordonnées du lien : {selected_link.coordinates}")
                return selected_link
            else:
                print(f"   ⚠️ Aucun motorway_link dans un rayon de {distance} km")
        
        print("   ❌ Aucun motorway_link trouvé après toutes les tentatives")        # En dernier recours, utiliser les coordonnées de la sortie comme point de segmentation
        print("   🔄 Utilisation des coordonnées de la sortie comme point de segmentation")
        
        # Créer un motorway_link fictif basé sur la sortie
        from src.cache.parsers.osm_parser import MotorwayLink
        
        # Créer un objet simple avec l'attribut coordinates attendu
        class FallbackLink:
            def __init__(self, coordinates):
                self.coordinates = coordinates
                self.way_id = f"fallback_{junction.node_id}"
                self.destination = f"Sortie {junction.ref or 'sans_ref'}"
                self.properties = {"fallback": True, "from_junction": junction.node_id}
        
        fallback_link = FallbackLink(junction.coordinates)
        
        return fallback_link

    def _calculate_distance(self, coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance entre deux points (formule haversine simplifiée).
        
        Args:
            coord1: Premier point [lat, lon]
            coord2: Deuxième point [lon, lat] (format OSM)
            
        Returns:
            float: Distance en kilomètres
        """
        lat1, lon1 = math.radians(coord2[1]), math.radians(coord2[0])  # coord2 car osm_coordinates est [lon, lat]
        lat2, lon2 = math.radians(coord1[1]), math.radians(coord1[0])  # coord1 est [lat, lon] pour junction
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371.0 * c  # Rayon de la Terre en km
