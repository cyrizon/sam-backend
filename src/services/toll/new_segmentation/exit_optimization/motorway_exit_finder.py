"""
motorway_exit_finder.py
-----------------------

Module spécialisé pour trouver les sorties d'autoroute optimales (motorway_junction).

Responsabilité unique :
- Utiliser les classes existantes d'OSMDataParser
- Filtrer les sorties pertinentes (avec référence, pas d'aires de repos)
- Sélectionner la sortie la plus proche pour l'optimisation

Avantages par rapport aux péages :
- Points précis de sortie d'autoroute
- Évite les doublons de péages multiples
- Correspond à l'infrastructure réelle
- Meilleur pour la navigation ORS
"""

from typing import List, Optional
from ..osm_data_parser import OSMDataParser, MotorwayJunction


class MotorwayExitFinder:
    """
    Trouve les sorties d'autoroute optimales en utilisant les données OSM existantes.
    """
    
    def __init__(self, osm_data_parser: OSMDataParser):
        """
        Initialise le finder avec un parser OSM.
        
        Args:
            osm_data_parser: Parser pour accéder aux données OSM
        """
        self.osm_parser = osm_data_parser
    
    def find_exits_near_point(
        self, 
        center_coordinates: List[float], 
        search_radius_km: float = 1.0
    ) -> List[MotorwayJunction]:
        """
        Trouve les sorties d'autoroute dans un rayon donné.
        
        Args:
            center_coordinates: [longitude, latitude] du point central
            search_radius_km: Rayon de recherche en km
            
        Returns:
            List[MotorwayJunction]: Liste des sorties trouvées
        """
        print(f"   🔍 Recherche de sorties d'autoroute dans {search_radius_km}km de {center_coordinates}")
        
        # Utiliser la méthode existante pour trouver les junctions proches
        all_junctions = self._get_junctions_near_point(center_coordinates, search_radius_km)
        
        # Filtrer les sorties valides
        valid_exits = self._filter_valid_exits(all_junctions, center_coordinates, search_radius_km)
        
        print(f"   🎯 {len(valid_exits)} sorties d'autoroute trouvées")
        return valid_exits
    
    def _get_junctions_near_point(self, center: List[float], radius_km: float) -> List[MotorwayJunction]:
        """
        Récupère toutes les junctions dans la zone de recherche.
        
        Args:
            center: Coordonnées du centre [lon, lat]
            radius_km: Rayon de recherche en km
            
        Returns:
            List[MotorwayJunction]: Junctions dans la zone
        """
        # Utiliser directement la méthode existante du parser
        # On passe une "route" d'un seul point pour chercher autour du point
        return self.osm_parser.find_junctions_near_route([center], max_distance_km=radius_km)
    
    def _filter_valid_exits(
        self, 
        junctions: List[MotorwayJunction], 
        center: List[float], 
        radius_km: float
    ) -> List[MotorwayJunction]:
        """
        Filtre les sorties valides selon les critères.
        
        Critères de validation :
        - Présence d'une référence (exit number)
        - Exclusion des aires de repos/service
        - Distance dans le rayon (double vérification)
        
        Args:
            junctions: Junctions brutes
            center: Point central de référence
            radius_km: Rayon maximum
            
        Returns:
            List[MotorwayJunction]: Sorties valides triées par distance
        """
        valid_exits = []
        
        for junction in junctions:
            if self._is_valid_exit(junction, center, radius_km):
                valid_exits.append(junction)
        
        # Trier par distance croissante
        valid_exits.sort(key=lambda x: x.distance_to(center))
        
        return valid_exits
    
    def _is_valid_exit(self, junction: MotorwayJunction, center: List[float], radius_km: float) -> bool:
        """
        Vérifie si une junction est une sortie valide.
        
        Args:
            junction: Junction à valider
            center: Point central de référence
            radius_km: Rayon maximum
            
        Returns:
            bool: True si la sortie est valide
        """
        # Vérifier la distance (double vérification)
        distance_km = junction.distance_to(center)
        if distance_km > radius_km:
            return False
        
        # Vérifier la présence d'une référence (numéro de sortie)
        if not junction.ref or junction.ref.strip() == '':
            return False
        
        # Exclure les aires de repos/service
        name = (junction.properties.get('name', '') or '').lower()
        excluded_terms = ['aire', 'rest', 'service', 'parking']
        if any(term in name for term in excluded_terms):
            return False
        
        return True
    
    def get_closest_exit(self, exits: List[MotorwayJunction]) -> Optional[MotorwayJunction]:
        """
        Retourne la sortie la plus proche.
        
        Args:
            exits: Liste des sorties (déjà triées par distance)
            
        Returns:
            Optional[MotorwayJunction]: La sortie la plus proche ou None
        """
        if not exits:
            return None
        
        closest_exit = exits[0]
        junction_name = closest_exit.properties.get('name', 'Sortie inconnue')
        
        print(f"   🚪 Sortie la plus proche : {junction_name} "
              f"(ref: {closest_exit.ref}, node: {closest_exit.node_id})")
        
        return closest_exit
