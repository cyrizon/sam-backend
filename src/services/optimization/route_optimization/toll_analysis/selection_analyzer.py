"""
Selection Analyzer
==================

Analyse les sélections de péages pour optimisation et préparation à la segmentation.
Transforme les péages sélectionnés en éléments optimisés (TollBoothStation, CompleteMotorwayLink).
"""

from typing import List, Dict, Tuple, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.cache.models.toll_booth_station import TollBoothStation
from src.cache.models.complete_motorway_link import CompleteMotorwayLink, LinkType
from ..utils.cache_accessor import CacheAccessor


class SelectionAnalyzer:
    """
    Analyseur de sélections pour optimisation.
    Transforme les péages sélectionnés en éléments optimisés.
    """
    
    def __init__(self):
        """Initialise l'analyseur."""
        # Utiliser CacheAccessor au lieu de créer un nouveau cache manager
        print("🔍 Selection Analyzer initialisé avec CacheAccessor")
        
    def analyze_selection_for_optimization(
        self, 
        selection_result: Dict, 
        route_coordinates: List[List[float]]
    ) -> Dict:
        """
        Analyse la sélection et retourne les éléments optimisés.
        
        Args:
            selection_result: Résultat de sélection initial
            route_coordinates: Coordonnées de route [start, end]
            
        Returns:
            Résultat avec éléments optimisés (TollBoothStation, CompleteMotorwayLink)
        """
        if not selection_result.get('selection_valid'):
            return selection_result
            
        print("🔍 Analyse pour optimisation...")
        
        selected_tolls = selection_result['selected_tolls']
        optimized_elements = []
        
        # Analyser chaque péage sélectionné
        for toll in selected_tolls:
            optimized_element = self._optimize_toll_element(toll, route_coordinates)
            if optimized_element:
                optimized_elements.append(optimized_element)
        
        # Mettre à jour le résultat
        selection_result['selected_tolls'] = optimized_elements
        selection_result['optimization_applied'] = True
        selection_result['elements_optimized'] = len(optimized_elements)
        
        print(f"   ✅ {len(optimized_elements)} éléments optimisés")
        return selection_result
    
    def _optimize_toll_element(
        self, 
        toll: Dict, 
        route_coordinates: List[List[float]]
    ) -> Optional[object]:
        """
        Optimise un élément péage en le transformant en objet cache V2.
        
        Args:
            toll: Élément péage à optimiser
            route_coordinates: Coordonnées de route
            
        Returns:
            Élément optimisé (TollBoothStation ou CompleteMotorwayLink)
        """
        # Gérer la nouvelle structure après Shapely
        if 'toll' in toll and hasattr(toll['toll'], 'name'):
            # Structure Shapely: {'toll': TollBoothStation, ...}
            toll_station = toll['toll']
            toll_name = toll_station.display_name
            toll_type = 'ouvert' if toll_station.is_open_toll else 'fermé'
        else:
            # Format legacy ou dict direct
            toll_type = toll.get('toll_type')
            toll_name = toll.get('name', 'Inconnu')
        
        print(f"   🔧 Optimisation de {toll_name} ({toll_type})")
        
        result = None
        if toll_type == 'ouvert':
            result = self._get_toll_booth_station(toll)
            print(f"       → Recherche TollBoothStation: {'✅ Trouvé' if result else '❌ Non trouvé'}")
        elif toll_type == 'fermé':
            result = self._get_optimized_motorway_link(toll, route_coordinates)
            print(f"       → Recherche MotorwayLink: {'✅ Trouvé' if result else '❌ Non trouvé'}")
        else:
            # Fallback : essayer de trouver l'élément correspondant
            result = self._find_best_match(toll, route_coordinates)
            print(f"       → Recherche fallback: {'✅ Trouvé' if result else '❌ Non trouvé'}")
        
        return result
    
    def _get_toll_booth_station(self, toll: Dict) -> Optional[TollBoothStation]:
        """Récupère la TollBoothStation correspondante."""
        try:
            # Cas 1: Structure Shapely avec 'toll' key contenant déjà un TollBoothStation
            if 'toll' in toll and hasattr(toll['toll'], 'osm_id'):
                # L'objet TollBoothStation est déjà là, le retourner directement
                return toll['toll']
            
            # Cas 2: Utiliser CacheAccessor pour récupérer les péages (format legacy)
            toll_stations = CacheAccessor.get_toll_stations()
            
            osm_id = toll.get('osm_id')
            if osm_id:
                # Recherche par OSM ID
                for station in toll_stations:
                    if station.osm_id == osm_id:
                        return station
            
            # Recherche par coordonnées si pas d'OSM ID
            coordinates = toll.get('coordinates', [])
            if coordinates:
                # Recherche simplifiée dans tous les péages
                min_distance = float('inf')
                closest_toll = None
                
                for station in toll_stations:
                    distance = self._calculate_distance(station.get_coordinates(), coordinates)
                    if distance < min_distance:
                        min_distance = distance
                        closest_toll = station
                
                # Retourner le plus proche si dans un rayon raisonnable (500m)
                if closest_toll and min_distance < 0.5:
                    return closest_toll
                
        except Exception as e:
            print(f"   ⚠️ Erreur récupération TollBoothStation : {e}")
            
        return None
    
    def _get_optimized_motorway_link(
        self, 
        toll: Dict, 
        route_coordinates: List[List[float]]
    ) -> Optional[CompleteMotorwayLink]:
        """
        Récupère le lien autoroutier optimisé pour un péage fermé.
        
        Args:
            toll: Péage fermé
            route_coordinates: Coordonnées de route
            
        Returns:
            CompleteMotorwayLink optimisé (entrée ou sortie)
        """
        try:
            # Récupérer les coordonnées du péage selon la structure
            toll_coords = None
            
            if 'toll' in toll and hasattr(toll['toll'], 'get_coordinates'):
                # Structure Shapely avec TollBoothStation
                toll_coords = toll['toll'].get_coordinates()
            else:
                # Format legacy
                toll_coords = toll.get('coordinates', [])
                
            if not toll_coords:
                return None
            
            # Utiliser CacheAccessor pour récupérer les liens
            entry_links = CacheAccessor.get_entry_links()
            exit_links = CacheAccessor.get_exit_links()
            
            # Trouver les liens proches avec filtrage multi-critères
            nearby_entries = []
            nearby_exits = []
            
            for link in entry_links:
                distance = self._calculate_distance(link.get_start_point(), toll_coords)
                if distance < 2.0:  # Rayon de 2km
                    if self._is_valid_motorway_link(link):
                        nearby_entries.append(link)
            
            for link in exit_links:
                distance = self._calculate_distance(link.get_end_point(), toll_coords)
                if distance < 2.0:  # Rayon de 2km
                    if self._is_valid_motorway_link(link):
                        nearby_exits.append(link)
                if distance < 2.0:  # Rayon de 2km
                    nearby_exits.append(link)
            
            # Récupérer le nom pour l'affichage
            toll_name_for_display = "Inconnu"
            if 'toll' in toll and hasattr(toll['toll'], 'display_name'):
                toll_name_for_display = toll['toll'].display_name
            elif 'name' in toll:
                toll_name_for_display = toll['name']
            
            print(f"   🔍 Liens trouvés près de {toll_name_for_display}: {len(nearby_entries)} entrées, {len(nearby_exits)} sorties (aires exclues)")
            
            # Debug des liens trouvés
            if nearby_entries:
                print(f"       🚪 Entrées disponibles:")
                for i, entry in enumerate(nearby_entries[:3]):  # Afficher les 3 premières
                    dest = getattr(entry, 'destination', 'Inconnue')
                    print(f"         {i+1}. {entry.link_id} → {dest}")
            
            if nearby_exits:
                print(f"       🚪 Sorties disponibles:")
                for i, exit_link in enumerate(nearby_exits[:3]):  # Afficher les 3 premières
                    dest = getattr(exit_link, 'destination', 'Inconnue')
                    print(f"         {i+1}. {exit_link.link_id} → {dest}")
            
            # Pour l'optimisation de péages fermés, TOUJOURS privilégier les ENTRÉES
            # L'objectif est d'éviter le péage fermé en rejoignant l'autoroute via une entrée
            best_link = None
            
            if nearby_entries:
                # Prendre la meilleure entrée (la plus proche)
                best_link = self._get_best_entry(nearby_entries, toll_coords)
                print(f"   🎯 Entrée sélectionnée pour éviter le péage fermé")
            elif nearby_exits:
                # Si pas d'entrée, prendre une sortie (cas de secours)
                best_link = self._get_best_exit(nearby_exits, toll_coords)
                print(f"   ⚠️ Aucune entrée disponible, utilisation d'une sortie")
            else:
                print(f"   ❌ Aucun lien d'autoroute trouvé")
            
            return best_link
            
        except Exception as e:
            print(f"   ⚠️ Erreur optimisation lien autoroutier : {e}")
            
        return None
    
    def _choose_best_link_for_route(
        self, 
        entries: List[CompleteMotorwayLink], 
        exits: List[CompleteMotorwayLink],
        route_coordinates: List[List[float]], 
        toll_coords: List[float]
    ) -> Optional[CompleteMotorwayLink]:
        """
        Choisit le meilleur lien autoroutier selon la position sur la route.
        
        Args:
            entries: Liens d'entrée disponibles
            exits: Liens de sortie disponibles
            route_coordinates: Coordonnées de route [start, end]
            toll_coords: Coordonnées du péage
            
        Returns:
            Meilleur lien autoroutier
        """
        start_point = route_coordinates[0]
        end_point = route_coordinates[1]
        
        # Calculer la distance relative du péage sur la route
        toll_distance_from_start = self._calculate_distance(start_point, toll_coords)
        toll_distance_from_end = self._calculate_distance(end_point, toll_coords)
        total_route_distance = self._calculate_distance(start_point, end_point)
        
        # Position relative (0 = début, 1 = fin)
        relative_position = toll_distance_from_start / total_route_distance if total_route_distance > 0 else 0.5
        
        # Choix de stratégie selon la position
        if relative_position < 0.3:
            # Début de route → préférer entrée
            return self._get_best_entry(entries, toll_coords)
        elif relative_position > 0.7:
            # Fin de route → préférer sortie
            return self._get_best_exit(exits, toll_coords)
        else:
            # Milieu de route → choisir le plus proche
            best_entry = self._get_best_entry(entries, toll_coords)
            best_exit = self._get_best_exit(exits, toll_coords)
            
            if not best_entry:
                return best_exit
            if not best_exit:
                return best_entry
                
            # Comparer les distances
            entry_distance = self._calculate_distance(best_entry.get_start_point(), toll_coords)
            exit_distance = self._calculate_distance(best_exit.get_end_point(), toll_coords)
            
            return best_entry if entry_distance <= exit_distance else best_exit
    
    def _get_best_entry(self, entries: List[CompleteMotorwayLink], toll_coords: List[float]) -> Optional[CompleteMotorwayLink]:
        """Récupère la meilleure entrée."""
        if not entries:
            return None
            
        # Trier par distance
        entries_with_distance = [
            (entry, self._calculate_distance(entry.get_start_point(), toll_coords))
            for entry in entries
        ]
        entries_with_distance.sort(key=lambda x: x[1])
        
        return entries_with_distance[0][0]
    
    def _get_best_exit(self, exits: List[CompleteMotorwayLink], toll_coords: List[float]) -> Optional[CompleteMotorwayLink]:
        """Récupère la meilleure sortie."""
        if not exits:
            return None
            
        # Trier par distance
        exits_with_distance = [
            (exit_link, self._calculate_distance(exit_link.get_end_point(), toll_coords))
            for exit_link in exits
        ]
        exits_with_distance.sort(key=lambda x: x[1])
        
        return exits_with_distance[0][0]
    
    def _find_best_match(
        self, 
        toll: Dict, 
        route_coordinates: List[List[float]]
    ) -> Optional[object]:
        """Trouve le meilleur élément correspondant par recherche générale."""
        # Récupérer les coordonnées selon la structure
        coordinates = None
        
        if 'toll' in toll and hasattr(toll['toll'], 'get_coordinates'):
            # Structure Shapely avec TollBoothStation
            coordinates = toll['toll'].get_coordinates()
        else:
            # Format legacy
            coordinates = toll.get('coordinates', [])
            
        if not coordinates:
            return None
            
        # Essayer d'abord TollBoothStation
        toll_booth = self._find_closest_toll_booth(coordinates)
        if toll_booth:
            return toll_booth
            
        # Sinon, chercher un lien autoroutier
        closest_link = self._find_closest_motorway_link(coordinates)
        if closest_link:
            return closest_link
            
        return None
    
    def _find_closest_toll_booth(self, coordinates: List[float]) -> Optional[TollBoothStation]:
        """Trouve le péage le plus proche."""
        min_distance = float('inf')
        closest_toll = None
        
        toll_stations = CacheAccessor.get_toll_stations()
        for toll_booth in toll_stations:
            distance = self._calculate_distance(toll_booth.get_coordinates(), coordinates)
            if distance < min_distance:
                min_distance = distance
                closest_toll = toll_booth
        
        # Retourner si dans un rayon raisonnable (5km)
        return closest_toll if min_distance < 5.0 else None
    
    def _find_closest_motorway_link(self, coordinates: List[float]) -> Optional[CompleteMotorwayLink]:
        """Trouve le lien autoroutier le plus proche."""
        min_distance = float('inf')
        closest_link = None
        
        complete_links = CacheAccessor.get_complete_motorway_links()
        for link in complete_links:
            distance = self._calculate_distance(link.get_start_point(), coordinates)
            if distance < min_distance:
                min_distance = distance
                closest_link = link
        
        # Retourner si dans un rayon raisonnable (1km)
        return closest_link if min_distance < 1.0 else None
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """
        Calcule la distance approximative entre deux points.
        
        Args:
            point1: Premier point [lon, lat]
            point2: Deuxième point [lon, lat]
            
        Returns:
            Distance en kilomètres (approximative)
        """
        if not point1 or not point2 or len(point1) < 2 or len(point2) < 2:
            return float('inf')
            
        # Distance euclidienne simple (approximation)
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        
        # Conversion approximative en km (1 degré ≈ 111 km)
        return ((dx * dx + dy * dy) ** 0.5) * 111
    
    def _is_valid_motorway_link(self, link) -> bool:
        """
        Vérifie si un lien autoroutier est valide (pas une aire de service).
        
        Args:
            link: CompleteMotorwayLink à vérifier
            
        Returns:
            True si c'est un lien valide, False si c'est une aire
        """
        # Critère 1: Exclure les destinations contenant "aire"
        if hasattr(link, 'destination') and link.destination:
            dest = link.destination.lower()
            if 'aire' in dest:
                return False
            # Si la destination est non null et ne contient pas 'aire', c'est une vraie entrée/sortie
            return True
        
        # Critère 2: Calculer la longueur du lien
        coordinates = link.get_all_coordinates()
        if len(coordinates) < 2:
            return False
            
        total_length = 0.0
        for i in range(len(coordinates) - 1):
            point1 = coordinates[i]
            point2 = coordinates[i + 1]
            segment_distance = self._calculate_distance(point1, point2)
            total_length += segment_distance
        
        # Convertir en mètres (distance était en km)
        total_length_meters = total_length * 1000
        
        # Critère 3: Exclure les liens trop courts (< 200m) si pas de destination explicite
        if total_length_meters < 200:
            return False
        
        return True
    
    def _calculate_link_length_meters(self, link) -> float:
        """Calcule la longueur d'un lien en mètres."""
        coordinates = link.get_all_coordinates()
        if len(coordinates) < 2:
            return 0.0
            
        total_length = 0.0
        for i in range(len(coordinates) - 1):
            point1 = coordinates[i]
            point2 = coordinates[i + 1]
            segment_distance = self._calculate_distance(point1, point2)
            total_length += segment_distance
        
        # Convertir en mètres (distance était en km)
        return total_length * 1000
