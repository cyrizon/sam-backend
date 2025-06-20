"""
highway_entrance_analyzer.py
----------------------------

Module pour analyser et trouver des entrées d'autoroute stratégiques.
Responsabilité : analyser la géographie des autoroutes pour trouver des entrées
logiques entre des points donnés.
"""

from typing import List, Optional, Dict
from ..toll_matcher import MatchedToll
import math


class HighwayEntranceAnalyzer:
    """
    Analyse les entrées d'autoroute pour une navigation intelligente.
    """
    
    def __init__(self, entrance_exit_finder):
        """
        Initialise l'analyzer.
        
        Args:
            entrance_exit_finder: Finder pour les entrées/sorties
        """
        self.entrance_exit_finder = entrance_exit_finder
    
    def find_entrance_between_tolls(
        self,
        tolls_to_avoid: List[MatchedToll],
        target_toll: MatchedToll
    ) -> Optional[List[float]]:
        """
        Trouve une entrée d'autoroute située géographiquement entre les péages à éviter
        et le péage cible.
        
        Cette méthode implémente la logique pour éviter le problème actuel :
        au lieu d'aller directement au péage cible (impossible sans péage),
        on trouve une entrée d'autoroute APRÈS les péages à éviter.
        
        Args:
            tolls_to_avoid: Péages qu'on veut éviter 
            target_toll: Péage qu'on veut atteindre
            
        Returns:
            Optional[List[float]]: Coordonnées de l'entrée stratégique ou None
        """
        if not tolls_to_avoid:
            return None        # Stratégie corrigée pour éviter les entrées trop proches :
        # 1. Prendre le PREMIER péage à éviter (le plus éloigné du target)
        first_toll_to_avoid = tolls_to_avoid[0]
        
        # 2. Calculer une position géographiquement BIEN APRÈS ce premier péage
        # mais suffisamment AVANT le péage cible
        strategic_entrance = self._calculate_strategic_position(
            first_toll_to_avoid, 
            target_toll
        )
        
        if strategic_entrance:
            print(f"       💡 Entrée stratégique calculée entre {first_toll_to_avoid.effective_name} et {target_toll.effective_name}")
            print(f"       📍 Position : {strategic_entrance}")
            return strategic_entrance
            
        return None

    def _calculate_strategic_position(
        self,
        avoid_toll: MatchedToll,
        target_toll: MatchedToll
    ) -> Optional[List[float]]:
        """
        Calcule une position stratégique entre deux péages.
        
        Logique améliorée : calculer un point situé à une distance significative
        du péage cible, en privilégiant des positions près d'axes routiers principaux.
        
        Args:
            avoid_toll: Péage à éviter
            target_toll: Péage cible
            
        Returns:
            Optional[List[float]]: Coordonnées [longitude, latitude] ou None
        """
        try:
            # Coordonnées du péage à éviter
            avoid_coords = avoid_toll.osm_coordinates  # [lon, lat]
            # Coordonnées du péage cible  
            target_coords = target_toll.osm_coordinates  # [lon, lat]
            
            # Calculer la distance totale entre les deux péages
            total_distance = self.calculate_distance_km(avoid_coords, target_coords)
            
            # Stratégie améliorée : distance minimale absolue
            min_distance_km = 10.0  # Minimum 10km du péage cible
            
            # Si la distance est trop courte, utiliser une stratégie conservative
            if total_distance < min_distance_km * 2:  # Moins de 20km entre les péages
                # Utiliser une position à exactement 10km du péage cible
                strategic_coords = self._calculate_position_at_distance(
                    target_coords, avoid_coords, min_distance_km
                )
            else:
                # Distance normale : utiliser des ratios intelligents mais avec distance minimale
                if total_distance < 30:  # Entre 20 et 30km
                    ratio = 0.3  # 30% du chemin
                elif total_distance < 60:  # Entre 30 et 60km
                    ratio = 0.5  # 50% du chemin
                else:  # Plus de 60km
                    ratio = 0.7  # 70% du chemin
                
                strategic_lon = avoid_coords[0] + ratio * (target_coords[0] - avoid_coords[0])
                strategic_lat = avoid_coords[1] + ratio * (target_coords[1] - avoid_coords[1])
                strategic_coords = [strategic_lon, strategic_lat]
                
                # Vérifier la distance minimale de sécurité
                distance_to_target = self.calculate_distance_km(strategic_coords, target_coords)
                
                if distance_to_target < min_distance_km:
                    # Reculer pour assurer la distance minimale
                    strategic_coords = self._calculate_position_at_distance(
                        target_coords, avoid_coords, min_distance_km
                    )
                    print(f"       ⚠️ Position ajustée pour respecter distance minimale ({min_distance_km}km)")
            
            distance_to_target = self.calculate_distance_km(strategic_coords, target_coords)
            print(f"       📏 Distance entre péages : {total_distance:.1f}km")
            print(f"       📏 Distance entrée→péage cible : {distance_to_target:.1f}km")
            print(f"       📍 Position stratégique optimisée : {strategic_coords}")
            
            return strategic_coords
            return strategic_coords
            
        except (IndexError, TypeError, AttributeError) as e:
            print(f"       ⚠️ Erreur calcul position stratégique : {e}")
            return None

    def _calculate_position_at_distance(
        self,
        target_coords: List[float],
        avoid_coords: List[float],
        distance_km: float
    ) -> List[float]:
        """
        Calcule une position située à une distance exacte du péage cible,
        sur la ligne entre le péage à éviter et le péage cible.
        
        Args:
            target_coords: Coordonnées du péage cible [lon, lat]
            avoid_coords: Coordonnées du péage à éviter [lon, lat]
            distance_km: Distance désirée en kilomètres du péage cible
            
        Returns:
            List[float]: Coordonnées [lon, lat] à la distance désirée
        """
        try:
            # Calculer la distance totale
            total_distance = self.calculate_distance_km(avoid_coords, target_coords)
            
            if total_distance <= distance_km:
                # Si la distance totale est plus petite que la distance désirée,
                # prendre un point au milieu
                ratio = 0.5
            else:
                # Calculer le ratio pour obtenir la distance désirée du target
                ratio = 1.0 - (distance_km / total_distance)
            
            # Calculer la position
            strategic_lon = avoid_coords[0] + ratio * (target_coords[0] - avoid_coords[0])
            strategic_lat = avoid_coords[1] + ratio * (target_coords[1] - avoid_coords[1])
            
            return [strategic_lon, strategic_lat]
            
        except (ValueError, TypeError, ZeroDivisionError):
            # Fallback : point au milieu
            return [
                (avoid_coords[0] + target_coords[0]) / 2,
                (avoid_coords[1] + target_coords[1]) / 2
            ]
    
    def calculate_distance_km(
        self,
        coord1: List[float],
        coord2: List[float]
    ) -> float:
        """
        Calcule la distance en km entre deux coordonnées.
        
        Args:
            coord1: [longitude, latitude]
            coord2: [longitude, latitude]
            
        Returns:
            float: Distance en kilomètres
        """
        try:
            lon1, lat1 = coord1
            lon2, lat2 = coord2
            
            # Formule de Haversine
            R = 6371  # Rayon de la Terre en km
            
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2) * math.sin(dlon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
            
        except (ValueError, TypeError):
            return 0.0
