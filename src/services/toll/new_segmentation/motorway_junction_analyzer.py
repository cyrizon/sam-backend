"""
motorway_junction_analyzer.py
----------------------------

Module principal pour analyser les motorway_junctions sur la route et identifier
les vraies sorties d'autoroute pour éviter les péages non-désirés.

Responsabilité : 
- Coordonner l'analyse des junctions sur la route de base
- Identifier les sorties avant/après chaque péage
- Valider que les sorties évitent bien les péages
"""

from typing import List, Dict, Optional
from .toll_matcher import MatchedToll
from .osm_data_parser import OSMDataParser
from .junction_analysis.junction_finder import JunctionFinder
from .junction_analysis.junction_filter import JunctionFilter
from .junction_analysis.exit_validator import ExitValidator


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
        self.junction_finder = JunctionFinder(osm_parser)
        self.junction_filter = JunctionFilter()
        self.exit_validator = ExitValidator(osm_parser)

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
        junctions_on_route = self.junction_finder.find_junctions_on_route(route_coords)
        if not junctions_on_route:
            print("❌ Aucune junction trouvée sur la route")
            return None
        
        print(f"📍 {len(junctions_on_route)} junctions trouvées sur la route")
        
        # 2. Ordonner les junctions selon leur position sur la route
        ordered_junctions = self.junction_finder.order_junctions_by_route_position(junctions_on_route, route_coords)
        
        # 3. Trouver la position du péage cible sur la route
        target_toll_position = self.junction_filter.find_toll_position_on_route(target_toll, route_coords)
        
        # 4. Filtrer les junctions qui sont AVANT le péage cible
        junctions_before_target = self.junction_filter.filter_junctions_before_toll(
            ordered_junctions, target_toll_position, route_coords
        )
        
        if not junctions_before_target:
            print(f"❌ Aucune junction trouvée avant {target_toll.effective_name}")
            return None
        
        # 5. Tester les sorties une par une (de la plus proche à la plus lointaine)
        for junction in junctions_before_target:
            exit_info = self.exit_validator.test_exit_avoids_tolls(junction, unwanted_tolls_after, route_coords)
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
        # Vérifier si le péage utilisé est déjà une sortie d'autoroute
        if hasattr(used_toll, 'is_exit') and used_toll.is_exit:
            print(f"   🚪 {used_toll.effective_name} est déjà une sortie - pas besoin de chercher une sortie supplémentaire")
            return None
            
        print(f"🔍 Recherche de sortie après {used_toll.effective_name} pour éviter {len(unwanted_tolls_after)} péages")
        
        # 1. Analyser toutes les junctions sur la route
        junctions_on_route = self.junction_finder.find_junctions_on_route(route_coords)
        if not junctions_on_route:
            print("❌ Aucune junction trouvée sur la route")
            return None
        
        print(f"📍 {len(junctions_on_route)} junctions trouvées sur la route")
        
        # 2. Ordonner les junctions selon leur position sur la route
        ordered_junctions = self.junction_finder.order_junctions_by_route_position(junctions_on_route, route_coords)
        
        # 3. Trouver la position du péage utilisé sur la route
        used_toll_position = self.junction_filter.find_toll_position_on_route(used_toll, route_coords)
        
        # 4. Filtrer les junctions qui sont APRÈS le péage utilisé mais AVANT le premier péage à éviter
        if unwanted_tolls_after:
            first_unwanted_toll_position = self.junction_filter.find_toll_position_on_route(unwanted_tolls_after[0], route_coords)
            junctions_between = self.junction_filter.filter_junctions_between_tolls(
                ordered_junctions, used_toll_position, first_unwanted_toll_position, route_coords
            )
        else:
            # Pas de péages à éviter, chercher toutes les sorties après le péage utilisé
            junctions_between = self.junction_filter.filter_junctions_after_toll(
                ordered_junctions, used_toll_position, route_coords
            )
        
        if not junctions_between:
            print(f"❌ Aucune junction trouvée entre {used_toll.effective_name} et les péages à éviter")
            return None
          
        # 5. Tester les sorties une par une (de la plus proche du péage utilisé à la plus lointaine)
        for junction in junctions_between:
            exit_info = self.exit_validator.test_exit_avoids_tolls(junction, unwanted_tolls_after, route_coords)
            if exit_info:
                formatted_name = self._format_junction_name(exit_info)
                print(f"✅ Sortie validée : {formatted_name} évite les péages")
                return exit_info
        
        print("❌ Aucune sortie trouvée qui évite tous les péages")
        return None

    def find_entrance_between_tolls(
        self,
        route_coords: List[List[float]],
        tolls_to_avoid: List[MatchedToll],
        target_toll: MatchedToll
    ) -> Optional[Dict]:
        """
        Trouve une entrée d'autoroute réelle entre les péages à éviter et le péage cible.
        
        Cette méthode utilise les vraies motorway_junctions au lieu de points géométriques arbitraires.
        
        Args:
            route_coords: Coordonnées de la route de base
            tolls_to_avoid: Péages qu'on veut éviter
            target_toll: Péage qu'on veut atteindre
            
        Returns:
            Optional[Dict]: Info de l'entrée trouvée ou None
        """
        if not tolls_to_avoid:
            return None
            
        print(f"🔍 Recherche entrée d'autoroute réelle entre péages à éviter et {target_toll.effective_name}")
        
        # 1. Chercher toutes les junctions sur la route
        junctions_on_route = self.junction_finder.find_junctions_on_route(route_coords)
        if not junctions_on_route:
            print("❌ Aucune junction trouvée sur la route")
            return None
            
        print(f"🔍 {len(junctions_on_route)} junctions trouvées sur la route")
        
        # 2. Ordonner les junctions selon leur position sur la route
        ordered_junctions = self.junction_finder.order_junctions_by_route_position(junctions_on_route, route_coords)
        
        # 3. Trouver les positions des péages sur la route
        last_avoided_toll = tolls_to_avoid[-1]  # Dernier péage à éviter
        last_avoided_position = self.junction_filter.find_toll_position_on_route(last_avoided_toll, route_coords)
        target_toll_position = self.junction_filter.find_toll_position_on_route(target_toll, route_coords)
        
        # 4. Filtrer les junctions qui sont APRÈS le dernier péage à éviter mais AVANT le péage cible
        junctions_between = self.junction_filter.filter_junctions_between_tolls(
            ordered_junctions, last_avoided_position, target_toll_position, route_coords
        )
        
        if not junctions_between:
            print(f"❌ Aucune junction trouvée entre {last_avoided_toll.effective_name} et {target_toll.effective_name}")
            return None
            
        print(f"✅ {len(junctions_between)} entrées d'autoroute trouvées entre les péages")
        
        # 5. Prendre la première junction viable (la plus proche du péage à éviter)
        # Cela assure qu'on rejoint l'autoroute dès que possible après avoir évité les péages
        for junction in junctions_between:
            junction_name = self._format_junction_name(junction)
            print(f"🎯 Entrée candidate : {junction_name}")
            # Vérifier que cette entrée nous mène bien vers le péage cible
            # (validation basique pour l'instant)
            return {
                'name': junction_name,
                'link_coordinates': junction.get('coordinates', junction.get('link_coordinates', [])),
                'junction_info': junction
            }
        
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
